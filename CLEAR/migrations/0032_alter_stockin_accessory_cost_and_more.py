# Generated by Django 5.0 on 2024-05-01 14:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('CLEAR', '0031_alter_job_order_total_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stockin_accessory',
            name='cost',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='stockin_textile',
            name='cost',
            field=models.FloatField(null=True),
        ),
    ]