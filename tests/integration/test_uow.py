import pytest

from allocation.domain import domain_logic
from allocation.services import unit_of_work


@pytest.mark.django_db(transaction=True)
def test_uow_save_committed_coil():
    """При использовании метода commit() произойдет фиксация изменений в базе данных."""
    uow = unit_of_work.DjangoCoilUnitOfWork()
    coil = domain_logic.Coil('Бухта-020', 'АВВГ_2х2,5', 150, 10, 2)

    with uow:
        uow.coil_repo.add(coil)
        uow.commit()
    saved_coil = uow.coil_repo.get('Бухта-020')

    assert saved_coil.reference == coil.reference
    assert saved_coil.product_id == coil.product_id
    assert saved_coil.initial_quantity == coil.initial_quantity


@pytest.mark.django_db(transaction=True)
def test_uow_roll_back_uncommitted_coil():
    """
    При неиспользовании метода commit() не произойдет фиксации изменений в базе данных.
    Будет выполнен метод rollback() и изменения будут отменены.
    """
    uow = unit_of_work.DjangoCoilUnitOfWork()
    coil = domain_logic.Coil('Бухта-021', 'АВВГ_2х2,5', 150, 10, 2)

    with uow:
        uow.coil_repo.add(coil)
    coils_list = uow.coil_repo.list()

    assert coils_list == []


@pytest.mark.django_db(transaction=True)
def test_uow_save_committed_line():
    """При использовании метода commit() произойдет фиксация изменений в базе данных."""
    uow = unit_of_work.DjangoOrderLineUnitOfWork()
    line = domain_logic.OrderLine('Заказ-020', 'Позиция-001', 'АВВГ_2х2,5', 15)

    with uow:
        uow.line_repo.add(line)
        uow.commit()
    saved_line = uow.line_repo.get('Заказ-020', 'Позиция-001')

    assert saved_line.product_id == line.product_id
    assert saved_line.quantity == line.quantity


@pytest.mark.django_db(transaction=True)
def test_uow_roll_back_uncommitted_line():
    """
    При неиспользовании метода commit() не произойдет фиксации изменений в базе данных.
    Будет выполнен метод rollback() и изменения будут отменены.
    """
    uow = unit_of_work.DjangoOrderLineUnitOfWork()
    line = domain_logic.OrderLine('Заказ-021', 'Позиция-001', 'АВВГ_2х2,5', 15)

    with uow:
        uow.line_repo.add(line)
    lines_list = uow.line_repo.list()

    assert lines_list == []
