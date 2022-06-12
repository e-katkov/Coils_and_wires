import json
import pytest

from rest_framework.test import APIClient

from allocation.domain import domain_logic
from allocation.services import unit_of_work


@pytest.mark.django_db(transaction=True)
def test_add_a_coil():
    coil_data = {"reference": 'Бухта-0010', "product_id": "АВВГ_2х2,5",
                 "quantity": 150, "recommended_balance": 10, "acceptable_loss": 2}
    client = APIClient()
    input_coil_data = json.dumps(coil_data, ensure_ascii=False)

    response = client.post('/v1/coils', data=input_coil_data, format='json')
    output_data = json.loads(response.data)

    assert output_data['message'] == 'OK'
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_add_a_coil_is_idempotent():
    coil_data_1 = {"reference": 'Бухта-015', "product_id": "АВВГ_2х2,5",
                   "quantity": 150, "recommended_balance": 10, "acceptable_loss": 2}
    coil_data_2 = {"reference": 'Бухта-015', "product_id": "АВВГ_3х1,5",
                   "quantity": 200, "recommended_balance": 12, "acceptable_loss": 1}
    client = APIClient()
    input_coil_data_1 = json.dumps(coil_data_1, ensure_ascii=False)
    input_coil_data_2 = json.dumps(coil_data_2, ensure_ascii=False)

    client.post('/v1/coils', data=input_coil_data_1, format='json')
    response = client.post('/v1/coils', data=input_coil_data_2, format='json')
    output_data = json.loads(response.data)

    assert output_data['message'] == \
           f'Запись с reference={coil_data_2["reference"]} уже существует в таблице Coil базы данных'
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_add_a_coil_raise_validation_error():
    # reference имеет неверное имя, quantity и recommended_balance имеют отрицательные значения.
    # Итого три несоответствия CoilBaseModel
    coil_data = {"reference": 'Бухт-020', "product_id": "АВВГ_2х2,5",
                 "quantity": -70, "recommended_balance": -10, "acceptable_loss": 2}
    client = APIClient()
    input_data = json.dumps(coil_data, ensure_ascii=False)

    response = client.post('/v1/coils', data=input_data, format='json')
    output_data = json.loads(response.data)

    assert '3 validation errors for CoilBaseModel' in output_data['message']
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_get_a_coil():
    client = APIClient()
    # Добавление coil_data в базу данных с помощью post запроса
    coil_data = {"reference": 'Бухта-021', "product_id": "АВВГ_2х2,5",
                 "quantity": 220, "recommended_balance": 12, "acceptable_loss": 3}
    input_coil_data = json.dumps(coil_data, ensure_ascii=False)
    client.post('/v1/coils', data=input_coil_data, format='json')
    # Добавление orderline в базу данных и дальнейшее размещение (allocation) с помощью post запросов
    line_data = {"order_id": 'Заказ-017', "line_item": "Позиция-001",
                 "product_id": 'АВВГ_2х2,5', "quantity": 40}
    input_line_data = json.dumps(line_data, ensure_ascii=False)
    client.post('/v1/orderlines', data=input_line_data, format='json')
    client.post('/v1/allocate', data=input_line_data, format='json')

    response = client.get(f"/v1/coils/{coil_data['reference']}")
    output_coil = json.loads(response.data)
    # множество из значений order_id размещенных (allocated) orderlines для полученного output_coil
    output_allocated_lines_order_ids = {json.loads(line)['order_id'] for line in output_coil['allocations']}

    assert output_coil['reference'] == 'Бухта-021'
    assert output_coil['quantity'] == 220
    assert output_allocated_lines_order_ids == {line_data['order_id']}
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_get_a_coil_raise_not_exist_error():
    coil_data = {"reference": 'Бухта-023', "product_id": "АВВГ_2х2,5",
                 "quantity": 170, "recommended_balance": 12, "acceptable_loss": 3}
    client = APIClient()
    input_coil_data = json.dumps(coil_data, ensure_ascii=False)
    client.post('/v1/coils', data=input_coil_data, format='json')
    wrong_reference = 'Бухта-005'

    response = client.get(f"/v1/coils/{wrong_reference}")
    output_data = json.loads(response.data)

    assert output_data['message'] == \
           f"Запись с reference={wrong_reference} отсутствует в таблице Coil базы данных"
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_get_a_coil_raise_validation_error():
    # запись добавляется в базу данных с помощью UnitOfWork
    # запись имеет ошибки в quantity и recommended_balance
    coil_data = {'reference': 'Бухта-025', 'product_id': 'АВВГ_2х2,5',
                 'quantity': -150, 'recommended_balance': -10, 'acceptable_loss': 2}
    uow = unit_of_work.DjangoCoilUnitOfWork()
    with uow:
        coil = domain_logic.Coil(coil_data['reference'], coil_data['product_id'], coil_data['quantity'],
                                 coil_data['recommended_balance'], coil_data['acceptable_loss'])
        uow.coil_repo.add(coil)
        uow.commit()
    client = APIClient()

    response = client.get(f"/v1/coils/{coil_data['reference']}")
    output_data = json.loads(response.data)

    assert '2 validation errors for CoilBaseModel' in output_data['message']
    assert response.status_code == 500
