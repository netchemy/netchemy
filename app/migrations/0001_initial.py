# Generated by Django 5.1.4 on 2025-01-15 08:42

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='account',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=100, null=True, unique=True)),
                ('role', models.CharField(max_length=100, null=True)),
                ('email', models.EmailField(max_length=254, null=True, unique=True)),
                ('password', models.CharField(max_length=200, null=True)),
                ('Subscription', models.BooleanField(default=False)),
                ('SubPlan', models.CharField(max_length=100, null=True)),
                ('startDate', models.DateTimeField(blank=True, null=True)),
                ('endDate', models.DateTimeField(blank=True, null=True)),
                ('payment_id', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
            ],
        ),
    ]
