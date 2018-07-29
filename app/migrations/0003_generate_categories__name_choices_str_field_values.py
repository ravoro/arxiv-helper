# -*- coding: utf-8 -*-
# Custom migrations defining Category._name_choices_str field

from __future__ import unicode_literals

from django.db import migrations


def forwards_generate_name_choices_str(apps, schema_editor):
    Category = apps.get_model('app', 'Category')
    for category in Category.objects.all():
        category.save()  # calling save() autogenerates _name_choices_str



class Migration(migrations.Migration):
    dependencies = [
        ('app', '0002_add_categories__name_choices_str_field'),
    ]

    operations = [
        migrations.RunPython(forwards_generate_name_choices_str, migrations.RunPython.noop),
    ]
