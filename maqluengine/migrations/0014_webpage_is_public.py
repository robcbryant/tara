# Generated by Django 2.0.2 on 2018-08-22 19:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maqluengine', '0013_formrecordreferencevalue_is_public'),
    ]

    operations = [
        migrations.AddField(
            model_name='webpage',
            name='is_public',
            field=models.BooleanField(default=True),
        ),
    ]
