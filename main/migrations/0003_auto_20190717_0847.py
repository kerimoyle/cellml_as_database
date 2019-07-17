# Generated by Django 2.2.3 on 2019-07-17 08:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_setup_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='Annotation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(blank=True, null=True)),
                ('code', models.CharField(blank=True, max_length=100, null=True)),
                ('source', models.URLField(blank=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='cellmodel',
            name='annotations',
            field=models.ManyToManyField(blank=True, related_name='used_by_cellmodel_objects', to='main.Annotation'),
        ),
        migrations.AddField(
            model_name='component',
            name='annotations',
            field=models.ManyToManyField(blank=True, related_name='used_by_component_objects', to='main.Annotation'),
        ),
        migrations.AddField(
            model_name='compoundunit',
            name='annotations',
            field=models.ManyToManyField(blank=True, related_name='used_by_compoundunit_objects', to='main.Annotation'),
        ),
        migrations.AddField(
            model_name='encapsulation',
            name='annotations',
            field=models.ManyToManyField(blank=True, related_name='used_by_encapsulation_objects', to='main.Annotation'),
        ),
        migrations.AddField(
            model_name='math',
            name='annotations',
            field=models.ManyToManyField(blank=True, related_name='used_by_math_objects', to='main.Annotation'),
        ),
        migrations.AddField(
            model_name='reset',
            name='annotations',
            field=models.ManyToManyField(blank=True, related_name='used_by_reset_objects', to='main.Annotation'),
        ),
        migrations.AddField(
            model_name='unit',
            name='annotations',
            field=models.ManyToManyField(blank=True, related_name='used_by_unit_objects', to='main.Annotation'),
        ),
        migrations.AddField(
            model_name='variable',
            name='annotations',
            field=models.ManyToManyField(blank=True, related_name='used_by_variable_objects', to='main.Annotation'),
        ),
    ]
