# Generated by Django 4.0.6 on 2022-08-01 11:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CoilDB',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=255, verbose_name='Идентификатор бухты')),
                ('product_id', models.CharField(max_length=255, verbose_name='Идентификатор материала')),
                ('quantity', models.IntegerField(verbose_name='Изначальное количество')),
                ('recommended_balance', models.IntegerField(verbose_name='Рекомендуемый остаток')),
                ('acceptable_loss', models.IntegerField(verbose_name='Приемлемые потери')),
            ],
        ),
        migrations.CreateModel(
            name='OrderLineDB',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_id', models.CharField(max_length=255, verbose_name='Идентификатор заказа')),
                ('line_item', models.CharField(max_length=255, verbose_name='Номер товарной позиции')),
                ('product_id', models.CharField(max_length=255, verbose_name='Идентификатор материала')),
                ('quantity', models.IntegerField(verbose_name='Количество материала')),
            ],
        ),
        migrations.CreateModel(
            name='AllocationDB',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('coil_record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='allocation.coildb')),
                ('orderline_record', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='allocation.orderlinedb')),
            ],
        ),
    ]
