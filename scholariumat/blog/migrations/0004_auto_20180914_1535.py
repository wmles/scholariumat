# Generated by Django 2.0.8 on 2018-09-14 13:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0003_auto_20180914_1457'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='bibliography',
            options={'verbose_name': 'Bibliographie', 'verbose_name_plural': 'Bibliographien'},
        ),
    ]