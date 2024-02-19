# Generated by Django 5.0.2 on 2024-02-19 16:42

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('CLEAR', '0019_alter_accessory_cost_alter_accessory_stock_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='labor_time',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='product',
            name='misc_margin',
            field=models.IntegerField(default=50, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='product',
            name='prod_margin',
            field=models.FloatField(validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='product',
            name='stock',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]