# Generated by Django 5.0 on 2024-04-04 07:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('CLEAR', '0023_stockin_total_cost'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stockin_textile',
            name='quantity',
            field=models.FloatField(),
        ),
    ]
