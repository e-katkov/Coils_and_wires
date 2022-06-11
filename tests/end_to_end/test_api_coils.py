import json
import pytest

from rest_framework.test import APIClient

from allocation.domain import domain_logic
from allocation.services import unit_of_work


@pytest.mark.django_db(transaction=True)
def test_add_a_coil():
    data = {"reference": 'Бухта-0010', "product_id": "АВВГ_2х2,5",
            "quantity": 150, "recommended_balance": 10, "acceptable_loss": 2}
    client = APIClient()
    output_data = json.dumps(data, ensure_ascii=False)

    response = client.post('/v1/coils', data=output_data, format='json')
    input_data = json.loads(response.data)

    assert input_data['message'] == 'OK'
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_add_a_coil_is_idempotent():
    data_1 = {"reference": 'Бухта-015', "product_id": "АВВГ_2х2,5",
              "quantity": 150, "recommended_balance": 10, "acceptable_loss": 2}
    data_2 = {"reference": 'Бухта-015', "product_id": "АВВГ_3х1,5",
              "quantity": 200, "recommended_balance": 12, "acceptable_loss": 1}
    client = APIClient()
    output_data_1 = json.dumps(data_1, ensure_ascii=False)
    output_data_2 = json.dumps(data_2, ensure_ascii=False)

    client.post('/v1/coils', data=output_data_1, format='json')
    response = client.post('/v1/coils', data=output_data_2, format='json')
    input_data = json.loads(response.data)

    assert input_data['message'] == \
           f'Запись с reference={data_2["reference"]} уже существует в таблице Coil базы данных'
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_add_a_coil_raise_validation_error():
    # reference имеет неверное имя, quantity и recommended_balance имеют отрицательные значения.
    # Итого три несоответствия CoilBaseModel
    data = {"reference": 'Бухт-020', "product_id": "АВВГ_2х2,5",
            "quantity": -70, "recommended_balance": -10, "acceptable_loss": 2}
    client = APIClient()
    output_data = json.dumps(data, ensure_ascii=False)

    response = client.post('/v1/coils', data=output_data, format='json')
    input_data = json.loads(response.data)

    assert '3 validation errors for CoilBaseModel' in input_data['message']
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_get_a_coil():
    client = APIClient()
    # Добавление coil_data в базу данных с помощью post запроса
    coil_data = {"reference": 'Бухта-021', "product_id": "АВВГ_2х2,5",
                 "quantity": 200, "recommended_balance": 12, "acceptable_loss": 3}
    output_coil_data = json.dumps(coil_data, ensure_ascii=False)
    client.post('/v1/coils', data=output_coil_data, format='json')
    # Добавление line_data в базу данных с помощью post запроса
    line_data = {"order_id": 'Заказ-017', "line_item": "Позиция-001",
                 "product_id": 'АВВГ_3х2,5', "quantity": 40}
    output_line_data = json.dumps(line_data, ensure_ascii=False)
    client.post('/v1/orderlines', data=output_line_data, format='json')

    response = client.get(f"/v1/coils/{coil_data['reference']}")
    input_data = json.loads(response.data)

    assert input_data['reference'] == 'Бухта-021'
    assert input_data['quantity'] == 200
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_get_a_coil_raise_not_exist_error():
    data = {"reference": 'Бухта-023', "product_id": "АВВГ_2х2,5",
            "quantity": 170, "recommended_balance": 12, "acceptable_loss": 3}
    client = APIClient()
    output_data = json.dumps(data, ensure_ascii=False)
    client.post('/v1/coils', data=output_data, format='json')
    wrong_reference = 'Бухта-005'

    response = client.get(f"/v1/coils/{wrong_reference}")
    input_data = json.loads(response.data)

    assert input_data['message'] == \
           f"Запись с reference={wrong_reference} отсутствует в таблице Coil базы данных"
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_get_a_coil_raise_validation_error():
    # запись добавляется в базу данных с помощью UnitOfWork
    # запись имеет ошибки в quantity и recommended_balance
    data = {'reference': 'Бухта-025', 'product_id': 'АВВГ_2х2,5',
            'quantity': -150, 'recommended_balance': -10, 'acceptable_loss': 2}
    uow = unit_of_work.DjangoCoilUnitOfWork()
    with uow:
        coil = domain_logic.Coil(data['reference'], data['product_id'], data['quantity'],
                                 data['recommended_balance'], data['acceptable_loss'])
        uow.coil_repo.add(coil)
        uow.commit()
    client = APIClient()

    response = client.get(f"/v1/coils/{data['reference']}")
    input_data = json.loads(response.data)

    assert '2 validation errors for CoilBaseModel' in input_data['message']
    assert response.status_code == 500
