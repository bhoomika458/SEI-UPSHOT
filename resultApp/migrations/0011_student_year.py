# Generated by Django 3.2.9 on 2022-01-25 05:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resultApp', '0010_logindetails'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='year',
            field=models.CharField(default=True, max_length=30),
        ),
    ]
