# Generated by Django 5.0.2 on 2024-05-05 15:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('CLEAR', '0036_remove_account_username_account_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='username',
            field=models.CharField(default=None, max_length=50),
        ),
    ]
