import logging

from django.db import models
from django.db.models import Q
from django.core.mail import mail_managers
from django.urls import reverse_lazy
from django.conf import settings

from django_extensions.db.models import TimeStampedModel, TitleDescriptionModel

from framework.behaviours import CommentAble
from .behaviours import AttachmentBase


logger = logging.getLogger('__name__')


class Product(models.Model):
    """Class to avoid MTI/generic relations: Explicit OneToOneField with all products."""

    @property
    def type(self):
        """Get product object"""
        for product_rel in self._meta.get_fields():
            if product_rel.one_to_one and getattr(self, product_rel.name, False):
                return getattr(self, product_rel.name)

    @property
    def items_available(self):
        return self.item_set.filter(Q(price__gt=0), Q(amount__gt=0) | Q(amount__isnull=True))

    def __str__(self):
        return self.type.__str__()

    class Meta:
        verbose_name = 'Produkt'
        verbose_name_plural = 'Produkte'


class ItemType(TitleDescriptionModel, TimeStampedModel):
    slug = models.SlugField()
    shipping = models.BooleanField(default=False)
    requestable = models.BooleanField(default=False)
    purchasable_at = models.SmallIntegerField(default=0)
    accessible_at = models.SmallIntegerField(null=True, blank=True)
    contains = models.ManyToManyField('self', related_name='contained_in', symmetrical=False)
    unavailability_notice = models.CharField(max_length=20, default="Nicht verfügbar")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Item Typ'
        verbose_name_plural = 'Item Typen'


class Item(TimeStampedModel):
    """Purchasable items."""

    type = models.ForeignKey(ItemType, on_delete=models.CASCADE, verbose_name='Typ')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.SmallIntegerField('Preis', null=True, blank=True)
    amount = models.IntegerField('Anzahl', null=True, blank=True)
    requests = models.ManyToManyField('users.Profile', related_name='item_requests', blank=True, editable=False)

    @property
    def available(self):
        return self.price and (self.amount is None or self.amount > 0)

    @property
    def attachment(self):
        """Fetches related attachment"""
        for item_rel in self._meta.get_fields():
            if item_rel.one_to_one and issubclass(item_rel.related_model, AttachmentBase) and \
               getattr(self, item_rel.name, False):
                return getattr(self, item_rel.name)

    def is_purchasable(self, profile):
        return profile.amount >= self.type.purchasable_at

    def download(self):
        return self.attachment.get() if self.attachment else None

    def request(self, profile):
        if self.type.requestable:
            self.requests.add(profile)
            edit_url = reverse_lazy('admin:products_item_change', args=[self.pk])
            mail_managers(
                f'Anfrage: {self.product}',
                f'Nutzer {profile} hat {self.product} im Format {self.type} angefragt. '
                f'Das Item kann unter folgender URL editiert werden: {settings.DEFAULT_DOMAIN}{edit_url}')

    def inform_users(self):
        pass
        # TODO: Send email to users in requests

    def add_to_cart(self, profile):
        """Only add a limited product if no purchase of it exists."""
        if not self.is_purchasable(profile):
            return False
        if self.amount is None:
            purchase, created = Purchase.objects.get_or_create(profile=profile, item=self, defaults={'executed': False})
            if not created:
                return False
        else:
            purchase, created = Purchase.objects.get_or_create(profile=profile, item=self, executed=False)
            if not created:
                purchase.amount += 1
                purchase.save()
        return True

    def sell(self, amount):
        """Given an amount, tries to lower local amount. Ignored if not limited."""
        if self.amount is not None:
            new_amount = self.amount - amount
            if new_amount >= 0:
                self.amount = new_amount
                self.save()
                return True
            else:
                logger.exception(f"Can't sell item: {self.amount} < {amount}")
                return False
        else:
            return True

    def refill(self, amount):
        """Refills amount."""
        if self.amount is not None:
            self.amount += amount
            self.save()

    def __str__(self):
        return '{} für {} Punkte'.format(self.type.__str__(), self.price)

    class Meta:
        verbose_name = 'Item'
        verbose_name_plural = 'Items'


class Purchase(TimeStampedModel, CommentAble):
    """Logs purchases."""

    profile = models.ForeignKey('users.Profile', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    amount = models.SmallIntegerField(default=1)
    shipped = models.DateField(blank=True, null=True)
    executed = models.BooleanField(default=False)

    @property
    def total(self):
        return self.item.price * self.amount if self.item.amount is not None else self.item.price

    @property
    def available(self):
        """Check if required amount is available"""
        return self.item.available and (self.item.amount is None or self.item.amount >= self.amount)

    def execute(self):
        if self.profile.spend(self.total):
            if self.item.sell(self.amount):
                self.executed = True
                self.save()
                return True
            else:
                self.profile.refill(self.total)
        return False

    def revert(self):
        self.profile.refill(self.total)
        self.item.refill(self.amount)
        self.delete()

    def __str__(self):
        return '%dx %s (%s)' % (self.amount, self.item.product.__str__(), self.profile.__str__())

    class Meta():
        verbose_name = 'Kauf'
        verbose_name_plural = 'Käufe'
