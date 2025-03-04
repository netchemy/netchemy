# Generated by Django 5.1.4 on 2025-01-18 09:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_remove_kyccapturedphoto_photo4_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='KYC',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('photo1', models.ImageField(upload_to='kyc_photos/')),
                ('photo2', models.ImageField(upload_to='kyc_photos/')),
                ('photo3', models.ImageField(upload_to='kyc_photos/')),
                ('front', models.ImageField(upload_to='kyc_photos/')),
                ('back', models.ImageField(upload_to='kyc_photos/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.account')),
            ],
        ),
    ]
