# Generated by Django 5.0 on 2024-04-29 13:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('CLEAR', '0026_store_job_order'),
    ]

    operations = [
        migrations.RenameField(
            model_name='job_order',
            old_name='finish_date',
            new_name='completion_date',
        ),
    ]
