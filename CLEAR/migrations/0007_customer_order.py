# Generated by Django 5.0 on 2024-01-11 04:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('CLEAR', '0006_product_materials'),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('mobile_number', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('purchase_mode', models.CharField(max_length=50)),
                ('payment_type', models.CharField(max_length=50)),
                ('order_status', models.CharField(default='In-queue', max_length=50)),
                ('order_date', models.DateTimeField(auto_now_add=True)),
                ('delivery_date', models.DateTimeField()),
                ('order_price', models.FloatField(blank=True, null=True)),
                ('address_city', models.CharField(max_length=50)),
                ('address_street', models.CharField(max_length=50)),
                ('address_barangay', models.CharField(max_length=50)),
                ('address_zip', models.IntegerField()),
                ('contact_number', models.IntegerField()),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='CLEAR.customer')),
            ],
        ),
    ]
