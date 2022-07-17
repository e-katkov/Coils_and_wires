import pytest

from allocation.domain import domain_logic
from allocation.services import unit_of_work


@pytest.mark.django_db(transaction=True)
def test_uow_save_committed_coil():
    """При использовании метода commit() произойдет фиксация изменений в базе данных."""
    uow = unit_of_work.DjangoUnitOfWork()
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
    uow = unit_of_work.DjangoUnitOfWork()
    coil = domain_logic.Coil('Бухта-021', 'АВВГ_2х2,5', 150, 10, 2)

    with uow:
        uow.coil_repo.add(coil)
    coils_list = uow.coil_repo.coils_list()

    assert coils_list == []
