import pytest

from allocation.domain.domain_logic import Coil, OrderLine, allocate_to_list_of_coils, OutOfStock


def test_prefers_smaller_coil():
    smaller_coil = Coil('Бухта-005', 'АВВГ_2х6', 95, 5, 1)
    medium_coil = Coil('Бухта-005', 'АВВГ_2х6', 96, 5, 1)
    bigger_coil = Coil('Бухта-005', 'АВВГ_2х6', 97, 5, 1)
    line = OrderLine('Заказ-010', 'АВВГ_2х6', 15)

    allocate_to_list_of_coils(
        line, [bigger_coil, smaller_coil, medium_coil]
    )

    assert smaller_coil.available_quantity == 80
    assert medium_coil.available_quantity == 96
    assert bigger_coil.available_quantity == 97


def test_prefers_coil_with_suitable_balance():
    right_coil = Coil('Бухта-006', 'АВВГ_2х6', 20, 4, 1)
    wrong_coil_1 = Coil('Бухта-006', 'АВВГ_2х6', 20, 6, 1)
    wrong_coil_2 = Coil('Бухта-006', 'АВВГ_2х6', 20, 8, 1)
    line = OrderLine('Заказ-011', 'АВВГ_2х6', 15)

    allocate_to_list_of_coils(
        line, [wrong_coil_1, right_coil, wrong_coil_2]
    )

    assert right_coil.available_quantity == 5
    assert wrong_coil_1.available_quantity == 20
    assert wrong_coil_2.available_quantity == 20


def test_prefers_coil_with_suitable_loss():
    right_coil = Coil('Бухта-007', 'АВВГ_2х6', 20, 8, 4)
    wrong_coil_1 = Coil('Бухта-007', 'АВВГ_2х6', 20, 8, 2)
    wrong_coil_2 = Coil('Бухта-007', 'АВВГ_2х6', 20, 8, 1)
    line = OrderLine('Заказ-011', 'АВВГ_2х6', 17)

    allocate_to_list_of_coils(
        line, [wrong_coil_1, right_coil, wrong_coil_2]
    )

    assert right_coil.available_quantity == 3
    assert wrong_coil_1.available_quantity == 20
    assert wrong_coil_2.available_quantity == 20


def test_returns_allocated_coil_reference():
    smaller_coil = Coil('Бухта-008', 'АВВГ_2х6', 95, 10, 3)
    medium_coil = Coil('Бухта-008', 'АВВГ_2х6', 105, 7, 2)
    bigger_coil = Coil('Бухта-008', 'АВВГ_2х6', 120, 3, 1)
    line = OrderLine('Заказ-012', 'АВВГ_2х6', 30)

    allocation = allocate_to_list_of_coils(
        line, [bigger_coil, smaller_coil, medium_coil]
    )

    assert smaller_coil.reference == allocation


def test_raise_out_of_stock_exception_if_cannot_allocate():
    coil = Coil('Бухта-009', 'АВВГ_2х6', 10, 5, 1)
    line = OrderLine('Заказ-014', 'АВВГ_2х6', 11)

    with pytest.raises(OutOfStock, match='АВВГ_2х6'):
        allocate_to_list_of_coils(line, [coil])
