# Generated by Django 5.0 on 2024-04-03 14:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('CLEAR', '0022_stockin_accessory_cost_stockin_textile_cost'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockin',
            name='total_cost',
            field=models.FloatField(null=True),
        ),
    ]
