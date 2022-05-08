from allocation.domain.domain_logic import Coil, OrderLine


def test_allocating_reduced_available_quantity():
    coil = Coil('Бухта_001', 'АВВГ_2х2,5', 150)
    line = OrderLine('Заказ-001', 'АВВГ_2х2,5', 40)

    coil.allocate(line)

    assert coil.available_quantity == 110

