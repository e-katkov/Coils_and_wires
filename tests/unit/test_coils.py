import pytest

from allocation.domain.domain_logic import Coil, OrderLine


def test_allocating_reduced_available_quantity():
    coil = Coil('Бухта-001', 'АВВГ_2х2,5', 150, 5, 1)
    line = OrderLine('Заказ-001', 'АВВГ_2х2,5', 40)

    coil.allocate(line)

    assert coil.available_quantity == 110


@pytest.mark.parametrize(
    'coil_quantity, line_quantity, result',
    [(170, 20, True), (60, 110, False), (70, 70, True)],
    ids=['170-20', '60-110', '70-70'])
def test_can_allocate_at_various_quantities(coil_quantity, line_quantity, result):
    coil = Coil('Бухта-002', 'АВВГ_3х1,5', coil_quantity, 5, 1)
    line = OrderLine('Заказ-002', 'АВВГ_3х1,5', line_quantity)

    assert coil.can_allocate(line) is result


@pytest.mark.parametrize(
    'coil_product_id, line_product_id, result',
    [('АВВГ_2х2,5', 'АВВГ_2х2,5', True), ('АВВГ_2х2,5', 'АВВГ_3х1,5', False)],
    ids=['match', 'not match'])
def test_can_allocate_at_various_product_id(coil_product_id, line_product_id, result):
    coil = Coil('Бухта-002', coil_product_id, 120, 5, 1)
    line = OrderLine('Заказ-002', line_product_id, 50)

    assert coil.can_allocate(line) is result


def test_allocation_is_idempotent():
    coil = Coil('Бухта-003', 'АВВГ_3х1,5', 140, 5, 1)
    line = OrderLine('Заказ-003', 'АВВГ_3х1,5', 50)
    coil.allocate(line)
    coil.allocate(line)

    assert coil.available_quantity == 90


def test_deallocate_allocated_line():
    coil = Coil('Бухта-004', 'АВВГ_3х1,5', 110, 5, 1)
    line = OrderLine('Заказ-004', 'АВВГ_3х1,5', 60)

    coil.allocate(line)
    previous_quantity = coil.available_quantity
    coil.deallocate(line)
    current_quantity = coil.available_quantity

    assert previous_quantity == 50 and current_quantity == 110


def test_deallocate_not_allocated_line():
    coil = Coil('Бухта-004', 'АВВГ_3х1,5', 110, 5, 1)
    line = OrderLine('Заказ-004', 'АВВГ_3х1,5', 60)

    coil.deallocate(line)
    current_quantity = coil.available_quantity

    assert current_quantity == 110
