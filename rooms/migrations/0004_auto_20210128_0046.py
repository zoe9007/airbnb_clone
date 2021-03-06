# Generated by Django 2.2.5 on 2021-01-27 14:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0003_auto_20210127_1238'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='roomtype',
            options={'ordering': ['name'], 'verbose_name': 'Room Type'},
        ),
        migrations.AlterField(
            model_name='photo',
            name='room',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='photos', to='rooms.Room'),
        ),
    ]
