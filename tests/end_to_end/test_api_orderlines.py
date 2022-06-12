import json
import pytest

from rest_framework.test import APIClient

from allocation.domain import domain_logic
from allocation.services import unit_of_work


@pytest.mark.django_db(transaction=True)
def test_add_a_line():
    line_data = {"order_id": 'Заказ-020', "line_item": "Позиция-001",
                 "product_id": 'АВВГ_2х6', "quantity": 25}
    client = APIClient()
    input_line_data = json.dumps(line_data, ensure_ascii=False)

    response = client.post('/v1/orderlines', data=input_line_data, format='json')
    output_data = json.loads(response.data)

    assert output_data['message'] == 'OK'
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_add_a_line_is_idempotent():
    # line_data имеют заведомо одинаковые значения order_id и line_item
    line_data_1 = {"order_id": 'Заказ-021', "line_item": "Позиция-001",
                   "product_id": 'АВВГ_2х6', "quantity": 20}
    line_data_2 = {"order_id": 'Заказ-021', "line_item": "Позиция-001",
                   "product_id": 'АВВГ_3х2,5', "quantity": 45}
    client = APIClient()
    input_line_data_1 = json.dumps(line_data_1, ensure_ascii=False)
    input_line_data_2 = json.dumps(line_data_2, ensure_ascii=False)

    client.post('/v1/orderlines', data=input_line_data_1, format='json')
    response = client.post('/v1/orderlines', data=input_line_data_2, format='json')
    output_data = json.loads(response.data)

    assert output_data['message'] == \
           f'Запись с order_id={line_data_2["order_id"]} и line_item={line_data_2["line_item"]}' \
           f' уже существует в таблице OrderLine базы данных'
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_add_a_line_raise_validation_error():
    # order_id имеет неверное имя, quantity имеет отрицательные значение.
    # Итого два несоответствия OrderLineBaseModel
    line_data = {"order_id": 'Закз-025', "line_item": "Позиция-001",
                 "product_id": 'АВВГ_2х6', "quantity": -15}
    client = APIClient()
    input_line_data = json.dumps(line_data, ensure_ascii=False)

    response = client.post('/v1/orderlines', data=input_line_data, format='json')
    output_data = json.loads(response.data)

    assert '2 validation errors for OrderLineBaseModel' in output_data['message']
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_get_a_line():
    line_data_1 = {"order_id": 'Заказ-007', "line_item": "Позиция-001",
                   "product_id": 'АВВГ_2х6', "quantity": 20}
    line_data_2 = {"order_id": 'Заказ-007', "line_item": "Позиция-002",
                   "product_id": 'АВВГ_2х2,5', "quantity": 15}
    client = APIClient()
    input_line_data_1 = json.dumps(line_data_1, ensure_ascii=False)
    input_line_data_2 = json.dumps(line_data_2, ensure_ascii=False)
    client.post('/v1/orderlines', data=input_line_data_1, format='json')
    client.post('/v1/orderlines', data=input_line_data_2, format='json')

    response = client.get("/v1/orderlines/Заказ-007/Позиция-002")
    output_data = json.loads(response.data)

    assert output_data['line_item'] == 'Позиция-002'
    assert output_data['quantity'] == 15
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_get_a_line_raise_not_exist_error():
    line_data = {"order_id": 'Заказ-009', "line_item": "Позиция-005",
                 "product_id": 'АВВГ_2х6', "quantity": 12}
    client = APIClient()
    input_line_data = json.dumps(line_data, ensure_ascii=False)
    client.post('/v1/orderlines', data=input_line_data, format='json')
    wrong_line_item = 'Позиция-002'

    response = client.get(f"/v1/orderlines/{line_data['order_id']}/{wrong_line_item}")
    output_data = json.loads(response.data)

    assert output_data['message'] == \
           f"Запись с order_id={line_data['order_id']} и line_item={wrong_line_item}" \
           f" отсутствует в таблице OrderLine базы данных"
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_get_a_line_raise_validation_error():
    # запись добавляется в базу данных с помощью UnitOfWork
    # запись имеет ошибку в quantity, т.е. одно несоответствие OrderLineBaseModel
    line_data = {"order_id": 'Заказ-011', "line_item": "Позиция-001",
                 "product_id": 'АВВГ_2х6', "quantity": -12}
    uow = unit_of_work.DjangoOrderLineUnitOfWork()
    with uow:
        coil = domain_logic.OrderLine(line_data['order_id'], line_data['line_item'],
                                      line_data['product_id'], line_data['quantity'])
        uow.line_repo.add(coil)
        uow.commit()
    client = APIClient()

    response = client.get(f"/v1/orderlines/{line_data['order_id']}/{line_data['line_item']}")
    output_data = json.loads(response.data)

    assert '1 validation error for OrderLineBaseModel' in output_data['message']
    assert response.status_code == 500
