# Generated by Django 2.0.5 on 2018-07-19 12:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('donations', '0002_donation_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentmethod',
            name='local_approval',
            field=models.BooleanField(default=False),
        ),
    ]
