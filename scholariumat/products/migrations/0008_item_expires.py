# Generated by Django 2.0.8 on 2018-10-19 07:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0007_itemtype_buy_once'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='expires',
            field=models.DateField(blank=True, null=True),
        ),
    ]
