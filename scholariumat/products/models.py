import logging
from slugify import slugify
from datetime import date

from django.db import models
from django.db.models import Q
from django.core.mail import mail_managers
from django.urls import reverse_lazy
from django.conf import settings
from django.http import HttpResponse

from django_extensions.db.models import TimeStampedModel, TitleDescriptionModel, TitleSlugDescriptionModel

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

    def items_accessible(self, profile):
        """Returns items that can be accessed by user"""
        return self.item_set.filter(
            Q(purchase__in=profile.purchases) | Q(type__accessible_at__lt=profile.amount)).distinct()

    def any_attachments_accessible(self, profile):
        """Only checks for existence for performance reasons"""
        for item in self.items_accessible(profile):
            if item.attachments:
                return True

    def __str__(self):
        return self.type.__str__()

    class Meta:
        verbose_name = 'Produkt'
        verbose_name_plural = 'Produkte'


class ItemType(TitleDescriptionModel, TimeStampedModel):
    slug = models.SlugField()
    shipping = models.BooleanField(default=False)
    requestable = models.BooleanField(default=False)
    default_price = models.SmallIntegerField(null=True, blank=True)
    purchasable_at = models.SmallIntegerField(default=0)
    accessible_at = models.SmallIntegerField(null=True, blank=True)
    unavailability_notice = models.CharField(max_length=20, default="Nicht verfügbar")
    buy_once = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Item Typ'
        verbose_name_plural = 'Item Typen'


class Item(TimeStampedModel):
    """
    Items are purchasable can have 3 states in relation to a user:
    - requestable: Is visible and can be requested.
    - purchasable: Can be purchased.
    - accessible: Can be accessed, attachments can be downloaded, etc.
    If amount is None, the item is unlimited.
    """

    title = models.CharField(max_length=50, blank=True)
    type = models.ForeignKey(ItemType, on_delete=models.CASCADE, verbose_name='Typ')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    _price = models.SmallIntegerField('Preis', null=True, blank=True)
    amount = models.IntegerField('Anzahl', null=True, blank=True)
    requests = models.ManyToManyField('users.Profile', related_name='item_requests', blank=True, editable=False)
    files = models.ManyToManyField('products.FileAttachment', blank=True)
    expires = models.DateField(null=True, blank=True)

    @property
    def price(self):
        return self._price or self.type.default_price

    @property
    def expired(self):
        return self.expires and self.expires < date.today()

    @property
    def sold_out(self):
        return self.amount and self.amount <= 0

    @property
    def available(self):
        return self.price and not self.expired and not self.sold_out

    @property
    def attachments(self):
        # TODO: Remove? Custom attachments should maybe be handled individually when needed.
        """Fetches related attachments """
        attachment_list = []
        for item_rel in self._meta.get_fields():
            if item_rel.related_model and issubclass(item_rel.related_model, AttachmentBase)\
                    and getattr(self, item_rel.get_accessor_name(), False):
                attachment_list += (getattr(self, item_rel.get_accessor_name()).all())
        return list(self.files.all()) + attachment_list

    def is_requestable(self, profile):
        return not self.available and \
            profile.amount >= self.type.purchasable_at and \
            self.type.requestable

    def is_purchasable(self, profile):
        return self.available and profile.amount >= self.type.purchasable_at and \
            not (self.is_accessible(profile) and self.type.buy_once)

    def amount_purchased(self, profile):
        return sum(p.amount for p in profile.purchases.filter(item=self))

    def is_accessible(self, profile):
        return profile.amount >= self.type.accessible_at if self.type.accessible_at is not None else \
            bool(profile.purchases.filter(item=self))

    def amount_accessible(self, profile):
        return 1 if self.type.accessible_at is not None and profile.amount >= self.type.accessible_at else \
            self.amount_purchased(profile)

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
        # TODO: Send email to users in requests when saved and available

    def add_to_cart(self, profile):
        """Only add a limited product if no purchase of it exists."""
        if self.is_purchasable(profile):
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
        if self.title:
            return f'{self.type.title}: {self.title}'
        return self.type.title

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
    free = models.BooleanField(default=False)
    date = models.DateField(null=True, blank=True)

    @property
    def total(self):
        return 0 if self.free else self.item.price * self.amount

    @property
    def available(self):
        """Check if required amount is available"""
        return self.item.available and self.item.amount >= self.amount

    def execute(self):
        if self.item.is_purchasable(self.profile):
            if self.profile.spend(self.total):
                if self.item.sell(self.amount):
                    if self.item.type.shipping:
                        mail_managers(
                            f'Bestellung: {self.item.product}',
                            f'Nutzer {self.profile} hat {self.item.product} im Format {self.item.type} bestellt. '
                            f'Adresse: {self.profile.address}')
                    self.executed = True
                    self.date = date.today()
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


class AttachmentType(TitleSlugDescriptionModel):
    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Anhangstyp'
        verbose_name_plural = 'Anhangstypen'


class FileAttachment(models.Model):
    file = models.FileField()
    type = models.ForeignKey('products.AttachmentType', on_delete=models.PROTECT)

    def get(self):
        print(self.file)
        response = HttpResponse(self.file, content_type=f'application/{self.type.slug}')
        response['Content-Disposition'] = f'attachment; \
            filename={slugify(self.item.product)}.{self.type.slug}'
        return response

    def __str__(self):
        return f'{self.type.__str__()}: {self.file.name}'

    class Meta:
        verbose_name = 'Anhang'
        verbose_name_plural = 'Anhänge'
