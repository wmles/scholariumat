import logging

from django.db import models
from django.db.models import Q
from django.core.mail import mail_managers
from django.urls import reverse_lazy
from django.conf import settings

from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel, TitleDescriptionModel

from users.models import Profile
from framework.behaviours import CommentAble, PermalinkAble


logger = logging.getLogger('__name__')


class Product(models.Model):
    """Class to avoid MTI/generic relations: Explicit OneToOneField with all products."""

    @property
    def type(self):
        """Get product object"""
        for product_rel in self._meta.get_fields():
            if product_rel.one_to_one:
                return getattr(self, product_rel.name)

    @property
    def items_available(self):
        return self.item_set.filter(Q(price__gt=0), Q(amount__gt=0) | Q(type__limited=False))

    def __str__(self):
        return self.type.__str__()


class ProductBase(TitleSlugDescriptionModel, TimeStampedModel, PermalinkAble):
    """Abstract parent class for all product type classes."""

    product = models.OneToOneField(Product, on_delete=models.CASCADE, null=True, editable=False)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.product:
            self.product = Product.objects.create()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # TODO: Gets ignored in bulk delete. pre_delete signal better?
        self.product.delete()
        super().delete(*args, **kwargs)

    class Meta:
        abstract = True


class ItemType(TitleDescriptionModel, TimeStampedModel):
    slug = models.SlugField()
    limited = models.BooleanField(default=True)
    shipping = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Item Typ'
        verbose_name_plural = 'Item Typen'


class Item(TimeStampedModel):
    """Purchaseable items."""

    type = models.ForeignKey(ItemType, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.SmallIntegerField(null=True, blank=True)
    amount = models.IntegerField(null=True, blank=True)
    file = models.FileField(blank=True)
    requests = models.ManyToManyField(Profile, related_name='item_requests')

    @property
    def available(self):
        return self.price and (self.amount or not self.type.limited)

    def request(self, profile):
        self.requests.add(profile)
        edit_url = reverse_lazy('admin:products_item_change', args=[self.pk])
        mail_managers(
            f'Anfrage: {self.product}',
            f'Nutzer {profile} hat {self.product} im Format {self.type} angefragt. '
            f'Das Item kann unter folgender URL editiert werden: {settings.DEFAULT_DOMAIN}{edit_url}'
        )

    def inform_users(self):
        pass
        # TODO: Send email to users in requests

    def add_to_cart(self, profile):
        purchase, created = Purchase.objects.get_or_create(profile=profile, item=self, executed=False)
        if not created:
            purchase.amount += 1
            purchase.save()

    def sell(self, amount):
        """Given an amount, tries to lower local amount. Ignored if not limited."""
        if self.type.limited:
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
        self.amount += amount
        self.save()

    def __str__(self):
        return '{} für {} Punkte'.format(self.type.__str__(), self.price)

    class Meta:
        verbose_name = 'Item'
        verbose_name_plural = 'Items'


class Purchase(TimeStampedModel, CommentAble):
    """Logs purchases."""

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    amount = models.SmallIntegerField(default=1)
    shipped = models.DateField(blank=True, null=True)
    executed = models.BooleanField(default=False)

    @property
    def total(self):
        return self.item.price * self.amount

    @property
    def available(self):
        """Check if required amount is available"""
        return self.item.amount >= self.amount

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
