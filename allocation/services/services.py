from allocation.domain import domain_logic
from allocation.services import unit_of_work


def add_coil(
        reference: str,
        product_id: str,
        quantity: int,
        recommended_balance: int,
        acceptable_loss: int,
        uow: unit_of_work.AbstractCoilUnitOfWork
):
    with uow:
        uow.coil_repo.add(domain_logic.Coil(reference, product_id, quantity, recommended_balance, acceptable_loss))
        uow.commit()


def add_line(
        order_id: str,
        line_item: str,
        product_id: str,
        quantity: int,
        uow: unit_of_work.AbstractOrderLineUnitOfWork
):
    with uow:
        uow.line_repo.add(domain_logic.OrderLine(order_id, line_item, product_id, quantity))
        uow.commit()


def allocate(
        order_id: str,
        line_item: str,
        uow_line: unit_of_work.AbstractOrderLineUnitOfWork,
        uow_coil: unit_of_work.AbstractCoilUnitOfWork
):
    with uow_line:
        line = uow_line.line_repo.get(order_id, line_item)
    with uow_coil:
        list_of_coils = uow_coil.coil_repo.list()
        coil = domain_logic.allocate_to_list_of_coils(line=line, coils=list_of_coils)
        uow_coil.coil_repo.update(coil)
        result_coil = coil
        uow_coil.commit()
    return result_coil
