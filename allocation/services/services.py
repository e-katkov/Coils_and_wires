from allocation.domain import domain_logic
from allocation.services import unit_of_work


def get_a_coil(
        reference: str,
        uow: unit_of_work.AbstractUnitOfWork,
) -> domain_logic.Coil:
    """
    Принимает идентификатор бухты - экземпляра класса Coil доменной модели,
    возвращает соответствующий ему экземпляр класса Coil, полученный из записи в базе данных.
    """
    with uow:
        coil = uow.coil_repo.get(reference)
        return coil


def add_a_coil(
        reference: str,
        product_id: str,
        quantity: int,
        recommended_balance: int,
        acceptable_loss: int,
        uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    """
    Принимает атрибуты бухты - экземпляра класса Coil доменной модели,
    создает соответствующую им запись в таблице Coil базы данных.
    """
    with uow:
        coil = domain_logic.Coil(reference, product_id, quantity, recommended_balance, acceptable_loss)
        uow.coil_repo.add(coil)
        uow.commit()


def update_a_coil(
        reference: str,
        product_id: str,
        quantity: int,
        recommended_balance: int,
        acceptable_loss: int,
        uow: unit_of_work.AbstractUnitOfWork,
) -> set[domain_logic.OrderLine]:
    """
    Принимает атрибуты бухты - экземпляра класса Coil доменной модели,
    обновляет соответствующую им запись в таблице Coil базы данных.
    Возвращает множество товарных позиций - экземпляров класса OrderLine доменной модели,
    полученных из записей в базе данных, которые перестанут быть размещенными после обновления записи.
    """
    with uow:
        # Получение бухты, которую необходимо обновить
        db_coil = uow.coil_repo.get(reference)
        # Создание бухты, которая обновит db_coil
        input_coil = domain_logic.Coil(reference, product_id, quantity, recommended_balance, acceptable_loss)
        # Получение множества товарных позиций, ранее размещенных в db_coil,
        # которые смогут быть размещены в input_coil после обновления db_coil
        reallocated_lines = db_coil.reallocate(input_coil)
        # Размещение товарных позиций, принадлежащих reallocated_lines, в бухте input_coil
        input_coil.allocations = reallocated_lines
        # Обновление input_coil в базе данных
        uow.coil_repo.update(input_coil)
        # Получение множества товарных позиций, которые перестанут быть размещенными после обновления db_coil
        deallocated_lines = db_coil.allocations - reallocated_lines
        uow.commit()
        return deallocated_lines


def delete_a_coil(
        reference: str,
        uow: unit_of_work.AbstractUnitOfWork,
) -> set[domain_logic.OrderLine]:
    """
    Принимает идентификатор бухты - экземпляра класса Coil доменной модели,
    удаляет соответствующую ему запись в таблице Coil базы данных.
    Возвращает множество товарных позиций - экземпляров класса OrderLine доменной модели,
    полученных из записей в базе данных, которые перестанут быть размещенными после удаления записи.
    """
    with uow:
        # Получение бухты, которую необходимо удалить
        coil = uow.coil_repo.get(reference)
        # Получение множества товарных позиций, которые перестанут быть размещенными после удаления coil
        deallocated_lines = coil.allocations
        # Удаление coil из базы данных
        uow.coil_repo.delete(reference)
        uow.commit()
        return deallocated_lines


def get_a_line(
        order_id: str,
        line_item: str,
        uow: unit_of_work.AbstractUnitOfWork,
) -> domain_logic.OrderLine:
    """
    Принимает идентификаторы товарной позиции - экземпляра класса OrderLine доменной модели,
    возвращает соответствующий им экземпляр класса OrderLine, полученный из записи в базе данных.
    """
    with uow:
        line = uow.line_repo.get(order_id, line_item)
        return line


def add_a_line(
        order_id: str,
        line_item: str,
        product_id: str,
        quantity: int,
        uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    """
    Принимает атрибуты товарной позиции - экземпляра класса OrderLine доменной модели,
    создает соответствующую им запись в таблице OrderLine базы данных.
    """
    with uow:
        line = domain_logic.OrderLine(order_id, line_item, product_id, quantity)
        uow.line_repo.add(line)
        uow.commit()


def update_a_line(
        order_id: str,
        line_item: str,
        product_id: str,
        quantity: int,
        uow: unit_of_work.AbstractUnitOfWork,
) -> domain_logic.Coil:
    """
    Принимает атрибуты товарной позиции - экземпляра класса OrderLine доменной модели,
    обновляет соответствующую им запись в таблице OrderLine базы данных.
    Возвращает бухту - экземпляр класса Coil, полученный из записи в базе данных,
    в которой будет размещена товарная позиция после ее обновления.
    """
    with uow:
        # Получение товарной позиции, которую необходимо обновить
        db_line = uow.line_repo.get(order_id=order_id, line_item=line_item)
        # Получение бухты, в которой размещена обновляемая товарная позиция
        allocation_coil = get_an_allocation_coil(order_id, line_item, uow)

        # Отмена размещения db_line в allocation_coil, если она не "поддельная"
        if not allocation_coil.reference == 'fake':
            allocation_coil.deallocate(db_line)
            uow.coil_repo.update(allocation_coil)
            uow.commit()

        # Обновление db_line до input_line
        # Создание товарной позиции, которая обновит db_line
        input_line = domain_logic.OrderLine(order_id, line_item, product_id, quantity)
        # Обновление input_line в базе данных
        uow.line_repo.update(input_line)
        uow.commit()

        # Размещение обновленной товарной позиции и возврат бухты, в которой она будет размещена
        if allocation_coil.reference == 'fake':
            # Возврат "поддельной" бухты, если изначально товарная позиция не была размещена
            return allocation_coil
        else:
            # Попытка разместить input_line в найденной allocation_coil
            if allocation_coil.can_allocate(input_line):
                allocation_coil.allocate(input_line)
                uow.coil_repo.update(allocation_coil)
                uow.commit()
                return allocation_coil
            # Если попытка неудачная, то выполнение обычного размещения товарной позиции
            else:
                list_of_coils = uow.coil_repo.coils_list()
                allocation_coil = domain_logic.allocate_to_list_of_coils(line=input_line, coils=list_of_coils)
                uow.coil_repo.update(allocation_coil)
                uow.commit()
                return allocation_coil


def delete_a_line(
        order_id: str,
        line_item: str,
        uow: unit_of_work.AbstractUnitOfWork,
) -> domain_logic.Coil:
    """
    Принимает идентификаторы товарной позиции - экземпляра класса OrderLine доменной модели,
    удаляет соответствующую им запись в таблице OrderLine базы данных.
    Возвращает бухту - экземпляр класса Coil, полученный из записи в базе данных,
    в которой была размещена удаленная товарная позиция.
    """
    # Получение бухты, в которой размещена удаляемая товарная позиция
    allocation_coil = get_an_allocation_coil(order_id, line_item, uow)
    with uow:
        # Получение товарной позиции, которую необходимо удалить
        line = uow.line_repo.get(order_id=order_id, line_item=line_item)
        # Удаление товарной позиции из базы данных
        uow.line_repo.delete(order_id=order_id, line_item=line_item)
        uow.commit()

        # Отмена размещения товарной позиции и возврат бухты, в которой она была размещена
        if allocation_coil.reference == 'fake':
            # Возврат allocation_coil, при условии, что он "поддельный"
            return allocation_coil
        else:
            # Отмена размещения line в allocation_coil
            allocation_coil.deallocate(line)
            # Обновление allocation_coil в базе данных
            uow.coil_repo.update(allocation_coil)
            uow.commit()
            return allocation_coil


def get_an_allocation_coil(
        order_id: str,
        line_item: str,
        uow: unit_of_work.AbstractUnitOfWork,
) -> domain_logic.Coil:
    """
    Принимает идентификаторы товарной позиции - экземпляра класса OrderLine доменной модели.
    Возвращает бухту - экземпляр класса Coil, полученный из записи в базе данных или "поддельный",
    в которой размещена товарная позиция.
    """
    with uow:
        # Получение товарной позиции, для которой необходимо найти бухту, где она размещена.
        # Получение необходимо для проверки существования товарной позиции
        uow.line_repo.get(order_id=order_id, line_item=line_item)

        # Получение allocation_coil - бухты, в которой размещена товарная позиция.
        # Если бухта не будет найдена, то allocation_coil будет "поддельной" бухтой
        allocation_coil = domain_logic.Coil('fake', 'fake', 1, 1, 1)
        coils_list = uow.coil_repo.coils_list()
        for coil in coils_list:
            for line in coil.allocations:
                if line.order_id == order_id and line.line_item == line_item:
                    allocation_coil = coil
        return allocation_coil


def allocate(
        order_id: str,
        line_item: str,
        uow: unit_of_work.AbstractUnitOfWork,
) -> domain_logic.Coil:
    """
    Принимает идентификаторы товарной позиции - экземпляра класса OrderLine доменной модели,
    размещает товарную позицию в одной из бухт.
    Возвращает бухту - экземпляр класса Coil, полученный из записи в базе данных,
    в которой размещена товарная позиция.
    """
    with uow:
        # Получение товарной позиции, которую необходимо разместить
        line = uow.line_repo.get(order_id, line_item)

        # Размещение товарной позиции в бухте ее и возврат
        list_of_coils = uow.coil_repo.coils_list()
        allocation_coil = domain_logic.allocate_to_list_of_coils(line=line, coils=list_of_coils)
        # Обновление allocation_coil в базе данных
        uow.coil_repo.update(allocation_coil)
        uow.commit()
        return allocation_coil


def deallocate(
        order_id: str,
        line_item: str,
        uow: unit_of_work.AbstractUnitOfWork,
) -> domain_logic.Coil:
    """
    Принимает идентификаторы товарной позиции - экземпляра класса OrderLine доменной модели,
    отменяет размещение товарной позиции в бухте.
    Возвращает бухту - экземпляр класса Coil, полученный из записи в базе данных,
    в которой ранее была размещена товарная позиция.
    """
    with uow:
        # Получение товарной позиции, для которой необходимо отменить размещение
        line = uow.line_repo.get(order_id=order_id, line_item=line_item)

        # Получение бухты, в которой размещена line
        allocation_coil = get_an_allocation_coil(order_id, line_item, uow)
        # Отмена размещения товарной позиции и возврат бухты, в которой она была размещена
        if allocation_coil.reference == 'fake':
            # Возврат allocation_coil, при условии, что он "поддельный"
            return allocation_coil
        else:
            # Отмена размещения line в allocation_coil
            allocation_coil.deallocate(line)
            # Обновление allocation_coil в базе данных
            uow.coil_repo.update(allocation_coil)
            uow.commit()
            return allocation_coil
