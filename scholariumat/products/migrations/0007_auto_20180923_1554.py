# Generated by Django 2.0.8 on 2018-09-23 13:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0006_auto_20180919_1702'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='itemtype',
            name='contains',
        ),
        migrations.AddField(
            model_name='purchase',
            name='free',
            field=models.BooleanField(default=False),
        ),
    ]
