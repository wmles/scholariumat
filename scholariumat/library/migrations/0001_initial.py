# Generated by Django 2.0.8 on 2018-09-24 11:51

from django.db import migrations, models
import django_extensions.db.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'Autor',
                'verbose_name_plural': 'Autoren',
            },
        ),
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('slug', django_extensions.db.fields.AutoSlugField(blank=True, editable=False, populate_from='title', verbose_name='slug')),
            ],
            options={
                'verbose_name': 'Kollektion',
                'verbose_name_plural': 'Kollektionen',
            },
        ),
        migrations.CreateModel(
            name='Lending',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('comment', models.TextField(blank=True)),
                ('returned', models.DateField(blank=True, null=True)),
                ('charged', models.DateField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Leihe',
                'verbose_name_plural': 'Leihen',
            },
        ),
        migrations.CreateModel(
            name='ZotAttachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(blank=True, max_length=100)),
                ('format', models.CharField(choices=[('file', 'Datei'), ('note', 'Notiz')], max_length=5)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ZotItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('title', models.CharField(max_length=1000)),
                ('slug', models.CharField(max_length=50, unique=True)),
                ('published', models.DateField(blank=True, null=True)),
                ('authors', models.ManyToManyField(to='library.Author')),
                ('collection', models.ManyToManyField(to='library.Collection')),
            ],
            options={
                'verbose_name': 'Zotero Item',
                'verbose_name_plural': 'Zotero Items',
            },
        ),
    ]
