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
    # orderline имеют одинаковые значения order_id и line_item
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
def test_get_a_line_raise_not_exist_exception():
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
    # Добавление orderline в базу данных с помощью UnitOfWork
    # запись имеет ошибку в quantity, т.е. одно несоответствие OrderLineBaseModel
    line_data = {"order_id": 'Заказ-011', "line_item": "Позиция-001",
                 "product_id": 'АВВГ_2х6', "quantity": -12}
    uow = unit_of_work.DjangoOrderLineUnitOfWork()
    with uow:
        line = domain_logic.OrderLine(line_data['order_id'], line_data['line_item'],
                                      line_data['product_id'], line_data['quantity'])
        uow.line_repo.add(line)
        uow.commit()
    client = APIClient()

    response = client.get(f"/v1/orderlines/{line_data['order_id']}/{line_data['line_item']}")
    output_data = json.loads(response.data)

    assert '1 validation error for OrderLineBaseModel' in output_data['message']
    assert response.status_code == 500


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('line_2_quantity, coil_reference, coil_quantity',
                         [(30, "Бухта-031", 95), (90, "Бухта-032", 105)],
                         ids=["smaller_coil", "medium_coil"])
def test_update_a_line_returns_not_fake_coil(three_coils_and_lines, line_2_quantity, coil_reference, coil_quantity):
    client = APIClient()
    # Добавление coils в базу данных с помощью post запросов
    for coil_data in three_coils_and_lines['three_coils']:
        input_coil_data = json.dumps(coil_data, ensure_ascii=False)
        client.post('/v1/coils', data=input_coil_data, format='json')
    # Добавление orderline в базу данных и дальнейшее размещение (allocation) с помощью post запроса
    line_data_1 = {"order_id": "Заказ-015", "line_item": "Позиция-001",
                   "product_id": "АВВГ_2х6", "quantity": 40}
    input_line_data_1 = json.dumps(line_data_1, ensure_ascii=False)
    client.post('/v1/orderlines', data=input_line_data_1, format='json')
    client.post('/v1/allocate', data=input_line_data_1, format='json')

    # Обновление orderline с уменьщением (1) и увеличением (2) quantity.
    # orderline должна быть размещена в smaller_coil (1) и medium_coil (2)
    line_data_2 = {"order_id": "Заказ-015", "line_item": "Позиция-001",
                   "product_id": "АВВГ_2х6", "quantity": line_2_quantity}
    input_line_data_2 = json.dumps(line_data_2, ensure_ascii=False)
    response = client.put(f"/v1/orderlines/{line_data_1['order_id']}/{line_data_1['line_item']}",
                          data=input_line_data_2, format='json')
    output_data = json.loads(response.data)

    assert output_data['reference'] == coil_reference
    assert output_data['quantity'] == coil_quantity
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_update_a_line_returns_fake_coil(three_coils_and_lines):
    client = APIClient()
    # Добавление coils в базу данных с помощью post запросов
    for coil_data in three_coils_and_lines['three_coils']:
        input_coil_data = json.dumps(coil_data, ensure_ascii=False)
        client.post('/v1/coils', data=input_coil_data, format='json')
    # Добавление orderline в базу данных с помощью post запроса
    # orderline остается неразмещенной
    line_data_1 = {"order_id": "Заказ-015", "line_item": "Позиция-001",
                   "product_id": "АВВГ_2х6", "quantity": 40}
    input_line_data_1 = json.dumps(line_data_1, ensure_ascii=False)
    client.post('/v1/orderlines', data=input_line_data_1, format='json')

    # Обновление orderline с уменьщением quantity.
    line_data_2 = {"order_id": "Заказ-015", "line_item": "Позиция-001",
                   "product_id": "АВВГ_2х6", "quantity": 25}
    input_line_data_2 = json.dumps(line_data_2, ensure_ascii=False)
    response = client.put(f"/v1/orderlines/{line_data_1['order_id']}/{line_data_1['line_item']}",
                          data=input_line_data_2, format='json')
    output_data = json.loads(response.data)

    assert output_data['reference'] == 'fake'
    assert output_data['quantity'] == 1
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_put_a_line_raise_input_validation_error():
    client = APIClient()
    # Добавление orderline в базу данных с помощью post запроса
    line_data_1 = {"order_id": 'Заказ-017', "line_item": "Позиция-002",
                   "product_id": 'АВВГ_2х2,5', "quantity": 30}
    input_coil_data_1 = json.dumps(line_data_1, ensure_ascii=False)
    client.post('/v1/orderlines', data=input_coil_data_1, format='json')

    # Обновление orderline в базе данных с помощью post запроса
    # line_item имеет неверное имя, quantity имеет отрицательные значение.
    # Итого два несоответствия OrderLineBaseModel
    line_data_2 = {"order_id": 'Заказ-017', "line_item": "Пазиция-004",
                   "product_id": 'АВВГ_2х2,5', "quantity": -24}
    input_line_data_2 = json.dumps(line_data_2, ensure_ascii=False)
    response = client.put(f"/v1/orderlines/{line_data_1['order_id']}/{line_data_1['line_item']}",
                          data=input_line_data_2, format='json')
    output_data = json.loads(response.data)

    assert '2 validation errors for OrderLineBaseModel' in output_data['message']
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_put_a_line_raise_not_exist_exception():
    client = APIClient()
    # Добавление orderline в базу данных с помощью post запроса
    line_data_1 = {"order_id": 'Заказ-018', "line_item": "Позиция-003",
                   "product_id": 'АВВГ_2х2,5', "quantity": 15}
    input_coil_data_1 = json.dumps(line_data_1, ensure_ascii=False)
    client.post('/v1/orderlines', data=input_coil_data_1, format='json')
    # wrong_line_item - это line_item несуществующей в базе данных orderline
    wrong_line_item = "Позиция-004"

    # Обновление orderline в базе данных с помощью post запроса
    # line_item в route содержит неверное значение - wrong_line_item
    line_data_2 = {"order_id": 'Заказ-018', "line_item": "Позиция-003",
                   "product_id": 'АВВГ_2х2,5', "quantity": 18}
    input_line_data_2 = json.dumps(line_data_2, ensure_ascii=False)
    response = client.put(f"/v1/orderlines/{line_data_1['order_id']}/{wrong_line_item}",
                          data=input_line_data_2, format='json')
    output_data = json.loads(response.data)

    assert output_data['message'] == \
           f"Запись с order_id={line_data_1['order_id']} и line_item={wrong_line_item}" \
           f" отсутствует в таблице OrderLine базы данных"
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_put_a_line_raise_output_validation_error():
    # Добавление coil в базу данных с помощью UnitOfWork
    # запись имеет ошибку в recommended_balance, т.е. одно несоответствие CoilBaseModel
    coil_data = {'reference': 'Бухта-025', 'product_id': 'АВВГ_2х2,5',
                 'quantity': 200, 'recommended_balance': -10, 'acceptable_loss': 3}
    uow = unit_of_work.DjangoCoilUnitOfWork()
    with uow:
        coil = domain_logic.Coil(coil_data['reference'], coil_data['product_id'], coil_data['quantity'],
                                 coil_data['recommended_balance'], coil_data['acceptable_loss'])
        uow.coil_repo.add(coil)
        uow.commit()
    client = APIClient()
    # Добавление orderline в базу данных и дальнейшее размещение (allocation) с помощью post запроса
    line_data_1 = {"order_id": "Заказ-019", "line_item": "Позиция-001",
                   "product_id": "АВВГ_2х2,5", "quantity": 40}
    input_line_data_1 = json.dumps(line_data_1, ensure_ascii=False)
    client.post('/v1/orderlines', data=input_line_data_1, format='json')
    client.post('/v1/allocate', data=input_line_data_1, format='json')

    # Обновление orderline в базе данных с помощью post запроса
    # возвращаемый allocation_coil не пройдет валидацию, возникнет validation error
    line_data_2 = {"order_id": "Заказ-019", "line_item": "Позиция-001",
                   "product_id": "АВВГ_2х2,5", "quantity": 45}
    input_line_data_2 = json.dumps(line_data_2, ensure_ascii=False)
    response = client.put(f"/v1/orderlines/{line_data_1['order_id']}/{line_data_1['line_item']}",
                          data=input_line_data_2, format='json')
    output_data = json.loads(response.data)

    assert '1 validation error for CoilBaseModel' in output_data['message']
    assert response.status_code == 500


@pytest.mark.django_db(transaction=True)
def test_delete_a_line_returns_not_fake_coil(three_coils_and_lines):
    client = APIClient()
    # Добавление coils в базу данных с помощью post запросов
    for coil_data in three_coils_and_lines['three_coils']:
        input_coil_data = json.dumps(coil_data, ensure_ascii=False)
        client.post('/v1/coils', data=input_coil_data, format='json')
    # Добавление orderline в базу данных и дальнейшее размещение (allocation) с помощью post запроса
    # Размещение будет выполнено в smaller_coil
    line_data = {"order_id": "Заказ-022", "line_item": "Позиция-004",
                 "product_id": "АВВГ_2х6", "quantity": 50}
    input_line_data = json.dumps(line_data, ensure_ascii=False)
    client.post('/v1/orderlines', data=input_line_data, format='json')
    client.post('/v1/allocate', data=input_line_data, format='json')

    # Удаление orderline
    response = client.delete(f"/v1/orderlines/{line_data['order_id']}/{line_data['line_item']}")
    output_data = json.loads(response.data)

    assert output_data['reference'] == "Бухта-031"
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_delete_a_line_returns_fake_coil(three_coils_and_lines):
    client = APIClient()
    # Добавление orderline в базу данных с помощью post запроса
    # Размещение не будет выполнено, поэтому при удалении будет возвращен "поддельный" coil
    line_data = {"order_id": "Заказ-023", "line_item": "Позиция-004",
                 "product_id": "АВВГ_2х2,5", "quantity": 12}
    input_line_data = json.dumps(line_data, ensure_ascii=False)
    client.post('/v1/orderlines', data=input_line_data, format='json')

    # Удаление orderline
    response = client.delete(f"/v1/orderlines/{line_data['order_id']}/{line_data['line_item']}")
    output_data = json.loads(response.data)

    assert output_data['reference'] == 'fake'
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_delete_a_line_raise_not_exist_exception():
    client = APIClient()
    # Добавление orderline в базу данных с помощью post запроса
    line_data = {"order_id": "Заказ-024", "line_item": "Позиция-003",
                 "product_id": "АВВГ_2х2,5", "quantity": 14}
    input_coil_data = json.dumps(line_data, ensure_ascii=False)
    client.post('/v1/orderlines', data=input_coil_data, format='json')
    # wrong_order_id - это order_id несуществующей в базе данных orderline
    wrong_order_id = "Позиция-002"

    # Удаление orderline
    # order_id в route имеет неверное значение - wrong_order_id
    response = client.delete(f"/v1/orderlines/{wrong_order_id}/{line_data['line_item']}")
    output_data = json.loads(response.data)

    assert output_data['message'] == \
           f"Запись с order_id={wrong_order_id} и line_item={line_data['line_item']}" \
           f" отсутствует в таблице OrderLine базы данных"
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_delete_a_line_raise_validation_error():
    # Добавление coil в базу данных с помощью UnitOfWork
    # запись имеет ошибку в acceptable_loss, т.е. одно несоответствие CoilBaseModel
    uow = unit_of_work.DjangoCoilUnitOfWork()
    with uow:
        coil = domain_logic.Coil(reference='Бухта-027', product_id='АВВГ_2х2,5', quantity=150,
                                 recommended_balance=12, acceptable_loss=-4)
        uow.coil_repo.add(coil)
        uow.commit()
    client = APIClient()
    # Добавление orderline в базу данных и дальнейшее размещение (allocation) с помощью post запроса
    line_data = {"order_id": "Заказ-025", "line_item": "Позиция-004",
                 "product_id": "АВВГ_2х2,5", "quantity": 15}
    input_line_data = json.dumps(line_data, ensure_ascii=False)
    client.post('/v1/orderlines', data=input_line_data, format='json')
    client.post('/v1/allocate', data=input_line_data, format='json')

    # Удаление orderline
    response = client.delete(f"/v1/orderlines/{line_data['order_id']}/{line_data['line_item']}")
    output_data = json.loads(response.data)

    assert '1 validation error for CoilBaseModel' in output_data['message']
    assert response.status_code == 500
