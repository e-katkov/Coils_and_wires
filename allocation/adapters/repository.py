from typing import Protocol

from allocation import models as django_models
from allocation.adapters import mapper
from allocation.domain import domain_logic
from allocation.exceptions import exceptions


class AbstractCoilRepository(Protocol):
    def get(self, reference: str) -> domain_logic.Coil: ...

    def add(self, coil_domain: domain_logic.Coil) -> None: ...

    def update(self, coil_domain: domain_logic.Coil) -> None: ...

    def delete(self, reference: str) -> None: ...

    def coils_list(self) -> list[domain_logic.Coil]: ...


class AbstractOrderLineRepository(Protocol):
    def get(self, order_id: str, line_item: str) -> domain_logic.OrderLine: ...

    def add(self, orderline_domain: domain_logic.OrderLine) -> None: ...

    def update(self, orderline_domain: domain_logic.OrderLine) -> None: ...

    def delete(self, order_id: str, line_item: str) -> None: ...

    def order_lines_list(self) -> list[domain_logic.OrderLine]: ...


class DjangoCoilRepository:
    def get(self, reference: str) -> domain_logic.Coil:
        """
        Принимает идентификатор экземпляра класса Coil доменной модели,
        возвращает экземпляр класса Coil доменной модели,
        полученный из соответствующей записи таблицы CoilDB.

        Вызывает исключение при отсутствии подходящей записи.
        """
        # Получение записи таблицы CoilDB или вызов исключения
        coil_record = DjangoCoilRepository._get_coil_record_from_db(reference)
        coil_domain = mapper.coil_record_to_domain(coil_record)
        return coil_domain

    def add(self, coil_domain: domain_logic.Coil) -> None:
        """
        Принимает экземпляр класса Coil доменной модели,
        создает соответствующую ему запись в таблице CoilDB.

        Вызывает исключение, которое возникает при совпадении идентификатора reference
        у экземпляра и одной из существующих записей.
        """
        if django_models.CoilDB.objects.filter(reference=coil_domain.reference):
            raise exceptions.DBCoilRecordAlreadyExist(
                f'Запись с reference={coil_domain.reference} уже существует в таблице CoilDB базы данных',
            )
        else:
            django_models.CoilDB.objects.create(reference=coil_domain.reference,
                                                product_id=coil_domain.product_id,
                                                quantity=coil_domain.initial_quantity,
                                                recommended_balance=coil_domain.recommended_balance,
                                                acceptable_loss=coil_domain.acceptable_loss)

    def update(self, coil_domain: domain_logic.Coil) -> None:
        """
        Принимает экземпляр класса Coil доменной модели,
        обновляет соответствующую ему запись в таблице CoilDB.

        Определяет запись, соответствующую экземпляру, по идентификатору reference.
        Вызывает исключение при отсутствии подходящей записи.
        Связывает обновляемую запись с записями таблицы OrderLine, в соответствии
        с атрибутом allocations экземпляра класса Coil доменной модели,
        путем создания записей промежуточной таблицы AllocationDB.
        """
        # Получение записи таблицы CoilDB или вызов исключения
        coil_record = DjangoCoilRepository._get_coil_record_from_db(coil_domain.reference)
        django_models.CoilDB.objects.filter(reference=coil_domain.reference).update(
            product_id=coil_domain.product_id,
            quantity=coil_domain.initial_quantity,
            recommended_balance=coil_domain.recommended_balance,
            acceptable_loss=coil_domain.acceptable_loss,
        )
        django_models.AllocationDB.objects.filter(coil_record=coil_record).delete()
        coil_record.allocationdb_set.set(DjangoCoilRepository._get_or_create_allocation_record(
            coil_record, orderline_domain) for orderline_domain in coil_domain.allocations)

    def delete(self, reference: str) -> None:
        """
        Принимает идентификатор экземпляра класса Coil доменной модели,
        удаляет соответствующую ему запись в таблице CoilDB.

        Вызывает исключение при отсутствии подходящей записи.
        """
        # Получение записи таблицы CoilDB или вызов исключения
        DjangoCoilRepository._get_coil_record_from_db(reference)
        django_models.CoilDB.objects.filter(reference=reference).delete()

    def coils_list(self) -> list[domain_logic.Coil]:
        return [mapper.coil_record_to_domain(coil) for coil in django_models.CoilDB.objects.all()]

    @staticmethod
    def _get_coil_record_from_db(reference: str) -> django_models.CoilDB:
        """
        Принимает идентификатор экземпляра класса Coil доменной модели,
        возвращает соответствующую ему одиночную запись таблицы CoilDB.

        Вызывает исключение при отсутствии подходящей записи.
        """
        try:
            coil_record = django_models.CoilDB.objects.get(reference=reference)
        except django_models.CoilDB.DoesNotExist:
            raise exceptions.DBCoilRecordDoesNotExist(
                f'Запись с reference={reference} отсутствует в таблице CoilDB базы данных',
            )
        return coil_record

    @staticmethod
    def _get_or_create_allocation_record(coil_record: django_models.CoilDB,
                                         orderline_domain: domain_logic.OrderLine) -> django_models.AllocationDB:
        """
        Принимает запись таблицы CoilDB и экземпляр класса OrderLine доменной модели,
        возвращает существующую или создает новую запись промежуточной таблицы AllocationDB,
        которая связывает соответствующие записи таблиц CoilDB и OrderLineDB.

        Вызывает исключение при отсутствии записи таблицы OrderLineDB,
        соответствующей экземпляру OrderLine доменной модели.
        """
        # Получение записи таблицы OrderLineDB или вызов исключения
        orderline_record = DjangoOrderLineRepository._get_orderline_record_from_db(
            order_id=orderline_domain.order_id,
            line_item=orderline_domain.line_item,
        )
        allo, _ = django_models.AllocationDB.objects.get_or_create(coil_record=coil_record,
                                                                   orderline_record=orderline_record)
        return allo


class DjangoOrderLineRepository:
    def get(self, order_id: str, line_item: str) -> domain_logic.OrderLine:
        """
        Принимает идентификаторы экземпляра класса OrderLine доменной модели,
        возвращает экземпляр класса OrderLine доменной модели,
        полученный из соответствующей записи таблицы OrderLineDB.

        Вызывает исключение при отсутствии подходящей записи.
        """
        # Получение записи таблицы OrderLineDB или вызов исключения
        orderline_record = DjangoOrderLineRepository._get_orderline_record_from_db(order_id, line_item)
        orderline_domain = mapper.orderline_record_to_domain(orderline_record)
        return orderline_domain

    def add(self, orderline_domain: domain_logic.OrderLine) -> None:
        """
        Принимает экземпляр класса OrderLine доменной модели,
        создает соответствующую ему запись в таблице OrderLineDB.

        Вызывает исключение, которое возникает при совпадении идентификаторов
        order_id, line_item у экземпляра и одной из существующих записей.
        """
        if django_models.OrderLineDB.objects.filter(order_id=orderline_domain.order_id,
                                                    line_item=orderline_domain.line_item):
            raise exceptions.DBOrderLineRecordAlreadyExist(
                f'Запись с order_id={orderline_domain.order_id} и line_item={orderline_domain.line_item}'
                f' уже существует в таблице OrderLineDB базы данных',
            )
        else:
            django_models.OrderLineDB.objects.create(order_id=orderline_domain.order_id,
                                                     line_item=orderline_domain.line_item,
                                                     product_id=orderline_domain.product_id,
                                                     quantity=orderline_domain.quantity)

    def update(self, orderline_domain: domain_logic.OrderLine) -> None:
        """
        Принимает экземпляр класса OrderLine доменной модели,
        обновляет соответствующую ему запись в таблице OrderLineDB.

        Определяет запись, соответствующую экземпляру, по идентификаторам order_id, line_item.
        Вызывает исключение при отсутствии подходящей записи.
        """
        # Получение записи таблицы OrderLineDB или вызов исключения
        DjangoOrderLineRepository._get_orderline_record_from_db(orderline_domain.order_id, orderline_domain.line_item)
        django_models.OrderLineDB.objects.filter(order_id=orderline_domain.order_id,
                                                 line_item=orderline_domain.line_item).update(
            product_id=orderline_domain.product_id,
            quantity=orderline_domain.quantity,
        )

    def delete(self, order_id: str, line_item: str) -> None:
        """
        Принимает идентификаторы экземпляра класса OrderLine доменной модели,
        удаляет соответствующую им запись.

        Вызывает исключение при отсутствии подходящей записи.
        """
        # Получение записи таблицы OrderLineDB или вызов исключения
        DjangoOrderLineRepository._get_orderline_record_from_db(order_id, line_item)
        django_models.OrderLineDB.objects.filter(order_id=order_id, line_item=line_item).delete()

    def order_lines_list(self) -> list[domain_logic.OrderLine]:
        return [mapper.orderline_record_to_domain(line) for line in django_models.OrderLineDB.objects.all()]

    @staticmethod
    def _get_orderline_record_from_db(order_id: str, line_item: str) -> django_models.OrderLineDB:
        """
        Принимает идентификаторы экземпляра класса OrderLine доменной модели,
        возвращает соответствующую им одиночную запись таблицы OrderLineDB.

        Вызывает исключение при отсутствии подходящей записи.
        """
        try:
            orderline_record = django_models.OrderLineDB.objects.get(order_id=order_id, line_item=line_item)
        except django_models.OrderLineDB.DoesNotExist:
            raise exceptions.DBOrderLineRecordDoesNotExist(
                f'Запись с order_id={order_id} и line_item={line_item}'
                f' отсутствует в таблице OrderLineDB базы данных',
            )
        return orderline_record
