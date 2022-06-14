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


@pytest.fixture
def three_coils_and_lines():
    smaller_coil = {"reference": "Бухта-031", "product_id": "АВВГ_2х6",
                    "quantity": 95, "recommended_balance": 10, "acceptable_loss": 3}
    medium_coil = {"reference": "Бухта-032", "product_id": "АВВГ_2х6",
                   "quantity": 105, "recommended_balance": 7, "acceptable_loss": 3}
    bigger_coil = {"reference": "Бухта-033", "product_id": "АВВГ_2х6",
                   "quantity": 120, "recommended_balance": 15, "acceptable_loss": 3}
    line_1 = {"order_id": "Заказ-031", "line_item": "Позиция-005",
              "product_id": "АВВГ_2х6", "quantity": 35}
    line_2 = {"order_id": "Заказ-032", "line_item": "Позиция-004",
              "product_id": "АВВГ_2х6", "quantity": 30}
    line_3 = {"order_id": "Заказ-033", "line_item": "Позиция-002",
              "product_id": "АВВГ_2х6", "quantity": 10}
    return {'three_coils': [medium_coil, smaller_coil, bigger_coil],
            'three_lines': [line_1, line_3, line_2]}
