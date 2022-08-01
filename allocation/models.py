from django.db import models


class CoilDB(models.Model):
    reference = models.CharField(max_length=255, verbose_name='Идентификатор бухты')
    product_id = models.CharField(max_length=255, verbose_name='Идентификатор материала')
    quantity = models.IntegerField(verbose_name='Изначальное количество')
    recommended_balance = models.IntegerField(verbose_name='Рекомендуемый остаток')
    acceptable_loss = models.IntegerField(verbose_name='Приемлемые потери')


class OrderLineDB(models.Model):
    order_id = models.CharField(max_length=255, verbose_name='Идентификатор заказа')
    line_item = models.CharField(max_length=255, verbose_name='Номер товарной позиции')
    product_id = models.CharField(max_length=255, verbose_name='Идентификатор материала')
    quantity = models.IntegerField(verbose_name='Количество материала')


class AllocationDB(models.Model):
    coil_record = models.ForeignKey(CoilDB, on_delete=models.CASCADE)
    orderline_record = models.OneToOneField(OrderLineDB, on_delete=models.CASCADE)
