import json
import pytest

from rest_framework.test import APIClient

from allocation.domain import domain_logic
from allocation.services import unit_of_work


@pytest.mark.django_db(transaction=True)
def test_api_allocate_a_line(three_coils_and_lines):
    client = APIClient()
    # Добавление бухт в базу данных с помощью POST запросов
    for coil_data in three_coils_and_lines['three_coils']:
        client.post('/v1/coils', data=coil_data, format='json')
    # Добавление товарных позиций в базу данных и дальнейшее размещение с помощью POST запросов
    for line_data in three_coils_and_lines['three_lines']:
        client.post('/v1/orderlines', data=line_data, format='json')
        client.post('/v1/allocate', data=line_data, format='json')

    # Получение бухты с идентификатором reference='Бухта-031',
    # куда должны быть размещены все товарные позиции
    response = client.get('/v1/coils/Бухта-031')
    output_coil = json.loads(response.data)
    # Получение множества из кортежей (order_id, line_item) размещенных товарных позиций
    # для полученного output_coil
    allocated_lines_order_id_and_line_item = \
        {(json.loads(line)['order_id'], json.loads(line)['line_item']) for line in output_coil['allocations']}

    assert allocated_lines_order_id_and_line_item == \
           {(line['order_id'], line['line_item']) for line in three_coils_and_lines['three_lines']}
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_api_allocate_a_line_is_idempotent(three_coils_and_lines):
    client = APIClient()
    # Добавление бухт в базу данных с помощью POST запросов
    for coil_data in three_coils_and_lines['three_coils']:
        client.post('/v1/coils', data=coil_data, format='json')
    # Добавление товарных позиций в базу данных и дальнейшее размещение с помощью POST запросов
    for line_data in three_coils_and_lines['three_lines']:
        client.post('/v1/orderlines', data=line_data, format='json')
        client.post('/v1/allocate', data=line_data, format='json')
    # Повторное размещение одной товарной позиции с помощью POST запроса
    line_data = three_coils_and_lines['three_lines'][1]
    client.post('/v1/allocate', data=line_data, format='json')

    # Получение бухты с идентификатором reference='Бухта-031',
    # куда должны быть размещены все товарные позиции
    response = client.get('/v1/coils/Бухта-031')
    output_coil = json.loads(response.data)
    # Получение множества из кортежей (order_id, line_item) размещенных товарных позиций
    # для полученного output_coil
    allocated_lines_order_id_and_line_item = \
        {(json.loads(line)['order_id'], json.loads(line)['line_item']) for line in output_coil['allocations']}
    # Получение бухт, для которых не должно было произойти размещение
    response_medium_coil = client.get('/v1/coils/Бухта-032')
    output_medium_coil = json.loads(response_medium_coil.data)
    response_bigger_coil = client.get('/v1/coils/Бухта-033')
    output_bigger_coil = json.loads(response_bigger_coil.data)

    assert allocated_lines_order_id_and_line_item == \
           {(line['order_id'], line['line_item']) for line in three_coils_and_lines['three_lines']}
    assert response.status_code == 200
    assert output_medium_coil['allocations'] == []
    assert output_bigger_coil['allocations'] == []


@pytest.mark.django_db(transaction=True)
def test_api_allocate_a_line_raise_input_validation_error():
    client = APIClient()
    # Создание товарной позиции
    # order_id имеет неверное значение, quantity имеет отрицательное значение
    # Итого два несоответствия OrderLineBaseModel
    line_data = {"order_id": "Закfз-034", "line_item": "Позиция-002",
                 "product_id": 'АВВГ_2х6', "quantity": -20}

    # Размещение товарной позиции с помощью POST запроса
    response = client.post('/v1/allocate', data=line_data, format='json')
    output_data = json.loads(response.data)

    # Товарная позиция не соответствует OrderLineBaseModel, что вызовет ошибку ValidationError
    assert '2 validation errors for OrderLineBaseModel' in output_data['message']
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_api_allocate_a_line_raise_output_validation_error():
    client = APIClient()
    # Добавление бухты в базу данных с помощью UnitOfWork
    # reference имеет неверное значение, recommended_balance имеет отрицательное значение
    # Итого два несоответствия CoilBaseModel
    uow = unit_of_work.DjangoCoilUnitOfWork()
    with uow:
        coil = domain_logic.Coil(reference='Бухт-035', product_id='АВВГ_2х6', quantity=150,
                                 recommended_balance=-10, acceptable_loss=2)
        uow.coil_repo.add(coil)
        uow.commit()
    # Добавление товарной позиции в базу данных с помощью POST запроса
    line_data = {"order_id": "Заказ-036", "line_item": "Позиция-001",
                 "product_id": "АВВГ_2х6", "quantity": 85}
    client.post('/v1/orderlines', data=line_data, format='json')

    # Размещение товарной позиции с помощью POST запроса
    response = client.post('/v1/allocate', data=line_data, format='json')
    output_data = json.loads(response.data)

    # Размещение товарной позиции вернет allocation_coil, который не соответствует CoilBaseModel,
    # что вызовет ошибку ValidationError
    assert '2 validation errors for CoilBaseModel' in output_data['message']
    assert response.status_code == 500


@pytest.mark.django_db(transaction=True)
def test_api_allocate_a_line_raise_out_of_stock_exception(three_coils_and_lines):
    client = APIClient()
    # Добавление бухт в базу данных с помощью POST запросов
    for coil_data in three_coils_and_lines['three_coils']:
        client.post('/v1/coils', data=coil_data, format='json')
    # Добавление товарной позиции в базу данных с помощью POST запроса
    line_data = {"order_id": "Заказ-035", "line_item": "Позиция-002",
                 "product_id": "АВВГ_2х6", "quantity": 600}
    client.post('/v1/orderlines', data=line_data, format='json')

    # Размещение товарной позиции с помощью POST запроса
    response = client.post('/v1/allocate', data=line_data, format='json')
    output_data = json.loads(response.data)

    # Товарная позиция имеет величину quantity большую, чем у бухт,
    # поэтому размещение товарной позиции вызовет исключение OutOfStock
    assert output_data['message'] == 'Недостаточное количество материала с product_id=АВВГ_2х6'
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_api_allocate_a_line_raise_not_exist_exception(three_coils_and_lines):
    client = APIClient()
    # Добавление бухт в базу данных с помощью POST запросов
    for coil_data in three_coils_and_lines['three_coils']:
        client.post('/v1/coils', data=coil_data, format='json')
    # Создание товарной позиции
    line_data = {"order_id": "Заказ-036", "line_item": "Позиция-004",
                 "product_id": "АВВГ_2х6", "quantity": 20}

    # Размещение товарной позиции с помощью POST запроса
    response = client.post('/v1/allocate', data=line_data, format='json')
    output_data = json.loads(response.data)

    # Товарная позиция не была сохранена в базе данных,
    # поэтому ее размещение вызовет исключение DBOrderLineRecordDoesNotExist
    assert output_data['message'] == \
           f"Запись с order_id={line_data['order_id']} и line_item={line_data['line_item']}"\
           f" отсутствует в таблице OrderLine базы данных"
    assert response.status_code == 404


@pytest.mark.django_db(transaction=True)
def test_api_get_an_allocation_coil_returns_real_coil(three_coils_and_lines):
    client = APIClient()
    # Добавление бухт в базу данных с помощью POST запросов
    for coil_data in three_coils_and_lines['three_coils']:
        client.post('/v1/coils', data=coil_data, format='json')
    # Добавление товарной позиции в базу данных и дальнейшее размещение с помощью POST запросов
    # Размещение будет выполнено в smaller_coil
    line_data = {"order_id": "Заказ-037", "line_item": "Позиция-002",
                 "product_id": "АВВГ_2х6", "quantity": 45}
    client.post('/v1/orderlines', data=line_data, format='json')
    client.post('/v1/allocate', data=line_data, format='json')

    # Получение allocation_coil, в которую размещена товарная позиция
    response = client.get(f"/v1/allocate/{line_data['order_id']}/{line_data['line_item']}")
    output_data = json.loads(response.data)

    assert output_data['reference'] == "Бухта-031"
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_api_get_an_allocation_coil_returns_fake_coil(three_coils_and_lines):
    client = APIClient()
    # Добавление бухт в базу данных с помощью POST запросов
    for coil_data in three_coils_and_lines['three_coils']:
        client.post('/v1/coils', data=coil_data, format='json')
    # Добавление товарной позиции в базу данных и дальнейшее размещение с помощью POST запросов
    # Размещение не выполняется
    line_data = {"order_id": "Заказ-037", "line_item": "Позиция-002",
                 "product_id": "АВВГ_2х6", "quantity": 45}
    client.post('/v1/orderlines', data=line_data, format='json')

    # Получение allocation_coil, в которую размещена товарная позиция, с помощью GET запроса
    response = client.get(f"/v1/allocate/{line_data['order_id']}/{line_data['line_item']}")
    output_data = json.loads(response.data)

    # Размещение товарной позиции не выполнялось, что приведет к возврату "поддельной" бухты
    assert output_data['reference'] == 'fake'
    assert output_data['quantity'] == 1
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_api_get_an_allocation_coil_raise_not_exist_exception():
    client = APIClient()
    # Добавление товарной позиции в базу данных с помощью POST запроса
    line_data = {"order_id": 'Заказ-038', "line_item": "Позиция-003",
                 "product_id": 'АВВГ_2х6', "quantity": 70}
    client.post('/v1/orderlines', data=line_data, format='json')
    # wrong_line_item - это line_item несуществующей в базе данных товарной позиции
    wrong_line_item = 'Позиция-005'

    # Получение allocation_coil для несуществующей товарной позиции с помощью GET запроса
    response = client.get(f"/v1/allocate/{line_data['order_id']}/{wrong_line_item}")
    output_data = json.loads(response.data)

    # Получение allocation_coil по несуществующему для товарной позиции route
    # вызовет исключение DBOrderLineRecordDoesNotExist
    assert output_data['message'] == \
           f"Запись с order_id={line_data['order_id']} и line_item={wrong_line_item}" \
           f" отсутствует в таблице OrderLine базы данных"
    assert response.status_code == 404


@pytest.mark.django_db(transaction=True)
def test_api_get_an_allocation_coil_raise_validation_error():
    client = APIClient()
    # Добавление бухты в базу данных с помощью UnitOfWork
    # acceptable_loss имеет отрицательное значение
    # Итого одно несоответствие CoilBaseModel
    uow = unit_of_work.DjangoCoilUnitOfWork()
    with uow:
        coil = domain_logic.Coil(reference='Бухта-027', product_id='АВВГ_2х2,5', quantity=180,
                                 recommended_balance=20, acceptable_loss=-4)
        uow.coil_repo.add(coil)
        uow.commit()
    # Добавление товарной позиции в базу данных и дальнейшее размещение с помощью POST запросов
    line_data = {"order_id": "Заказ-039", "line_item": "Позиция-002",
                 "product_id": "АВВГ_2х2,5", "quantity": 45}
    client.post('/v1/orderlines', data=line_data, format='json')
    client.post('/v1/allocate', data=line_data, format='json')

    # Получение allocation_coil, в которую размещена товарная позиция, с помощью GET запроса
    response = client.get(f"/v1/allocate/{line_data['order_id']}/{line_data['line_item']}")
    output_data = json.loads(response.data)

    # allocation_coil не соответствует CoilBaseModel, что вызовет ошибку ValidationError
    assert '1 validation error for CoilBaseModel' in output_data['message']
    assert response.status_code == 500


@pytest.mark.django_db(transaction=True)
def test_api_deallocate_a_line_returns_real_coil(three_coils_and_lines):
    client = APIClient()
    # Добавление бухт в базу данных с помощью POST запросов
    for coil_data in three_coils_and_lines['three_coils']:
        client.post('/v1/coils', data=coil_data, format='json')
    # Добавление товарной позиции в базу данных и дальнейшее размещение с помощью POST запросов
    # Размещение будет выполнено в smaller_coil
    line_data = {"order_id": "Заказ-040", "line_item": "Позиция-004",
                 "product_id": "АВВГ_2х6", "quantity": 32}
    client.post('/v1/orderlines', data=line_data, format='json')
    client.post('/v1/allocate', data=line_data, format='json')

    # Отмена размещения товарной позиции и получение allocation_coil с помощью DELETE запроса
    response = client.delete(f"/v1/allocate/{line_data['order_id']}/{line_data['line_item']}")
    output_data = json.loads(response.data)

    assert output_data['reference'] == "Бухта-031"
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_api_deallocate_a_line_returns_fake_coil(three_coils_and_lines):
    client = APIClient()
    # Добавление бухт в базу данных с помощью POST запросов
    for coil_data in three_coils_and_lines['three_coils']:
        client.post('/v1/coils', data=coil_data, format='json')
    # Добавление товарной позиции в базу данных и дальнейшее размещение с помощью POST запросов
    # Размещение не выполняется
    line_data = {"order_id": "Заказ-041", "line_item": "Позиция-006",
                 "product_id": "АВВГ_2х6", "quantity": 27}
    client.post('/v1/orderlines', data=line_data, format='json')

    # Отмена размещения товарной позиции и получение allocation_coil с помощью DELETE запроса
    response = client.delete(f"/v1/allocate/{line_data['order_id']}/{line_data['line_item']}")
    output_data = json.loads(response.data)

    # Размещение товарной позиции не выполнялось, что приведет к возврату "поддельной" бухты
    assert output_data['reference'] == 'fake'
    assert output_data['quantity'] == 1
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_api_deallocate_a_line_raise_not_exist_exception():
    client = APIClient()
    # Добавление товарной позиции в базу данных с помощью POST запроса
    line_data = {"order_id": 'Заказ-042', "line_item": "Позиция-001",
                 "product_id": 'АВВГ_2х6', "quantity": 55}
    client.post('/v1/orderlines', data=line_data, format='json')
    # wrong_line_item - это line_item несуществующей в базе данных товарной позиции
    wrong_line_item = 'Позиция-012'

    # Отмена размещения товарной позиции и получение allocation_coil с помощью DELETE запроса
    response = client.delete(f"/v1/allocate/{line_data['order_id']}/{wrong_line_item}")
    output_data = json.loads(response.data)

    # Получение allocation_coil по несуществующему для товарной позиции route
    # вызовет исключение DBOrderLineRecordDoesNotExist
    assert output_data['message'] == \
           f"Запись с order_id={line_data['order_id']} и line_item={wrong_line_item}" \
           f" отсутствует в таблице OrderLine базы данных"
    assert response.status_code == 404


@pytest.mark.django_db(transaction=True)
def test_api_deallocate_a_line_raise_validation_error():
    client = APIClient()
    # Добавление бухты в базу данных с помощью UnitOfWork
    # acceptable_loss имеет отрицательное значение
    # Итого одно несоответствие CoilBaseModel
    uow = unit_of_work.DjangoCoilUnitOfWork()
    with uow:
        coil = domain_logic.Coil(reference='Бухта-028', product_id='АВВГ_2х2,5', quantity=180,
                                 recommended_balance=20, acceptable_loss=-4)
        uow.coil_repo.add(coil)
        uow.commit()
    # Добавление товарной позиции в базу данных и дальнейшее размещение с помощью POST запросов
    line_data = {"order_id": "Заказ-043", "line_item": "Позиция-005",
                 "product_id": "АВВГ_2х2,5", "quantity": 37}
    client.post('/v1/orderlines', data=line_data, format='json')
    client.post('/v1/allocate', data=line_data, format='json')

    # Отмена размещения товарной позиции и получение allocation_coil с помощью DELETE запроса
    response = client.delete(f"/v1/allocate/{line_data['order_id']}/{line_data['line_item']}")
    output_data = json.loads(response.data)

    # allocation_coil не соответствует CoilBaseModel, что вызовет ошибку ValidationError
    assert '1 validation error for CoilBaseModel' in output_data['message']
    assert response.status_code == 500
