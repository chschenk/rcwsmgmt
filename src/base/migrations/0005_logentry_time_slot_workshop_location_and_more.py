# Generated by Django 5.0.4 on 2024-04-22 15:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0004_alter_logentry_new_status_alter_logentry_old_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='logentry',
            name='time_slot',
            field=models.CharField(choices=[('M', 'Vormittags'), ('A', 'Nachmittags'), ('B', 'Vormittags und Nachmittags'), ('C', '')], default='M', max_length=1, verbose_name='Workshopphase'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='workshop',
            name='location',
            field=models.CharField(choices=[('Z', 'Zentral'), ('D', 'Dezentral')], default='Z', max_length=1, verbose_name='Ort'),
        ),
        migrations.AddField(
            model_name='workshop',
            name='time_slot',
            field=models.CharField(choices=[('M', 'Vormittags'), ('A', 'Nachmittags'), ('B', 'Vormittags und Nachmittags'), ('C', '')], default='M', max_length=1, verbose_name='Workshopphase'),
            preserve_default=False,
        ),
    ]