# Generated by Django 2.0.5 on 2018-07-17 11:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('donations', '0004_auto_20180717_1348'),
        ('framework', '0003_auto_20180714_1115'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='menusubitem',
            options={'ordering': ['id']},
        ),
        migrations.RemoveField(
            model_name='menu',
            name='levels',
        ),
        migrations.AddField(
            model_name='menuitem',
            name='description',
            field=models.TextField(blank=True, null=True, verbose_name='description'),
        ),
        migrations.AddField(
            model_name='menuitem',
            name='levels',
            field=models.ManyToManyField(to='donations.DonationLevel'),
        ),
        migrations.AddField(
            model_name='menusubitem',
            name='description',
            field=models.TextField(blank=True, null=True, verbose_name='description'),
        ),
        migrations.AddField(
            model_name='menusubitem',
            name='levels',
            field=models.ManyToManyField(to='donations.DonationLevel'),
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='id',
            field=models.IntegerField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='menusubitem',
            name='id',
            field=models.IntegerField(primary_key=True, serialize=False),
        ),
    ]
