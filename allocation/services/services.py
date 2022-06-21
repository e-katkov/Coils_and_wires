from allocation.domain import domain_logic
from allocation.services import unit_of_work


def get_a_coil(
        reference: str,
        uow: unit_of_work.AbstractCoilUnitOfWork
) -> domain_logic.Coil:
    with uow:
        coil = uow.coil_repo.get(reference)
    return coil


def add_a_coil(
        reference: str,
        product_id: str,
        quantity: int,
        recommended_balance: int,
        acceptable_loss: int,
        uow: unit_of_work.AbstractCoilUnitOfWork
):
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
        uow: unit_of_work.AbstractCoilUnitOfWork
) -> set[domain_logic.OrderLine]:
    with uow:
        # Получение coil, который необходимо обновить
        db_coil = uow.coil_repo.get(reference)
        # Создание coil, который обновит db_coil
        input_coil = domain_logic.Coil(reference, product_id, quantity, recommended_balance, acceptable_loss)
        # Получение множества orderlines, ранее размещенных в db_coil,
        # которые смогут быть размещены в input_coil после обновления db_coil
        reallocated_lines = db_coil.reallocate(input_coil)
        # Размещение orderlines, принадлежащих множеству reallocated_lines, в input_coil
        input_coil.allocations = reallocated_lines
        # Обновление input_coil в базе данных
        uow.coil_repo.update(input_coil)
        # Получение множества orderlines, которые перестанут быть размещенными после обновления db_coil
        deallocated_lines = db_coil.allocations - reallocated_lines
        uow.commit()
    return deallocated_lines


def delete_a_coil(
        reference: str,
        uow: unit_of_work.AbstractCoilUnitOfWork,
) -> set[domain_logic.OrderLine]:
    with uow:
        # Получение coil, который необходимо удалить
        coil = uow.coil_repo.get(reference)
        # Получение множества orderlines, которые перестанут быть размещенными после удаления coil
        deallocated_lines = coil.allocations
        # Удаление coil
        uow.coil_repo.delete(reference)
        uow.commit()
    return deallocated_lines


def get_a_line(
        order_id: str,
        line_item: str,
        uow: unit_of_work.AbstractOrderLineUnitOfWork
) -> domain_logic.OrderLine:
    with uow:
        line = uow.line_repo.get(order_id, line_item)
    return line


def add_a_line(
        order_id: str,
        line_item: str,
        product_id: str,
        quantity: int,
        uow: unit_of_work.AbstractOrderLineUnitOfWork
):
    with uow:
        line = domain_logic.OrderLine(order_id, line_item, product_id, quantity)
        uow.line_repo.add(line)
        uow.commit()


def update_a_line(
        order_id: str,
        line_item: str,
        product_id: str,
        quantity: int,
        uow_line: unit_of_work.AbstractOrderLineUnitOfWork,
        uow_coil: unit_of_work.AbstractCoilUnitOfWork
) -> domain_logic.Coil:
    with uow_line:
        # Получение orderline, которую необходимо обновить
        db_line = uow_line.line_repo.get(order_id=order_id, line_item=line_item)
        # Получение allocation_coil, куда размещена db_line
        allocation_coil = uow_line.line_repo.get_an_allocation_coil(db_line)
    # Отмена размещения db_line в allocation_coil, если он не "поддельный"
    with uow_coil:
        if not allocation_coil.reference == 'fake':
            allocation_coil.deallocate(db_line)
            uow_coil.coil_repo.update(allocation_coil)
            uow_coil.commit()
    # Обновление db_line до input_line
    with uow_line:
        # Создание orderline, которая обновит db_line
        input_line = domain_logic.OrderLine(order_id, line_item, product_id, quantity)
        # Обновление input_line в базе данных
        uow_line.line_repo.update(input_line)
        uow_line.commit()
    # Размещение input_line
    with uow_coil:
        if allocation_coil.reference == 'fake':
            # Возврат "поддельного" coil в случае, если изначально allocation_coil отсутствовал
            fake_coil = allocation_coil
            return fake_coil
        else:
            # Попытка разместить input_line в найденный allocation_coil
            if allocation_coil.can_allocate(input_line):
                allocation_coil.allocate(input_line)
                uow_coil.coil_repo.update(allocation_coil)
                uow_coil.commit()
                return allocation_coil
            # Если попытка неудачная, то выполнение обычного размещения
            else:
                list_of_coils = uow_coil.coil_repo.list()
                allocation_coil = domain_logic.allocate_to_list_of_coils(line=input_line, coils=list_of_coils)
                uow_coil.coil_repo.update(allocation_coil)
                uow_coil.commit()
                return allocation_coil


def delete_a_line(
        order_id: str,
        line_item: str,
        uow: unit_of_work.AbstractOrderLineUnitOfWork,
) -> domain_logic.Coil:
    with uow:
        # Получение orderline, которую необходимо удалить
        line = uow.line_repo.get(order_id=order_id, line_item=line_item)
        # Получение allocation_coil, куда размещена line
        allocation_coil = uow.line_repo.get_an_allocation_coil(line)
        # Удаление line
        uow.line_repo.delete(order_id=order_id, line_item=line_item)
        uow.commit()
    return allocation_coil


def get_an_allocation_coil(
        order_id: str,
        line_item: str,
        uow: unit_of_work.AbstractOrderLineUnitOfWork,
) -> domain_logic.Coil:
    with uow:
        # Получение orderline, для которой необходимо получить coil, в который она размещена
        line = uow.line_repo.get(order_id=order_id, line_item=line_item)
        # Получение allocation_coil, куда размещена line
        allocation_coil = uow.line_repo.get_an_allocation_coil(line)
        return allocation_coil


def allocate(
        order_id: str,
        line_item: str,
        uow_line: unit_of_work.AbstractOrderLineUnitOfWork,
        uow_coil: unit_of_work.AbstractCoilUnitOfWork
) -> domain_logic.Coil:
    with uow_line:
        # Получение orderline, которую необходимо разместить
        line = uow_line.line_repo.get(order_id, line_item)
    with uow_coil:
        # Размещение orderline и получение allocation_coil, в которую она размещена
        list_of_coils = uow_coil.coil_repo.list()
        allocation_coil = domain_logic.allocate_to_list_of_coils(line=line, coils=list_of_coils)
        # Обновление allocation_coil
        uow_coil.coil_repo.update(allocation_coil)
        uow_coil.commit()
    return allocation_coil


def deallocate(
        order_id: str,
        line_item: str,
        uow_line: unit_of_work.AbstractOrderLineUnitOfWork,
        uow_coil: unit_of_work.AbstractCoilUnitOfWork
) -> domain_logic.Coil:
    with uow_line:
        # Получение orderline, для которой необходимо отменить размещение
        line = uow_line.line_repo.get(order_id=order_id, line_item=line_item)
        # Получение allocation_coil, куда размещена line
        allocation_coil = uow_line.line_repo.get_an_allocation_coil(line)

    if allocation_coil.reference == 'fake':
        # Возврат allocation_coil, при условии, что он "поддельный"
        return allocation_coil
    else:
        with uow_coil:
            # Отмена размещения line
            allocation_coil.deallocate(line)
            # Обновление allocation_coil в базе данных
            uow_coil.coil_repo.update(allocation_coil)
            uow_coil.commit()
        return allocation_coil
