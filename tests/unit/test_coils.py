from allocation.domain.domain_logic import Coil, OrderLine


def test_allocating_reduced_alailable_quantity():
    coil = Coil('бухта_001', 'АВВГ_2х2,5', 150)
    line = OrderLine('Заказ-001', 'АВВГ_2х2,5', 40)

    coil.allocate(line)

    assert coil.alailable_quantity == 110

