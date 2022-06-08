import pytest

from allocation.domain.domain_logic import OrderLine


@pytest.fixture
def dict_of_orderlines():
    set_0 = {
        OrderLine('Заказ-004', 'Позиция-001', 'АВВГ_3х1,5', 6),
        OrderLine('Заказ-005', 'Позиция-002', 'АВВГ_3х1,5', 7),
        OrderLine('Заказ-006', 'Позиция-004', 'АВВГ_3х1,5', 10),
        OrderLine('Заказ-008', 'Позиция-001', 'АВВГ_3х1,5', 11),
    }
    set_1 = {OrderLine('Заказ-009', 'Позиция-001', 'АВВГ_3х1,5', 11),}
    set_2 = {OrderLine('Заказ-010', 'Позиция-001', 'АВВГ_3х1,5', 12),}
    return {'set_0': set_0, 'set_1': set_1, 'set_2': set_2}
