# Generated by Django 5.1.4 on 2025-02-28 21:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0018_project_total_revenue_delete_userrevenue'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='total_revenue',
        ),
        migrations.CreateModel(
            name='ProjectRevenue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_revenue', models.DecimalField(decimal_places=2, default=0.0, max_digits=15)),
                ('project', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='revenue', to='app.project')),
            ],
        ),
    ]
