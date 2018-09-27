# Generated by Django 2.0.8 on 2018-09-24 11:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchase',
            name='profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.Profile'),
        ),
        migrations.AddField(
            model_name='item',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.Product'),
        ),
        migrations.AddField(
            model_name='item',
            name='requests',
            field=models.ManyToManyField(blank=True, editable=False, related_name='item_requests', to='users.Profile'),
        ),
        migrations.AddField(
            model_name='item',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.ItemType', verbose_name='Typ'),
        ),
        migrations.AddField(
            model_name='fileattachment',
            name='item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.Item'),
        ),
        migrations.AddField(
            model_name='fileattachment',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='products.AttachmentType'),
        ),
    ]