# Generated by Django 5.1.4 on 2025-01-17 10:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='KYCCapturedPhoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('photo', models.ImageField(blank=True, null=True, upload_to='kyc_photos/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('verified', models.BooleanField(default=False, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('kyc_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.account')),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('Project_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.account')),
            ],
        ),
        migrations.CreateModel(
            name='ProjectFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='projects/')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to='app.project')),
            ],
        ),
    ]
