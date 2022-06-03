import json
import pytest

from rest_framework.test import APIClient


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
