# Generated by Django 5.2 on 2025-06-13 14:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.CharField(choices=[('student', 'Student'), ('owner', 'Landlord'), ('admin', 'Admin')], default='student', max_length=10),
        ),
    ]
