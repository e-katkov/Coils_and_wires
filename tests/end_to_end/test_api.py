import pytest
import json

from rest_framework.test import APIClient


@pytest.mark.django_db(transaction=True)
def test_add_a_coil():
    data = {"reference": 'Бухта-0010', "product_id": "АВВГ_2х2,5",
            "quantity": 150, "recommended_balance": 10, "acceptable_loss": 2}
    client = APIClient()
    output_data = json.dumps(data, ensure_ascii=False)
    response = client.post('/v1/coils', data=output_data, format='json')

    assert response.data['message'] == 'OK'
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_adding_a_coil_is_idempotent():
    data_1 = {"reference": 'Бухта-015', "product_id": "АВВГ_2х2,5",
              "quantity": 150, "recommended_balance": 10, "acceptable_loss": 2}
    data_2 = {"reference": 'Бухта-015', "product_id": "АВВГ_3х1,5",
              "quantity": 200, "recommended_balance": 12, "acceptable_loss": 1}
    client = APIClient()

    output_data_1 = json.dumps(data_1, ensure_ascii=False)
    output_data_2 = json.dumps(data_2, ensure_ascii=False)
    client.post('/v1/coils', data=output_data_1, format='json')
    response = client.post('/v1/coils', data=output_data_2, format='json')

    assert response.data['message'] == \
           f'Запись с reference={data_2["reference"]} уже существует в таблице Coil базы данных'
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_raise_validation_error():
    data = {"reference": 'Бухты-0020', "product_id": "АВВГ_2х2,5",
            "quantity": -70, "recommended_balance": -10, "acceptable_loss": 2}
    client = APIClient()

    output_data = json.dumps(data, ensure_ascii=False)
    response = client.post('/v1/coils', data=output_data, format='json')

    assert '3 validation errors for CoilBaseModel' in response.data['message']
    assert response.status_code == 400
