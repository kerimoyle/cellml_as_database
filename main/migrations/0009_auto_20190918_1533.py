# Generated by Django 2.2.4 on 2019-09-18 15:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_auto_20190918_1532'),
    ]

    operations = [
        migrations.AlterField(
            model_name='component',
            name='parent_component',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='components', to='main.Component'),
        ),
    ]
