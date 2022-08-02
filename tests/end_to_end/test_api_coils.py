import json

import pytest
from rest_framework.test import APIClient

from allocation.domain import domain_logic
from allocation.exceptions import exceptions
from allocation.services import unit_of_work


@pytest.mark.django_db(transaction=True)
def test_api_add_a_coil():
    client = APIClient()
    # Создание бухты
    coil_data = {"reference": 'Бухта-0010', "product_id": "АВВГ_2х2,5",
                 "quantity": 150, "recommended_balance": 10, "acceptable_loss": 2}

    # Добавление бухты в базу данных с помощью POST запроса
    response = client.post('/v1/coils', data=coil_data, format='json')
    output_data = json.loads(response.data)

    assert response.status_code == 201
    assert output_data['message'] == 'Created'


@pytest.mark.django_db(transaction=True)
def test_api_add_a_coil_is_idempotent():
    client = APIClient()
    # Создание бухт
    # Бухты имеют одинаковые значения идентификатора reference
    coil_data_1 = {"reference": 'Бухта-015', "product_id": "АВВГ_2х2,5",
                   "quantity": 150, "recommended_balance": 10, "acceptable_loss": 2}
    coil_data_2 = {"reference": 'Бухта-015', "product_id": "АВВГ_3х1,5",
                   "quantity": 200, "recommended_balance": 12, "acceptable_loss": 1}

    # Добавление бухт в базу данных с помощью POST запросов
    client.post('/v1/coils', data=coil_data_1, format='json')
    response = client.post('/v1/coils', data=coil_data_2, format='json')
    output_data = json.loads(response.data)

    assert response.status_code == 409
    # Добавление бухты с уже существующим reference вызовет исключение DBCoilRecordAlreadyExist
    assert output_data['message'] == exceptions.DBCoilRecordAlreadyExist(coil_data_2["reference"]).message


@pytest.mark.django_db(transaction=True)
def test_api_add_a_coil_raise_validation_error():
    client = APIClient()
    # Создание бухты
    # reference имеет неверное значение, quantity и recommended_balance имеют отрицательные значения
    # Итого три несоответствия CoilBaseModel
    coil_data = {"reference": 'Бухт-020', "product_id": "АВВГ_2х2,5",
                 "quantity": -70, "recommended_balance": -10, "acceptable_loss": 2}

    # Добавление бухты в базу данных с помощью POST запроса
    response = client.post('/v1/coils', data=coil_data, format='json')
    output_data = json.loads(response.data)

    assert response.status_code == 400
    # Бухта не соответствует CoilBaseModel, что вызовет ошибку ValidationError
    assert '3 validation errors for CoilBaseModel' in output_data['message']


@pytest.mark.django_db(transaction=True)
def test_api_get_a_coil():
    client = APIClient()
    # Добавление бухты в базу данных с помощью POST запроса
    coil_data = {"reference": 'Бухта-021', "product_id": "АВВГ_2х2,5",
                 "quantity": 220, "recommended_balance": 12, "acceptable_loss": 3}
    client.post('/v1/coils', data=coil_data, format='json')
    # Добавление товарной позиции в базу данных и дальнейшее размещение с помощью POST запросов
    line_data = {"order_id": 'Заказ-017', "line_item": "Позиция-001",
                 "product_id": 'АВВГ_2х2,5', "quantity": 40}
    client.post('/v1/orderlines', data=line_data, format='json')
    client.post('/v1/allocate', data=line_data, format='json')

    # Получение бухты с помощью GET запроса
    response = client.get(f"/v1/coils/{coil_data['reference']}")
    output_coil = json.loads(response.data)
    # Получение множества из кортежей (order_id, line_item) размещенных товарных позиций
    # для полученного output_coil
    allocated_lines_order_id_and_line_item = \
        {(json.loads(line)['order_id'], json.loads(line)['line_item']) for line in output_coil['allocations']}

    assert response.status_code == 200
    assert output_coil['reference'] == 'Бухта-021'
    assert output_coil['quantity'] == 220
    assert allocated_lines_order_id_and_line_item == {(line_data['order_id'], line_data['line_item'])}


@pytest.mark.django_db(transaction=True)
def test_api_get_a_coil_raise_not_exist_exception():
    client = APIClient()
    # Добавление бухты в базу данных с помощью POST запроса
    coil_data = {"reference": "Бухта-023", "product_id": "АВВГ_2х2,5",
                 "quantity": 170, "recommended_balance": 12, "acceptable_loss": 3}
    client.post('/v1/coils', data=coil_data, format='json')
    # wrong_reference - это reference несуществующей в базе данных бухты
    wrong_reference = 'Бухта-005'

    # Получение несуществующей бухты с помощью GET запроса
    response = client.get(f"/v1/coils/{wrong_reference}")
    output_data = json.loads(response.data)

    assert response.status_code == 404
    # Получение бухты по несуществующему route вызовет исключение DBCoilRecordDoesNotExist
    assert output_data['message'] == exceptions.DBCoilRecordDoesNotExist(wrong_reference).message


@pytest.mark.django_db(transaction=True)
def test_api_get_a_coil_raise_validation_error():
    client = APIClient()
    # Добавление бухты в базу данных с помощью UnitOfWork
    # quantity и recommended_balance имеют отрицательные значения
    # Итого два несоответствия CoilBaseModel
    uow = unit_of_work.DjangoUnitOfWork()
    with uow:
        coil = domain_logic.Coil(reference='Бухта-025', product_id='АВВГ_2х2,5', quantity=-150,
                                 recommended_balance=-10, acceptable_loss=2)
        uow.coil_repo.add(coil)
        uow.commit()

    # Получение бухты с помощью GET запроса
    response = client.get(f"/v1/coils/{coil.reference}")
    output_data = json.loads(response.data)

    assert response.status_code == 500
    # Бухта не соответствует CoilBaseModel, что вызовет ошибку ValidationError
    assert '2 validation errors for CoilBaseModel' in output_data['message']


@pytest.mark.django_db(transaction=True)
def test_api_update_a_coil(three_coils_and_lines):
    client = APIClient()
    # Добавление бухты в базу данных с помощью POST запроса
    coil_data_1 = {"reference": "Бухта-031", "product_id": "АВВГ_2х6",
                   "quantity": 85, "recommended_balance": 10, "acceptable_loss": 3}
    client.post('/v1/coils', data=coil_data_1, format='json')
    # Добавление товарных позиций в базу данных и дальнейшее размещение с помощью POST запросов
    for line_data in three_coils_and_lines['three_lines']:
        client.post('/v1/orderlines', data=line_data, format='json')
        client.post('/v1/allocate', data=line_data, format='json')

    # Обновление бухты с уменьшением quantity с помощью PUT запроса
    coil_data_2 = {"reference": "Бухта-031", "product_id": "АВВГ_2х6",
                   "quantity": 60, "recommended_balance": 10, "acceptable_loss": 3}
    response = client.put(f"/v1/coils/{coil_data_1['reference']}", data=coil_data_2, format='json')
    output_data = json.loads(response.data)
    # Получение множества из кортежей (order_id, line_item) неразмещенных товарных позиций
    deallocated_lines_order_id_and_line_item = \
        {(json.loads(line)['order_id'], json.loads(line)['line_item']) for line in output_data}
    # Получение обновленной бухты с помощью GET запроса
    response_2 = client.get(f"/v1/coils/{coil_data_1['reference']}")
    output_coil = json.loads(response_2.data)
    # Получение множества из кортежей (order_id, line_item) размещенных товарных позиций
    # для полученного output_coil
    allocated_lines_order_id_and_line_item = \
        {(json.loads(line)['order_id'], json.loads(line)['line_item']) for line in output_coil['allocations']}

    assert response.status_code == 200
    # Обновление бухты приведет к тому, что товарная позиция ("Заказ-031", "Позиция-005")
    # перестанет быть размещенной
    assert deallocated_lines_order_id_and_line_item == {("Заказ-031", "Позиция-005")}
    assert allocated_lines_order_id_and_line_item == {("Заказ-032", "Позиция-004"),
                                                      ("Заказ-033", "Позиция-002")}


@pytest.mark.django_db(transaction=True)
def test_api_update_a_coil_raise_validation_error():
    client = APIClient()
    # Создание бухты
    # reference имеет неверное значение, quantity и acceptable_loss имеют отрицательные значения
    # Итого три несоответствия CoilBaseModel
    coil_data = {"reference": "Бу[та-035", "product_id": "АВВГ_2х2,5",
                 "quantity": -70, "recommended_balance": 10, "acceptable_loss": -2}

    # Обновление бухты в базе данных с помощью PUT запроса
    response = client.put(f"/v1/coils/{coil_data['reference']}", data=coil_data, format='json')
    output_data = json.loads(response.data)

    assert response.status_code == 400
    # Бухта не соответствует CoilBaseModel, что вызовет ошибку ValidationError
    assert '3 validation errors for CoilBaseModel' in output_data['message']


@pytest.mark.django_db(transaction=True)
def test_api_update_a_coil_raise_not_exist_exception():
    client = APIClient()
    # Добавление бухты в базу данных с помощью POST запроса
    coil_data_1 = {"reference": "Бухта-037", "product_id": "АВВГ_2х2,5",
                   "quantity": 120, "recommended_balance": 15, "acceptable_loss": 3}
    client.post('/v1/coils', data=coil_data_1, format='json')
    # wrong_reference - это reference несуществующей в базе данных бухты
    wrong_reference = "Бухта-038"

    # Обновление несуществующей бухты в базе данных с помощью PUT запроса
    coil_data_2 = {"reference": "Бухта-037", "product_id": "АВВГ_2х2,5",
                   "quantity": 150, "recommended_balance": 20, "acceptable_loss": 3}
    response = client.put(f"/v1/coils/{wrong_reference}", data=coil_data_2, format='json')
    output_data = json.loads(response.data)

    assert response.status_code == 404
    # Обновление бухты по несуществующему route вызовет исключение DBCoilRecordDoesNotExist
    assert output_data['message'] == exceptions.DBCoilRecordDoesNotExist(wrong_reference).message


@pytest.mark.django_db(transaction=True)
def test_api_delete_a_coil(three_coils_and_lines):
    client = APIClient()
    # Добавление бухты в базу данных с помощью POST запроса
    coil_data = {"reference": "Бухта-038", "product_id": "АВВГ_2х6",
                 "quantity": 85, "recommended_balance": 10, "acceptable_loss": 3}
    client.post('/v1/coils', data=coil_data, format='json')
    # Добавление товарных позиций в базу данных и дальнейшее размещение с помощью POST запросов
    for line_data in three_coils_and_lines['three_lines']:
        client.post('/v1/orderlines', data=line_data, format='json')
        client.post('/v1/allocate', data=line_data, format='json')

    # Удаление бухты с помощью DELETE запроса
    response = client.delete(f"/v1/coils/{coil_data['reference']}")
    output_data = json.loads(response.data)
    # Получение множества из кортежей (order_id, line_item) для товарных позиций,
    # которые перестали быть размещены после удаления бухты
    deallocated_lines_order_id_and_line_item = \
        {(json.loads(line)['order_id'], json.loads(line)['line_item']) for line in output_data}

    assert response.status_code == 200
    # Удаление бухты вернет множество переставших быть размещенными товарных позиций
    assert deallocated_lines_order_id_and_line_item == \
           {("Заказ-031", "Позиция-005"), ("Заказ-032", "Позиция-004"), ("Заказ-033", "Позиция-002")}


@pytest.mark.django_db(transaction=True)
def test_api_delete_a_coil_raise_not_exist_exception():
    client = APIClient()
    # Добавление бухты в базу данных с помощью POST запроса
    coil_data = {"reference": 'Бухта-039', "product_id": "АВВГ_2х2,5",
                 "quantity": 200, "recommended_balance": 10, "acceptable_loss": 2}
    client.post('/v1/coils', data=coil_data, format='json')
    # wrong_reference - это reference несуществующей в базе данных бухты
    wrong_reference = 'Бухта-002'

    # Удаление несуществующей бухты с помощью DELETE запроса
    response = client.delete(f"/v1/coils/{wrong_reference}")
    output_data = json.loads(response.data)

    assert response.status_code == 404
    # Удаление бухты по несуществующему route вызовет исключение DBCoilRecordDoesNotExist
    assert output_data['message'] == exceptions.DBCoilRecordDoesNotExist(wrong_reference).message
