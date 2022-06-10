import pytest

from allocation.domain import domain_logic
from allocation.exceptions.exceptions import DBCoilRecordAlreadyExist, DBOrderLineRecordAlreadyExist
from allocation.services import unit_of_work


@pytest.mark.django_db(transaction=True)
def test_uow_saves_a_coil():
    data = {'reference': 'Бухта-020', 'product_id': 'АВВГ_2х2,5', 'quantity': 150,
            'recommended_balance': 10, 'acceptable_loss': 2}

    uow = unit_of_work.DjangoCoilUnitOfWork()
    with uow:
        coil = domain_logic.Coil(data['reference'], data['product_id'], data['quantity'],
                                            data['recommended_balance'], data['acceptable_loss'])
        uow.coil_repo.add(coil)
        uow.commit()
    saved_coil = uow.coil_repo.get(data['reference'])

    assert saved_coil.reference == data['reference']
    assert saved_coil.product_id == data['product_id']
    assert saved_coil.initial_quantity == data['quantity']
    assert saved_coil.recommended_balance == data['recommended_balance']
    assert saved_coil.acceptable_loss == data['acceptable_loss']


@pytest.mark.django_db(transaction=True)
def test_uow_roll_back_uncommitted_coil():
    data = {'reference': 'Бухта-020', 'product_id': 'АВВГ_2х2,5',
            'quantity': 150, 'recommended_balance': 10, 'acceptable_loss': 2}
    uow = unit_of_work.DjangoCoilUnitOfWork()

    with uow:
        coil = domain_logic.Coil(data['reference'], data['product_id'], data['quantity'],
                                 data['recommended_balance'], data['acceptable_loss'])
        uow.coil_repo.add(coil)
    list_of_coils = uow.coil_repo.list()

    assert list_of_coils == []


@pytest.mark.django_db(transaction=True)
def test_uow_roll_back_resaving_an_existing_coil_record():
    data_1 = {'reference': 'Бухта-025', 'product_id': 'АВВГ_3х2,5', 'quantity': 200,
              'recommended_balance': 15, 'acceptable_loss': 2}
    data_2 = {'reference': 'Бухта-025', 'product_id': 'АВВГ_4х16', 'quantity': 100,
              'recommended_balance': 20, 'acceptable_loss': 5}
    uow = unit_of_work.DjangoCoilUnitOfWork()

    with pytest.raises(DBCoilRecordAlreadyExist):
        with uow:
            coil_1 = domain_logic.Coil(data_1['reference'], data_1['product_id'], data_1['quantity'],
                                            data_1['recommended_balance'], data_1['acceptable_loss'])
            uow.coil_repo.add(coil_1)
            uow.commit()
            coil_2 = domain_logic.Coil(data_2['reference'], data_2['product_id'], data_2['quantity'],
                                            data_2['recommended_balance'], data_2['acceptable_loss'])
            uow.coil_repo.add(coil_2)
            uow.commit()
    list_of_coils = uow.coil_repo.list()

    assert len(list_of_coils) == 1
    assert list_of_coils[0].product_id == 'АВВГ_3х2,5'


@pytest.mark.django_db(transaction=True)
def test_uow_saves_a_line():
    data = {'order_id': 'Заказ-040', 'line_item': 'Позиция-001', 'product_id': 'АВВГ_2х6', 'quantity': 14}
    uow = unit_of_work.DjangoOrderLineUnitOfWork()

    with uow:
        line = domain_logic.OrderLine(data['order_id'], data['line_item'], data['product_id'], data['quantity'])
        uow.line_repo.add(line)
        uow.commit()
    saved_line = uow.line_repo.get(order_id=data['order_id'], line_item=data['line_item'])

    assert saved_line.order_id == data['order_id']
    assert saved_line.line_item == data['line_item']
    assert saved_line.product_id == data['product_id']
    assert saved_line.quantity == data['quantity']


@pytest.mark.django_db(transaction=True)
def test_uow_roll_back_uncommitted_line():
    data = {'order_id': 'Заказ-040', 'line_item': 'Позиция-001', 'product_id': 'АВВГ_2х6', 'quantity': 14}

    uow = unit_of_work.DjangoOrderLineUnitOfWork()
    with uow:
        line = domain_logic.OrderLine(data['order_id'], data['line_item'], data['product_id'], data['quantity'])
        uow.line_repo.add(line)
    list_of_lines = uow.line_repo.list()

    assert list_of_lines == []


@pytest.mark.django_db(transaction=True)
def test_uow_roll_back_resaving_an_existing_line_record():
    data_1 = {'order_id': 'Заказ-040', 'line_item': 'Позиция-001', 'product_id': 'АВВГ_2х6', 'quantity': 14}
    data_2 = {'order_id': 'Заказ-040', 'line_item': 'Позиция-001', 'product_id': 'АВВГ_3х2,5', 'quantity': 20}
    uow = unit_of_work.DjangoOrderLineUnitOfWork()

    with pytest.raises(DBOrderLineRecordAlreadyExist):
        with uow:
            line_1 = domain_logic.OrderLine(data_1['order_id'], data_1['line_item'],
                                            data_1['product_id'], data_1['quantity'])
            uow.line_repo.add(line_1)
            uow.commit()
            line_2 = domain_logic.OrderLine(data_2['order_id'], data_2['line_item'],
                                            data_2['product_id'], data_2['quantity'])
            uow.line_repo.add(line_2)
            uow.commit()
    list_of_lines = uow.line_repo.list()

    assert len(list_of_lines) == 1
    assert list_of_lines[0].product_id == 'АВВГ_2х6'
