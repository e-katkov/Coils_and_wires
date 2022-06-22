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
        """Создает экземпляр класса Coil доменной модели в соответствии с записью, для которой он вызван."""
        coil = domain_logic.Coil(reference=self.reference,
                                 product_id=self.product_id,
                                 quantity=self.quantity,
                                 recommended_balance=self.recommended_balance,
                                 acceptable_loss=self.acceptable_loss)
        coil.allocations = set(a.line.to_domain() for a in self.allocation_set.all())
        return coil

    @staticmethod
    def get(reference: str) -> 'Coil':
        """
        Принимает идентификатор экземпляра класса Coil доменной модели,
        возвращает соответствующую ему одиночную запись.

        Генерирует исключение, возникающее при отсутствии подходящей записи.
        """
        try:
            coil = Coil.objects.get(reference=reference)
        except Coil.DoesNotExist:
            raise DBCoilRecordDoesNotExist(
                f'Запись с reference={reference} отсутствует в таблице Coil базы данных'
            )
        else:
            return coil

    @staticmethod
    def create_from_domain(domain_coil: domain_logic.Coil) -> None:
        """
        Принимает экземпляр класса Coil доменной модели,
        создает соответствующую ему запись.

        Генерирует исключение, которое возникает при совпадении идентификатора reference
        у экземпляра и одной из существующих записей.
        """
        if Coil.objects.filter(reference=domain_coil.reference):
            raise DBCoilRecordAlreadyExist(
                f'Запись с reference={domain_coil.reference} уже существует в таблице Coil базы данных'
            )
        else:
            Coil.objects.create(reference=domain_coil.reference,
                                product_id=domain_coil.product_id,
                                quantity=domain_coil.initial_quantity,
                                recommended_balance=domain_coil.recommended_balance,
                                acceptable_loss=domain_coil.acceptable_loss)

    @staticmethod
    def update_from_domain(domain_coil: domain_logic.Coil) -> None:
        """
        Принимает экземпляр класса Coil доменной модели,
        обновляет соответствующую ему запись.

        Определяет запись, соответствующую экземпляру, по идентификатору reference.
        Генерирует исключение, возникающее при отсутствии подходящей записи.
        Связывает запись с записями таблицы Allocation согласно множеству allocations экземпляра.
        """
        coil = Coil.get(reference=domain_coil.reference)
        Coil.objects.filter(reference=domain_coil.reference).update(
            product_id=domain_coil.product_id,
            quantity=domain_coil.initial_quantity,
            recommended_balance=domain_coil.recommended_balance,
            acceptable_loss=domain_coil.acceptable_loss
        )
        Allocation.objects.filter(coil=coil).delete()
        coil.allocation_set.set(Allocation.get_or_create_from_domain(coil, domain_line)
                                for domain_line in domain_coil.allocations)

    @staticmethod
    def delete(reference: str) -> None:
        """
        Принимает идентификатор экземпляра класса Coil доменной модели,
        удаляет соответствующую ему запись.

        Генерирует исключение, возникающее при отсутствии подходящей записи.
        """
        Coil.get(reference=reference)
        Coil.objects.filter(reference=reference).delete()


class OrderLine(models.Model):
    order_id = models.CharField(max_length=255)
    line_item = models.CharField(max_length=255)
    product_id = models.CharField(max_length=255)
    quantity = models.IntegerField()

    def to_domain(self) -> domain_logic.OrderLine:
        """Создает экземпляр класса OrderLine доменной модели в соответствии с записью, для которой он вызван."""
        line = domain_logic.OrderLine(order_id=self.order_id,
                                      line_item=self.line_item,
                                      product_id=self.product_id,
                                      quantity=self.quantity)
        return line

    @staticmethod
    def get(order_id: str, line_item: str) -> 'OrderLine':
        """
        Принимает идентификаторы экземпляра класса OrderLine доменной модели,
        возвращает соответствующую им одиночную запись.

        Генерирует исключение, возникающее при отсутствии подходящей записи.
        """
        try:
            line = OrderLine.objects.get(order_id=order_id, line_item=line_item)
        except OrderLine.DoesNotExist:
            raise DBOrderLineRecordDoesNotExist(
                f'Запись с order_id={order_id} и line_item={line_item}'
                f' отсутствует в таблице OrderLine базы данных'
            )
        else:
            return line

    @staticmethod
    def create_from_domain(domain_line: domain_logic.OrderLine) -> None:
        """
        Принимает экземпляр класса OrderLine доменной модели,
        создает соответствующую ему запись.

        Генерирует исключение, которое возникает при совпадении идентификаторов
        order_id, line_item у экземпляра и одной из существующих записей.
        """
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

    @staticmethod
    def update_from_domain(domain_line: domain_logic.OrderLine) -> None:
        """
        Принимает экземпляр класса OrderLine доменной модели,
        обновляет соответствующую ему запись.

        Определяет запись, соответствующую экземпляру, по идентификаторам order_id, line_item.
        Генерирует исключение, возникающее при отсутствии подходящей записи.
        """
        OrderLine.get(order_id=domain_line.order_id, line_item=domain_line.line_item)
        OrderLine.objects.filter(order_id=domain_line.order_id, line_item=domain_line.line_item).update(
            product_id=domain_line.product_id,
            quantity=domain_line.quantity,
        )

    @staticmethod
    def get_an_allocation_coil(domain_line: domain_logic.OrderLine) -> domain_logic.Coil:
        """
        Принимает экземпляр класса OrderLine доменной модели,
        возвращает экземпляр класса Coil доменной модели, соответствующий связанной записи таблицы Coil.

        При отсутствии связи между записью таблицы OrderLine и записью таблицы Coil,
        которая выполнена с помощью записи промежуточной таблицы Allocation,
        возвращает "поддельный" экземпляр класса Coil доменной модели.
        """
        try:
            allocation_record = Allocation.objects.get(
                line__order_id=domain_line.order_id, line__line_item=domain_line.line_item
            )
        except Allocation.DoesNotExist:
            fake_coil = domain_logic.Coil('fake', 'fake', 1, 1, 1)
            return fake_coil
        else:
            real_coil = allocation_record.coil.to_domain()
            return real_coil

    @staticmethod
    def delete(order_id: str, line_item: str) -> None:
        """
        Принимает идентификаторы экземпляра класса OrderLine доменной модели,
        удаляет соответствующую им запись.

        Генерирует исключение, возникающее при отсутствии подходящей записи.
        """
        OrderLine.get(order_id=order_id, line_item=line_item)
        OrderLine.objects.filter(order_id=order_id, line_item=line_item).delete()


class Allocation(models.Model):
    coil = models.ForeignKey(Coil, on_delete=models.CASCADE)
    line = models.OneToOneField(OrderLine, on_delete=models.CASCADE)

    @staticmethod
    def get_or_create_from_domain(coil: Coil, domain_line: domain_logic.OrderLine) -> 'Allocation':
        """
        Принимает экземпляры классов Coil и OrderLine доменной модели,
        возвращает существующую или создает новую запись таблицы Allocation,
        которая связывает соответствующие экземплярам записи таблиц Coil и OrderLine.

        Генерирует исключение, возникающее при отсутствии записи таблицы OrderLine,
        соответствующей экземпляру OrderLine доменной модели.
        """
        line = OrderLine.get(order_id=domain_line.order_id, line_item=domain_line.line_item)
        allo, _ = Allocation.objects.get_or_create(coil=coil, line=line)
        return allo
