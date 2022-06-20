import json
import pytest

from rest_framework.test import APIClient

from allocation.domain import domain_logic
from allocation.services import unit_of_work


@pytest.mark.django_db(transaction=True)
def test_add_a_coil():
    client = APIClient()
    # Создание coil
    coil_data = {"reference": 'Бухта-0010', "product_id": "АВВГ_2х2,5",
                 "quantity": 150, "recommended_balance": 10, "acceptable_loss": 2}
    input_coil_data = json.dumps(coil_data, ensure_ascii=False)

    # Добавление coil в базу данных с помощью POST запроса
    response = client.post('/v1/coils', data=input_coil_data, format='json')
    output_data = json.loads(response.data)

    assert output_data['message'] == 'Created'
    assert response.status_code == 201


@pytest.mark.django_db(transaction=True)
def test_add_a_coil_is_idempotent():
    client = APIClient()
    # Создание coils
    # coil имеют одинаковые значения идентификатора reference
    coil_data_1 = {"reference": 'Бухта-015', "product_id": "АВВГ_2х2,5",
                   "quantity": 150, "recommended_balance": 10, "acceptable_loss": 2}
    coil_data_2 = {"reference": 'Бухта-015', "product_id": "АВВГ_3х1,5",
                   "quantity": 200, "recommended_balance": 12, "acceptable_loss": 1}
    input_coil_data_1 = json.dumps(coil_data_1, ensure_ascii=False)
    input_coil_data_2 = json.dumps(coil_data_2, ensure_ascii=False)

    # Добавление coils в базу данных с помощью POST запросов
    client.post('/v1/coils', data=input_coil_data_1, format='json')
    response = client.post('/v1/coils', data=input_coil_data_2, format='json')
    output_data = json.loads(response.data)

    # Добавление coil с уже существующим reference вызовет исключение DBCoilRecordAlreadyExist
    assert output_data['message'] == \
           f'Запись с reference={coil_data_2["reference"]} уже существует в таблице Coil базы данных'
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_add_a_coil_raise_validation_error():
    client = APIClient()
    # Создание coil
    # reference имеет неверное значение, quantity и recommended_balance имеют отрицательные значения
    # Итого три несоответствия CoilBaseModel
    coil_data = {"reference": 'Бухт-020', "product_id": "АВВГ_2х2,5",
                 "quantity": -70, "recommended_balance": -10, "acceptable_loss": 2}
    input_data = json.dumps(coil_data, ensure_ascii=False)

    # Добавление coil в базу данных с помощью POST запроса
    response = client.post('/v1/coils', data=input_data, format='json')
    output_data = json.loads(response.data)

    # coil не соответствует CoilBaseModel, что вызовет ошибку ValidationError
    assert '3 validation errors for CoilBaseModel' in output_data['message']
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_get_a_coil():
    client = APIClient()
    # Добавление coil в базу данных с помощью POST запроса
    coil_data = {"reference": 'Бухта-021', "product_id": "АВВГ_2х2,5",
                 "quantity": 220, "recommended_balance": 12, "acceptable_loss": 3}
    input_coil_data = json.dumps(coil_data, ensure_ascii=False)
    client.post('/v1/coils', data=input_coil_data, format='json')
    # Добавление orderline в базу данных и дальнейшее размещение (allocation) с помощью POST запросов
    line_data = {"order_id": 'Заказ-017', "line_item": "Позиция-001",
                 "product_id": 'АВВГ_2х2,5', "quantity": 40}
    input_line_data = json.dumps(line_data, ensure_ascii=False)
    client.post('/v1/orderlines', data=input_line_data, format='json')
    client.post('/v1/allocate', data=input_line_data, format='json')

    # Получение coil с помощью GET запроса
    response = client.get(f"/v1/coils/{coil_data['reference']}")
    output_coil = json.loads(response.data)
    # Получение множества из кортежей (order_id, line_item) размещенных orderlines для полученного output_coil
    allocated_lines_order_id_and_line_item = \
        {(json.loads(line)['order_id'], json.loads(line)['line_item']) for line in output_coil['allocations']}

    assert output_coil['reference'] == 'Бухта-021'
    assert output_coil['quantity'] == 220
    assert allocated_lines_order_id_and_line_item == {(line_data['order_id'], line_data['line_item'])}
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_get_a_coil_raise_not_exist_exception():
    client = APIClient()
    # Добавление coil в базу данных с помощью POST запроса
    coil_data = {"reference": "Бухта-023", "product_id": "АВВГ_2х2,5",
                 "quantity": 170, "recommended_balance": 12, "acceptable_loss": 3}
    input_coil_data = json.dumps(coil_data, ensure_ascii=False)
    client.post('/v1/coils', data=input_coil_data, format='json')
    # wrong_reference - это reference несуществующего в базе данных coil
    wrong_reference = 'Бухта-005'

    # Получение несуществующего coil с помощью GET запроса
    response = client.get(f"/v1/coils/{wrong_reference}")
    output_data = json.loads(response.data)

    # Получение coil по несуществующему route вызовет исключение DBCoilRecordDoesNotExist
    assert output_data['message'] == \
           f"Запись с reference={wrong_reference} отсутствует в таблице Coil базы данных"
    assert response.status_code == 404


@pytest.mark.django_db(transaction=True)
def test_get_a_coil_raise_validation_error():
    client = APIClient()
    # Добавление coil в базу данных с помощью UnitOfWork
    # quantity и recommended_balance имеют отрицательные значения
    # Итого два несоответствия CoilBaseModel
    uow = unit_of_work.DjangoCoilUnitOfWork()
    with uow:
        coil = domain_logic.Coil(reference='Бухта-025', product_id='АВВГ_2х2,5', quantity=-150,
                                 recommended_balance=-10, acceptable_loss=2)
        uow.coil_repo.add(coil)
        uow.commit()

    # Получение coil с помощью GET запроса
    response = client.get("/v1/coils/Бухта-025")
    output_data = json.loads(response.data)

    # coil не соответствует CoilBaseModel, что вызовет ошибку ValidationError
    assert '2 validation errors for CoilBaseModel' in output_data['message']
    assert response.status_code == 500


@pytest.mark.django_db(transaction=True)
def test_update_a_coil(three_coils_and_lines):
    client = APIClient()
    # Добавление coil в базу данных с помощью POST запроса
    coil_data_1 = {"reference": "Бухта-031", "product_id": "АВВГ_2х6",
                   "quantity": 85, "recommended_balance": 10, "acceptable_loss": 3}
    input_coil_data_1 = json.dumps(coil_data_1, ensure_ascii=False)
    client.post('/v1/coils', data=input_coil_data_1, format='json')
    # Добавление orderlines в базу данных и дальнейшее размещение (allocation) с помощью POST запросов
    for line_data in three_coils_and_lines['three_lines']:
        input_line_data = json.dumps(line_data, ensure_ascii=False)
        client.post('/v1/orderlines', data=input_line_data, format='json')
        client.post('/v1/allocate', data=input_line_data, format='json')

    # Обновление coil с уменьщением quantity с помощью PUT запроса
    coil_data_2 = {"reference": "Бухта-031", "product_id": "АВВГ_2х6",
                   "quantity": 60, "recommended_balance": 10, "acceptable_loss": 3}
    input_coil_data_2 = json.dumps(coil_data_2, ensure_ascii=False)
    response = client.put(f"/v1/coils/{coil_data_1['reference']}", data=input_coil_data_2, format='json')
    output_data = json.loads(response.data)
    # Получение множества из кортежей (order_id, line_item) неразмещенных orderlines
    deallocated_lines_order_id_and_line_item = \
        {(json.loads(line)['order_id'], json.loads(line)['line_item']) for line in output_data}
    # Получение обновленного coil с помощью GET запроса
    response_2 = client.get('/v1/coils/Бухта-031')
    output_coil = json.loads(response_2.data)
    # Получение множества из кортежей (order_id, line_item) размещенных orderlines для полученного output_coil
    allocated_lines_order_id_and_line_item = \
        {(json.loads(line)['order_id'], json.loads(line)['line_item']) for line in output_coil['allocations']}

    # Обновление coil приведет к тому, что line_1 ("Заказ-031", "Позиция-005") перестанет быть размещенной
    assert deallocated_lines_order_id_and_line_item == {("Заказ-031", "Позиция-005")}
    assert allocated_lines_order_id_and_line_item == {("Заказ-032", "Позиция-004"), ("Заказ-033", "Позиция-002")}
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_update_a_coil_raise_validation_error():
    client = APIClient()
    # Создание coil
    # reference имеет неверное значение, quantity и acceptable_loss имеют отрицательные значения
    # Итого три несоответствия CoilBaseModel
    coil_data = {"reference": "Бу[та-035", "product_id": "АВВГ_2х2,5",
                 "quantity": -70, "recommended_balance": 10, "acceptable_loss": -2}
    input_data = json.dumps(coil_data, ensure_ascii=False)

    # Обновление coil в базе данных с помощью PUT запроса
    response = client.put(f"/v1/coils/{coil_data['reference']}", data=input_data, format='json')
    output_data = json.loads(response.data)

    # coil не соответствует CoilBaseModel, что вызовет ошибку ValidationError
    assert '3 validation errors for CoilBaseModel' in output_data['message']
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_update_a_coil_raise_not_exist_exception():
    client = APIClient()
    # Добавление coil в базу данных с помощью POST запроса
    coil_data_1 = {"reference": "Бухта-037", "product_id": "АВВГ_2х2,5",
                   "quantity": 120, "recommended_balance": 15, "acceptable_loss": 3}
    input_coil_data_1 = json.dumps(coil_data_1, ensure_ascii=False)
    client.post('/v1/coils', data=input_coil_data_1, format='json')
    # wrong_reference - это reference несуществующего в базе данных coil
    wrong_reference = "Бухта-038"

    # Обновление несуществующего coil в базе данных с помощью PUT запроса
    coil_data_2 = {"reference": "Бухта-037", "product_id": "АВВГ_2х2,5",
                   "quantity": 150, "recommended_balance": 20, "acceptable_loss": 3}
    input_coil_data_2 = json.dumps(coil_data_2, ensure_ascii=False)
    response = client.put(f"/v1/coils/{wrong_reference}", data=input_coil_data_2, format='json')
    output_data = json.loads(response.data)

    # Обновление coil по несуществующему route вызовет исключение DBCoilRecordDoesNotExist
    assert output_data['message'] == \
           f"Запись с reference={wrong_reference} отсутствует в таблице Coil базы данных"
    assert response.status_code == 404


@pytest.mark.django_db(transaction=True)
def test_delete_a_coil(three_coils_and_lines):
    client = APIClient()
    # Добавление coil в базу данных с помощью POST запроса
    coil_data = {"reference": "Бухта-038", "product_id": "АВВГ_2х6",
                 "quantity": 85, "recommended_balance": 10, "acceptable_loss": 3}
    input_coil_data = json.dumps(coil_data, ensure_ascii=False)
    client.post('/v1/coils', data=input_coil_data, format='json')
    # Добавление orderlines в базу данных и дальнейшее размещение (allocation) с помощью POST запросов
    for line_data in three_coils_and_lines['three_lines']:
        input_line_data = json.dumps(line_data, ensure_ascii=False)
        client.post('/v1/orderlines', data=input_line_data, format='json')
        client.post('/v1/allocate', data=input_line_data, format='json')

    # Удаление coil с помощью DELETE запроса
    response = client.delete(f"/v1/coils/{coil_data['reference']}")
    output_data = json.loads(response.data)
    # Получение множества из кортежей (order_id, line_item) для orderlines,
    # которые перестали быть размещены после удаления coil
    deallocated_lines_order_id_and_line_item = \
        {(json.loads(line)['order_id'], json.loads(line)['line_item']) for line in output_data}

    # Удаление orderline вернет множество deallocated_lines переставших быть размещенными orderlines
    assert deallocated_lines_order_id_and_line_item == \
           {("Заказ-031", "Позиция-005"), ("Заказ-032", "Позиция-004"), ("Заказ-033", "Позиция-002")}
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_delete_a_coil_raise_not_exist_exception():
    client = APIClient()
    # Добавление coil в базу данных с помощью POST запроса
    coil_data = {"reference": 'Бухта-039', "product_id": "АВВГ_2х2,5",
                 "quantity": 200, "recommended_balance": 10, "acceptable_loss": 2}
    input_coil_data = json.dumps(coil_data, ensure_ascii=False)
    client.post('/v1/coils', data=input_coil_data, format='json')
    # wrong_reference - это reference несуществующего в базе данных coil
    wrong_reference = 'Бухта-002'

    # Удаление несуществующего coil с помощью DELETE запроса
    response = client.delete(f"/v1/coils/{wrong_reference}")
    output_data = json.loads(response.data)

    # Удаление coil по несуществующему route вызовет исключение DBCoilRecordDoesNotExist
    assert output_data['message'] == \
           f"Запись с reference={wrong_reference} отсутствует в таблице Coil базы данных"
    assert response.status_code == 404
