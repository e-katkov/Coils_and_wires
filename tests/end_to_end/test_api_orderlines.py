import json

import pytest

from rest_framework.test import APIClient

from allocation.domain import domain_logic
from allocation.services import unit_of_work


@pytest.mark.django_db(transaction=True)
def test_api_add_a_line():
    client = APIClient()
    # Создание товарной позиции
    line_data = {"order_id": 'Заказ-020', "line_item": "Позиция-001",
                 "product_id": 'АВВГ_2х6', "quantity": 25}

    # Добавление товарной позиции в базу данных с помощью POST запроса
    response = client.post('/v1/orderlines', data=line_data, format='json')
    output_data = json.loads(response.data)

    assert output_data['message'] == 'Created'
    assert response.status_code == 201


@pytest.mark.django_db(transaction=True)
def test_api_add_a_line_is_idempotent():
    client = APIClient()
    # Создание товарных позиций
    # Товарные позиции имеют одинаковые значения идентификаторов: order_id и line_item
    line_data_1 = {"order_id": 'Заказ-021', "line_item": "Позиция-001",
                   "product_id": 'АВВГ_2х6', "quantity": 20}
    line_data_2 = {"order_id": 'Заказ-021', "line_item": "Позиция-001",
                   "product_id": 'АВВГ_3х2,5', "quantity": 45}

    # Добавление товарных позиций в базу данных с помощью POST запросов
    client.post('/v1/orderlines', data=line_data_1, format='json')
    response = client.post('/v1/orderlines', data=line_data_2, format='json')
    output_data = json.loads(response.data)

    # Добавление товарной позиции с уже существующими order_id и line_item
    # вызовет исключение DBOrderLineRecordAlreadyExist
    assert output_data['message'] == \
           f'Запись с order_id={line_data_2["order_id"]} и line_item={line_data_2["line_item"]}' \
           f' уже существует в таблице OrderLine базы данных'
    assert response.status_code == 409


@pytest.mark.django_db(transaction=True)
def test_api_add_a_line_raise_validation_error():
    client = APIClient()
    # Создание товарной позиции
    # order_id имеет неверное значение, quantity имеет отрицательное значение
    # Итого два несоответствия OrderLineBaseModel
    line_data = {"order_id": 'Закз-025', "line_item": "Позиция-001",
                 "product_id": 'АВВГ_2х6', "quantity": -15}

    # Добавление товарной позиции в базу данных с помощью POST запроса
    response = client.post('/v1/orderlines', data=line_data, format='json')
    output_data = json.loads(response.data)

    # Товарная позиция не соответствует OrderLineBaseModel, что вызовет ошибку ValidationError
    assert '2 validation errors for OrderLineBaseModel' in output_data['message']
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_api_get_a_line():
    client = APIClient()
    # Добавление товарных позиций в базу данных с помощью POST запросов
    line_data_1 = {"order_id": 'Заказ-007', "line_item": "Позиция-001",
                   "product_id": 'АВВГ_2х6', "quantity": 20}
    line_data_2 = {"order_id": 'Заказ-007', "line_item": "Позиция-002",
                   "product_id": 'АВВГ_2х2,5', "quantity": 15}
    client.post('/v1/orderlines', data=line_data_1, format='json')
    client.post('/v1/orderlines', data=line_data_2, format='json')

    # Получение товарной позиции №2 с помощью GET запроса
    response = client.get(f"/v1/orderlines/{line_data_2['order_id']}/{line_data_2['line_item']}")
    output_data = json.loads(response.data)

    assert output_data['line_item'] == 'Позиция-002'
    assert output_data['quantity'] == 15
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_api_get_a_line_raise_not_exist_exception():
    client = APIClient()
    # Добавление товарной позиции в базу данных с помощью POST запроса
    line_data = {"order_id": 'Заказ-009', "line_item": "Позиция-005",
                 "product_id": 'АВВГ_2х6', "quantity": 12}
    client.post('/v1/orderlines', data=line_data, format='json')
    # wrong_line_item - это line_item несуществующей в базе данных товарной позиции
    wrong_line_item = 'Позиция-002'

    # Получение несуществующей товарной позиции с помощью GET запроса
    response = client.get(f"/v1/orderlines/{line_data['order_id']}/{wrong_line_item}")
    output_data = json.loads(response.data)

    # Получение товарной позиции по несуществующему route вызовет исключение DBOrderLineRecordDoesNotExist
    assert output_data['message'] == \
           f"Запись с order_id={line_data['order_id']} и line_item={wrong_line_item}" \
           f" отсутствует в таблице OrderLine базы данных"
    assert response.status_code == 404


@pytest.mark.django_db(transaction=True)
def test_api_get_a_line_raise_validation_error():
    client = APIClient()
    # Добавление товарной позиции в базу данных с помощью UnitOfWork
    # quantity имеет неверное значение
    # Итого одно несоответствие OrderLineBaseModel
    uow = unit_of_work.DjangoOrderLineUnitOfWork()
    with uow:
        line = domain_logic.OrderLine(order_id="Заказ-011", line_item="Позиция-001", product_id="АВВГ_2х6",
                                      quantity=-12)
        uow.line_repo.add(line)
        uow.commit()

    # Получение товарной позиции с помощью GET запроса
    response = client.get(f"/v1/orderlines/{line.order_id}/{line.line_item}")
    output_data = json.loads(response.data)

    # Товарная позиция не соответствует OrderLineBaseModel, что вызовет ошибку ValidationError
    assert '1 validation error for OrderLineBaseModel' in output_data['message']
    assert response.status_code == 500


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('line_2_quantity, coil_reference, coil_quantity',
                         [(30, "Бухта-031", 95), (90, "Бухта-032", 105)],
                         ids=["smaller_coil", "medium_coil"])
def test_api_update_a_line_returns_real_coil(three_coils_and_lines, line_2_quantity, coil_reference,
                                             coil_quantity):
    client = APIClient()
    # Добавление бухт в базу данных с помощью POST запросов
    for coil_data in three_coils_and_lines['three_coils']:
        client.post('/v1/coils', data=coil_data, format='json')
    # Добавление товарной позиции в базу данных и дальнейшее размещение с помощью POST запросов
    line_data_1 = {"order_id": "Заказ-015", "line_item": "Позиция-001",
                   "product_id": "АВВГ_2х6", "quantity": 40}
    client.post('/v1/orderlines', data=line_data_1, format='json')
    client.post('/v1/allocate', data=line_data_1, format='json')

    # Обновление товарной позиции с уменьшением (1), увеличением (2) quantity с помощью PUT запроса
    line_data_2 = {"order_id": "Заказ-015", "line_item": "Позиция-001",
                   "product_id": "АВВГ_2х6", "quantity": line_2_quantity}
    response = client.put(f"/v1/orderlines/{line_data_1['order_id']}/{line_data_1['line_item']}",
                          data=line_data_2, format='json')
    output_data = json.loads(response.data)

    # Товарная позиция будет размещена в smaller_coil (1), medium_coil (2)
    assert output_data['reference'] == coil_reference
    assert output_data['quantity'] == coil_quantity
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_api_update_a_line_returns_fake_coil(three_coils_and_lines):
    client = APIClient()
    # Добавление бухт в базу данных с помощью POST запросов
    for coil_data in three_coils_and_lines['three_coils']:
        client.post('/v1/coils', data=coil_data, format='json')
    # Добавление товарной позиции в базу данных с помощью POST запроса
    # Размещение не выполняется
    line_data_1 = {"order_id": "Заказ-015", "line_item": "Позиция-001",
                   "product_id": "АВВГ_2х6", "quantity": 40}
    client.post('/v1/orderlines', data=line_data_1, format='json')

    # Обновление товарной позиции с уменьшением quantity с помощью PUT запроса
    line_data_2 = {"order_id": "Заказ-015", "line_item": "Позиция-001",
                   "product_id": "АВВГ_2х6", "quantity": 25}
    response = client.put(f"/v1/orderlines/{line_data_1['order_id']}/{line_data_1['line_item']}",
                          data=line_data_2, format='json')
    output_data = json.loads(response.data)

    # Размещение товарной позиции не выполнялось, что приведет к возврату "поддельной" бухты
    assert output_data['reference'] == 'fake'
    assert output_data['quantity'] == 1
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_api_update_a_line_raise_input_validation_error():
    client = APIClient()
    # Добавление товарной позиции в базу данных с помощью POST запроса
    line_data_1 = {"order_id": 'Заказ-017', "line_item": "Позиция-002",
                   "product_id": 'АВВГ_2х2,5', "quantity": 30}
    client.post('/v1/orderlines', data=line_data_1, format='json')

    # Обновление товарной позиции в базе данных с помощью PUT запроса
    # line_item имеет неверное значение, quantity имеет отрицательное значение.
    # Итого два несоответствия OrderLineBaseModel
    line_data_2 = {"order_id": 'Заказ-017', "line_item": "Пазиция-004",
                   "product_id": 'АВВГ_2х2,5', "quantity": -24}
    response = client.put(f"/v1/orderlines/{line_data_1['order_id']}/{line_data_1['line_item']}",
                          data=line_data_2, format='json')
    output_data = json.loads(response.data)

    # Товарная позиция не соответствует OrderLineBaseModel, что вызовет ошибку ValidationError
    assert '2 validation errors for OrderLineBaseModel' in output_data['message']
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_api_update_a_line_raise_not_exist_exception():
    client = APIClient()
    # Добавление товарной позиции в базу данных с помощью POST запроса
    line_data_1 = {"order_id": 'Заказ-018', "line_item": "Позиция-003",
                   "product_id": 'АВВГ_2х2,5', "quantity": 15}
    client.post('/v1/orderlines', data=line_data_1, format='json')
    # wrong_line_item - это line_item несуществующей в базе данных товарной позиции
    wrong_line_item = "Позиция-004"

    # Обновление несуществующей товарной позиции в базе данных с помощью PUT запроса
    line_data_2 = {"order_id": 'Заказ-018', "line_item": "Позиция-003",
                   "product_id": 'АВВГ_2х2,5', "quantity": 18}
    response = client.put(f"/v1/orderlines/{line_data_1['order_id']}/{wrong_line_item}",
                          data=line_data_2, format='json')
    output_data = json.loads(response.data)

    # Обновление товарной позиции по несуществующему route вызовет исключение DBOrderLineRecordDoesNotExist
    assert output_data['message'] == \
           f"Запись с order_id={line_data_1['order_id']} и line_item={wrong_line_item}" \
           f" отсутствует в таблице OrderLine базы данных"
    assert response.status_code == 404


@pytest.mark.django_db(transaction=True)
def test_api_update_a_line_raise_output_validation_error():
    client = APIClient()
    # Добавление бухты в базу данных с помощью UnitOfWork
    # recommended_balance имеет неверное значение
    # Итого одно несоответствие CoilBaseModel
    uow = unit_of_work.DjangoCoilUnitOfWork()
    with uow:
        coil = domain_logic.Coil(reference='Бухта-025', product_id='АВВГ_2х2,5', quantity=200,
                                 recommended_balance=-10, acceptable_loss=3)
        uow.coil_repo.add(coil)
        uow.commit()
    # Добавление товарной позиции в базу данных и дальнейшее размещение с помощью POST запросов
    line_data_1 = {"order_id": "Заказ-019", "line_item": "Позиция-001",
                   "product_id": "АВВГ_2х2,5", "quantity": 40}
    client.post('/v1/orderlines', data=line_data_1, format='json')
    client.post('/v1/allocate', data=line_data_1, format='json')

    # Обновление товарной позиции в базе данных с помощью PUT запроса
    line_data_2 = {"order_id": "Заказ-019", "line_item": "Позиция-001",
                   "product_id": "АВВГ_2х2,5", "quantity": 45}
    response = client.put(f"/v1/orderlines/{line_data_1['order_id']}/{line_data_1['line_item']}",
                          data=line_data_2, format='json')
    output_data = json.loads(response.data)

    # Обновление товарной позиции вернет allocation_coil, в который она была размещена
    # allocation_coil не соответствует CoilBaseModel, что вызовет ошибку ValidationError
    assert '1 validation error for CoilBaseModel' in output_data['message']
    assert response.status_code == 500


@pytest.mark.django_db(transaction=True)
def test_api_delete_a_line_returns_real_coil(three_coils_and_lines):
    client = APIClient()
    # Добавление товарных позиций в базу данных с помощью POST запросов
    for coil_data in three_coils_and_lines['three_coils']:
        client.post('/v1/coils', data=coil_data, format='json')
    # Добавление товарной позиции в базу данных и дальнейшее размещение с помощью POST запросов
    # Размещение будет выполнено в smaller_coil
    line_data = {"order_id": "Заказ-022", "line_item": "Позиция-004",
                 "product_id": "АВВГ_2х6", "quantity": 50}
    client.post('/v1/orderlines', data=line_data, format='json')
    client.post('/v1/allocate', data=line_data, format='json')

    # Удаление товарной позиции с помощью DELETE запроса
    response = client.delete(f"/v1/orderlines/{line_data['order_id']}/{line_data['line_item']}")
    output_data = json.loads(response.data)

    # Удаление товарной позиции вернет allocation_coil, в который она была размещена, т.е. smaller_coil
    assert output_data['reference'] == "Бухта-031"
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_api_delete_a_line_returns_fake_coil(three_coils_and_lines):
    client = APIClient()
    # Добавление товарной позиции в базу данных с помощью POST запроса
    # Размещение не выполняется
    line_data = {"order_id": "Заказ-023", "line_item": "Позиция-004",
                 "product_id": "АВВГ_2х2,5", "quantity": 12}
    client.post('/v1/orderlines', data=line_data, format='json')

    # Удаление товарной позиции с помощью DELETE запроса
    response = client.delete(f"/v1/orderlines/{line_data['order_id']}/{line_data['line_item']}")
    output_data = json.loads(response.data)

    # Удаление товарной позиции вернет allocation_coil, в который она была размещена
    # Размещение товарной позиции не выполнялось, что приведет к возврату "поддельной" бухты
    assert output_data['reference'] == 'fake'
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_api_delete_a_line_raise_not_exist_exception():
    client = APIClient()
    # Добавление товарной позиции в базу данных с помощью POST запроса
    line_data = {"order_id": "Заказ-024", "line_item": "Позиция-003",
                 "product_id": "АВВГ_2х2,5", "quantity": 14}
    client.post('/v1/orderlines', data=line_data, format='json')
    # wrong_order_id - это order_id несуществующей в базе данных товарной позиции
    wrong_order_id = "Позиция-002"

    # Удаление несуществующей товарной позиции с помощью DELETE запроса
    response = client.delete(f"/v1/orderlines/{wrong_order_id}/{line_data['line_item']}")
    output_data = json.loads(response.data)

    # Удаление товарной позиции по несуществующему route вызовет исключение DBOrderLineRecordDoesNotExist
    assert output_data['message'] == \
           f"Запись с order_id={wrong_order_id} и line_item={line_data['line_item']}" \
           f" отсутствует в таблице OrderLine базы данных"
    assert response.status_code == 404


@pytest.mark.django_db(transaction=True)
def test_api_delete_a_line_raise_validation_error():
    client = APIClient()
    # Добавление бухты в базу данных с помощью UnitOfWork
    # acceptable_loss имеет неверное значение
    # Итого одно несоответствие CoilBaseModel
    uow = unit_of_work.DjangoCoilUnitOfWork()
    with uow:
        coil = domain_logic.Coil(reference='Бухта-027', product_id='АВВГ_2х2,5', quantity=150,
                                 recommended_balance=12, acceptable_loss=-4)
        uow.coil_repo.add(coil)
        uow.commit()
    # Добавление товарной позиции в базу данных и дальнейшее размещение с помощью POST запросов
    line_data = {"order_id": "Заказ-025", "line_item": "Позиция-004",
                 "product_id": "АВВГ_2х2,5", "quantity": 15}
    client.post('/v1/orderlines', data=line_data, format='json')
    client.post('/v1/allocate', data=line_data, format='json')

    # Удаление товарной позиции с помощью DELETE запроса
    response = client.delete(f"/v1/orderlines/{line_data['order_id']}/{line_data['line_item']}")
    output_data = json.loads(response.data)

    # Удаление товарной позиции вернет allocation_coil, в который она была размещена
    # allocation_coil не соответствует CoilBaseModel, что вызовет ошибку ValidationError
    assert '1 validation error for CoilBaseModel' in output_data['message']
    assert response.status_code == 500
