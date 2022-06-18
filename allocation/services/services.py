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
        input_coil = domain_logic.Coil(reference, product_id, quantity, recommended_balance, acceptable_loss)
        db_coil = uow.coil_repo.get(reference)
        reallocated_lines = db_coil.reallocate(input_coil)
        input_coil.allocations = reallocated_lines
        uow.coil_repo.update(input_coil)
        deallocated_lines = db_coil.allocations - reallocated_lines
        uow.commit()
    return deallocated_lines


def delete_a_coil(
        reference: str,
        uow: unit_of_work.AbstractCoilUnitOfWork,
) -> set[domain_logic.OrderLine]:
    with uow:
        # Определение coil, которую необходимо удалить
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
    # db_line - это orderline, которую необходимо обновить
    # Определение allocation_coil, куда размещена db_line
    with uow_line:
        db_line = uow_line.line_repo.get(order_id=order_id, line_item=line_item)
        allocation_coil = uow_line.line_repo.get_an_allocation_coil(db_line)
    # Удаление db_line из множества allocations найденного allocation_coil
    with uow_coil:
        if not allocation_coil.reference == 'fake':
            allocation_coil.deallocate(db_line)
            uow_coil.coil_repo.update(allocation_coil)
            uow_coil.commit()
    # Обновление db_line до input_line
    with uow_line:
        input_line = domain_logic.OrderLine(order_id, line_item, product_id, quantity)
        uow_line.line_repo.update(input_line)
        uow_line.commit()
    # Размещение (allocation) input_line
    # В первую очередь выполняется попытка разместить input_line в найденный allocation_coil
    # Возврат "поддельного" coil в случае, если изначально allocation_coil отсутствовал
    with uow_coil:
        if allocation_coil.reference == 'fake':
            fake_coil = allocation_coil
            return fake_coil
        else:
            if allocation_coil.can_allocate(input_line):
                allocation_coil.allocate(input_line)
                uow_coil.coil_repo.update(allocation_coil)
                uow_coil.commit()
                return allocation_coil
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
        # Удаление orderline
        uow.line_repo.delete(order_id=order_id, line_item=line_item)
        uow.commit()
        return allocation_coil


def allocate(
        order_id: str,
        line_item: str,
        uow_line: unit_of_work.AbstractOrderLineUnitOfWork,
        uow_coil: unit_of_work.AbstractCoilUnitOfWork
) -> domain_logic.Coil:
    with uow_line:
        line = uow_line.line_repo.get(order_id, line_item)
    with uow_coil:
        list_of_coils = uow_coil.coil_repo.list()
        allocation_coil = domain_logic.allocate_to_list_of_coils(line=line, coils=list_of_coils)
        uow_coil.coil_repo.update(allocation_coil)
        uow_coil.commit()
    return allocation_coil
