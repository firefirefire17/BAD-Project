# Generated by Django 5.0 on 2024-05-01 22:44

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('CLEAR', '0033_rename_global_value_financial_value'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='stock',
        ),
        migrations.AlterField(
            model_name='product_component',
            name='quantity',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(999)]),
        ),
    ]
