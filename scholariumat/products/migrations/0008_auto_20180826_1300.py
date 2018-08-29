# Generated by Django 2.0.8 on 2018-08-26 11:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0007_auto_20180823_1306'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='requests',
            field=models.ManyToManyField(blank=True, related_name='item_requests', to='users.Profile'),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='amount',
            field=models.SmallIntegerField(default=1),
        ),
    ]