# Generated by Django 5.1.4 on 2025-01-20 14:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_sales'),
    ]

    operations = [
        migrations.AddField(
            model_name='bankdetails',
            name='LinkId',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
