from django.db import models

from allocation.domain import domain_logic
from allocation.exceptions.exceptions import DBCoilRecordAlreadyExist, DBCoilRecordDoesNotExist, \
    DBOrderLineRecordDoesNotExist, DBOrderLineRecordAlreadyExist


class Coil(models.Model):
    reference = models.CharField(max_length=255)
    product_id = models.CharField(max_length=255)
    quantity = models.IntegerField()
    recommended_balance = models.IntegerField()
    acceptable_loss = models.IntegerField()

    def to_domain(self) -> domain_logic.Coil:
        coil = domain_logic.Coil(reference=self.reference,
                                 product_id=self.product_id,
                                 quantity=self.quantity,
                                 recommended_balance=self.recommended_balance,
                                 acceptable_loss=self.acceptable_loss)
        coil._allocations = set(a.line.to_domain() for a in self.allocation_set.all())
        return coil

    @staticmethod
    def create_from_domain(domain_coil: domain_logic.Coil):
        if Coil.objects.filter(reference=domain_coil.reference):
            raise DBCoilRecordAlreadyExist(
                f'Запись с reference={domain_coil.reference} уже существует в таблице Coil базы данных'
            )
        else:
            Coil.objects.create(reference=domain_coil.reference,
                                product_id=domain_coil.product_id,
                                quantity=domain_coil._initial_quantity,
                                recommended_balance=domain_coil.recommended_balance,
                                acceptable_loss=domain_coil.acceptable_loss)

    @staticmethod
    def update_from_domain(domain_coil: domain_logic.Coil):
        try:
            coil = Coil.objects.get(reference=domain_coil.reference)
        except Coil.DoesNotExist:
            raise DBCoilRecordDoesNotExist(
                f'Запись с reference={domain_coil.reference} отсутствует в таблице Coil базы данных'
            )
        else:
            Coil.objects.filter(reference=domain_coil.reference).update(
                product_id=domain_coil.product_id,
                quantity=domain_coil._initial_quantity,
                recommended_balance=domain_coil.recommended_balance,
                acceptable_loss=domain_coil.acceptable_loss
            )
            coil.allocation_set.set(
                Allocation.get_or_create_from_domain(coil, domain_line)
                for domain_line in domain_coil._allocations
            )


class OrderLine(models.Model):
    order_id = models.CharField(max_length=255)
    line_item = models.CharField(max_length=255)
    product_id = models.CharField(max_length=255)
    quantity = models.IntegerField()

    def to_domain(self) -> domain_logic.OrderLine:
        line = domain_logic.OrderLine(order_id=self.order_id,
                                      line_item=self.line_item,
                                      product_id=self.product_id,
                                      quantity=self.quantity)
        return line

    @staticmethod
    def get_from_domain(domain_line: domain_logic.OrderLine):
        try:
            line = OrderLine.objects.get(order_id=domain_line.order_id,
                                     line_item=domain_line.line_item)
        except OrderLine.DoesNotExist:
            raise DBOrderLineRecordDoesNotExist(
                f'Запись с order_id={domain_line.order_id} и line_item={domain_line.line_item}'
                f' отсутствует в таблице OrderLine базы данных'
            )
        else:
            return line

    @staticmethod
    def create_from_domain(domain_line: domain_logic.OrderLine):
        if OrderLine.objects.filter(order_id=domain_line.order_id,
                                 line_item=domain_line.line_item):
            raise DBOrderLineRecordAlreadyExist(
                f'Запись с order_id={domain_line.order_id} и line_item={domain_line.line_item}'
                f' уже существует в таблице OrderLine базы данных'
            )
        else:
            OrderLine.objects.create(order_id=domain_line.order_id,
                                     line_item=domain_line.line_item,
                                     product_id=domain_line.product_id,
                                     quantity=domain_line.quantity)


class Allocation(models.Model):
    coil = models.ForeignKey(Coil, on_delete=models.CASCADE)
    line = models.OneToOneField(OrderLine, on_delete=models.CASCADE)

    @staticmethod
    def get_or_create_from_domain(coil: Coil, domain_line: domain_logic.OrderLine):
        line = OrderLine.get_from_domain(domain_line)
        allo, _ = Allocation.objects.get_or_create(coil=coil, line=line)
        return allo
