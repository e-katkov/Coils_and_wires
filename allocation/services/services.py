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
        db_coil = uow_coil.coil_repo.get(reference=allocation_coil.reference)
        db_coil.allocations.add(line)
        uow_coil.coil_repo.update(db_coil)
        result_coil = db_coil
        uow_coil.commit()
    return result_coil
