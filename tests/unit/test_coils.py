import pytest

from allocation.domain.domain_logic import Coil, OrderLine


def test_allocating_reduced_available_quantity():
    """Размещение товарной позиции уменьшит доступное количество материала в бухте."""
    coil = Coil('Бухта-001', 'АВВГ_2х2,5', 150, 5, 1)
    line = OrderLine('Заказ-001', 'Позиция-001', 'АВВГ_2х2,5', 40)

    coil.allocate(line)

    assert coil.available_quantity == 110


@pytest.mark.parametrize('coil_quantity, line_quantity, result',
                         [(170, 20, True), (60, 110, False), (70, 70, True)],
                         ids=['170-20', '60-110', '70-70'])
def test_can_allocate_at_various_quantities(coil_quantity, line_quantity, result):
    """
    Размещение товарной позиции в бухте возможно, если количество материала в бухте
    больше или равно количеству материала в товарной позиции.
    """
    coil = Coil('Бухта-002', 'АВВГ_3х1,5', coil_quantity, 5, 1)
    line = OrderLine('Заказ-002', 'Позиция-001', 'АВВГ_3х1,5', line_quantity)

    assert coil.can_allocate(line) is result


@pytest.mark.parametrize('coil_product_id, line_item, line_product_id, result',
                         [('АВВГ_2х2,5', 'Позиция-001', 'АВВГ_2х2,5', True),
                          ('АВВГ_2х2,5', 'Позиция-002', 'АВВГ_3х1,5', False)],
                         ids=['match', 'not match'])
def test_can_allocate_at_various_product_id(coil_product_id, line_item, line_product_id, result):
    """
    Размещение товарной позиции в бухте возможно, если идентификатор материала в бухте
    совпадает с идентификатором материала в товарной позиции.
    """
    coil = Coil('Бухта-002', coil_product_id, 120, 5, 1)
    line = OrderLine('Заказ-002', line_item, line_product_id, 50)

    assert coil.can_allocate(line) is result


def test_allocation_is_idempotent():
    """Повторное размещение товарной позиции ничего не изменит в бухте."""
    coil = Coil('Бухта-003', 'АВВГ_3х1,5', 140, 5, 1)
    line = OrderLine('Заказ-003', 'Позиция-001', 'АВВГ_3х1,5', 50)
    coil.allocate(line)
    coil.allocate(line)

    assert coil.available_quantity == 90


def test_deallocate_allocated_line():
    """
    Отмена размещения товарной позиции в бухте соответственно изменит
    доступное количество материала и множество экземпляров размещенных товарных позиций в бухте.
    """
    coil = Coil('Бухта-004', 'АВВГ_3х1,5', 110, 5, 1)
    orderline = OrderLine('Заказ-004', 'Позиция-001', 'АВВГ_3х1,5', 60)
    coil.allocate(orderline)
    previous_quantity = coil.available_quantity
    previous_allocations_order_ids = {line.order_id for line in coil.allocations}

    coil.deallocate(orderline)
    current_quantity = coil.available_quantity
    current_allocations_order_ids = {line.order_id for line in coil.allocations}

    assert previous_quantity == 50
    assert current_quantity == 110
    assert previous_allocations_order_ids == {orderline.order_id}
    assert current_allocations_order_ids == set()


def test_deallocate_not_allocated_line():
    """
    Отмена размещения товарной позиции, которая ранее не была размещена,
    ничего не изменит в бухте.
    """
    coil = Coil('Бухта-004', 'АВВГ_3х1,5', 110, 5, 1)
    line = OrderLine('Заказ-004', 'Позиция-001', 'АВВГ_3х1,5', 60)

    coil.deallocate(line)
    current_quantity = coil.available_quantity

    assert current_quantity == 110


def test_coils_equivalence(not_a_coil):
    """
    При сравнении на равенство экземпляров двух классов:
    класса Coil доменной модели и класса NotACoil,
    которые имеют одинаковые атрибуты и их значения, будет возвращен False.
    """
    # Создание бухты
    coil_1 = Coil('Бухта-005', 'АВВГ_3х1,5', 90, 4, 1)
    # Создание "не бухты"
    coil_2 = not_a_coil('Бухта-005', 'АВВГ_3х1,5', 90, 4, 1)

    result = (coil_1 == coil_2)

    assert result is False


def test_coils_comparison(not_a_coil):
    """
    При сравнении экземпляров двух классов:
    класса Coil доменной модели и класса NotACoil,
    которые имеют одинаковые атрибуты, будет возвращен False.
    """
    # Создание бухты
    coil_1 = Coil('Бухта-005', 'АВВГ_3х1,5', 70, 2, 1)
    # Создание "не бухты"
    coil_2 = not_a_coil('Бухта-005', 'АВВГ_3х1,5', 90, 4, 1)

    result = (coil_1 < coil_2)

    assert result is False


def test_orderlines_equivalence(not_an_orderline):
    """
    При сравнении на равенство экземпляров двух классов:
    класса OrderLine доменной модели и класса NotAnOrderLine,
    которые имеют одинаковые атрибуты и их значения, будет возвращен False.
    """
    # Создание товарной позиции
    line_1 = OrderLine('Заказ-005', 'Позиция-002', 'АВВГ_3х1,5', 70)
    # Создание "не товарной позиции"
    line_2 = not_an_orderline('Заказ-005', 'Позиция-002', 'АВВГ_3х1,5', 70)

    result = (line_1 == line_2)

    assert result is False
