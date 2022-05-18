import pytest

from allocation.domain import domain_logic
from allocation.services import unit_of_work


@pytest.mark.django_db(transaction=True)
def test_uow_saves_a_coil():
    data = {'reference': 'Бухта-020',
            'product_id': 'АВВГ_2х2,5',
            'quantity': 150,
            'recommended_balance': 10,
            'acceptable_loss': 2}
    uow = unit_of_work.DjangoCoilUnitOfWork()
    with uow:
        uow.coil_repo.add(domain_logic.Coil(data['reference'],
                                            data['product_id'],
                                            data['quantity'],
                                            data['recommended_balance'],
                                            data['acceptable_loss']))
        uow.commit()
    saved_coil = uow.coil_repo.get(data['reference'])
    assert saved_coil.reference == data['reference']
    assert saved_coil.product_id == data['product_id']
    assert saved_coil._initial_quantity == data['quantity']
    assert saved_coil.recommended_balance == data['recommended_balance']
    assert saved_coil.acceptable_loss == data['acceptable_loss']

