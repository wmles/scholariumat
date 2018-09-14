# Generated by Django 2.0.8 on 2018-09-14 12:57

from django.db import migrations, models
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0002_article_product'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bibliography',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('slug', models.SlugField(unique=True)),
                ('file', models.FileField(upload_to='')),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.RenameField(
            model_name='article',
            old_name='priority',
            new_name='publish_priority',
        ),
        migrations.RemoveField(
            model_name='article',
            name='created',
        ),
        migrations.RemoveField(
            model_name='article',
            name='modified',
        ),
        migrations.RemoveField(
            model_name='article',
            name='product',
        ),
        migrations.AddField(
            model_name='article',
            name='private',
            field=models.TextField(blank=True, editable=False),
        ),
        migrations.AddField(
            model_name='article',
            name='public',
            field=models.TextField(blank=True, editable=False),
        ),
        migrations.AddField(
            model_name='article',
            name='public2',
            field=models.TextField(blank=True, editable=False),
        ),
        migrations.AddField(
            model_name='article',
            name='references',
            field=models.TextField(blank=True, editable=False),
        ),
    ]