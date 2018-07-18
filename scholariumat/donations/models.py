import datetime
import logging

from django.db import models
from django.conf import settings
from django.http import HttpRequest
from django.urls import reverse

from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel

from .behaviours import Payment


logger = logging.getLogger(__name__)


class DonationLevel(TitleSlugDescriptionModel):
    amount = models.SmallIntegerField(unique=True)

    @classmethod
    def get_level_by_amount(cls, amount):
        level = cls.objects.filter(amount__lte=amount).order_by('-amount')
        if level:
            return level[0]
        else:
            logger.info("No level available for {}".format(amount))

    @classmethod
    def get_lowest_amount(cls):
        level = cls.objects.all().order_by('-amount')
        return level[0].amount if level else None

    class Meta:
        verbose_name = 'Spendenstufe'
        verbose_name_plural = 'Spendenstufen'

    def __str__(self):
        return '{}: {}'.format(self.amount, self.title)


class PaymentMethod(TitleSlugDescriptionModel):
    return_url_name = models.CharField(max_length=50, default='donations:approve')  # TODO: Make static?

    @property
    def return_url(self):
        return HttpRequest.build_absolute_uri(reverse(self.return_url_name))

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Zahlungsmethode'
        verbose_name_plural = 'Zahlungsmethoden'


class Donation(Payment, TimeStampedModel):
    """Enables user to use services according to active donation level."""
    @staticmethod
    def _default_expiration():
        return datetime.date.today() + datetime.timedelta(days=settings.DONATION_PERIOD)

    profile = models.ForeignKey('users.Profile', on_delete=models.CASCADE)
    amount = models.SmallIntegerField()
    date = models.DateField(auto_now_add=True)
    expiration = models.DateField(default=_default_expiration.__func__)

    @property
    def level(self):
        return DonationLevel.get_level_by_amount(self.amount)

    def __str__(self):
        return '%s: %s (%s)' % (self.profile.name, self.level.title, self.date)

    class Meta:
        verbose_name = 'Unterstützung'
        verbose_name_plural = 'Unterstuetzungen'
