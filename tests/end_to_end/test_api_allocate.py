import json
import pytest

from rest_framework.test import APIClient

from allocation.domain import domain_logic
from allocation.services import unit_of_work


@pytest.mark.django_db(transaction=True)
def test_allocate_a_line(three_coils_and_lines):
    client = APIClient()
    # Добавление coil в базу данных с помощью post запросов
    for coil_data in three_coils_and_lines['three_coils']:
        input_coil_data = json.dumps(coil_data, ensure_ascii=False)
        client.post('/v1/coils', data=input_coil_data, format='json')
    # Добавление orderline в базу данных и дальнейшее размещение (allocation) с помощью post запросов
    for line_data in three_coils_and_lines['three_lines']:
        input_line_data = json.dumps(line_data, ensure_ascii=False)
        client.post('/v1/orderlines', data=input_line_data, format='json')
        client.post('/v1/allocate', data=input_line_data, format='json')

    # Ожидается, что orderlines должны быть размещены в coil, у которого reference='Бухта-031'
    response = client.get('/v1/coils/Бухта-031')
    output_coil = json.loads(response.data)
    # множество из кортежей (order_id, line_item) размещенных orderlines для полученного output_coil
    allocated_lines_order_id_and_line_item = \
        {(json.loads(line)['order_id'], json.loads(line)['line_item']) for line in output_coil['allocations']}

    assert output_coil['reference'] == 'Бухта-031'
    assert allocated_lines_order_id_and_line_item == \
           {(line['order_id'], line['line_item']) for line in three_coils_and_lines['three_lines']}


@pytest.mark.django_db(transaction=True)
def test_allocate_a_line_is_idempotent(three_coils_and_lines):
    client = APIClient()
    # Добавление coil в базу данных с помощью post запросов
    for coil_data in three_coils_and_lines['three_coils']:
        input_coil_data = json.dumps(coil_data, ensure_ascii=False)
        client.post('/v1/coils', data=input_coil_data, format='json')
    # Добавление orderline в базу данных и дальнейшее размещение (allocation) с помощью post запросов
    for line_data in three_coils_and_lines['three_lines']:
        input_line_data = json.dumps(line_data, ensure_ascii=False)
        client.post('/v1/orderlines', data=input_line_data, format='json')
        client.post('/v1/allocate', data=input_line_data, format='json')
    # Повторное размещение одного orderline с помощью post запроса
    line_data = three_coils_and_lines['three_lines'][1]
    input_line_data = json.dumps(line_data, ensure_ascii=False)
    client.post('/v1/allocate', data=input_line_data, format='json')

    # Ожидается, что orderlines должны быть размещены в coil, у которого reference='Бухта-031'
    response = client.get('/v1/coils/Бухта-031')
    output_coil = json.loads(response.data)
    # множество из кортежей (order_id, line_item) размещенных orderlines для полученного output_coil
    allocated_lines_order_id_and_line_item = \
        {(json.loads(line)['order_id'], json.loads(line)['line_item']) for line in output_coil['allocations']}
    # Получение значений coil, для которых не должно было произойти размещение
    response_medium_coil = client.get('/v1/coils/Бухта-032')
    output_medium_coil = json.loads(response_medium_coil.data)
    response_bigger_coil = client.get('/v1/coils/Бухта-033')
    output_bigger_coil = json.loads(response_bigger_coil.data)

    assert output_coil['reference'] == 'Бухта-031'
    assert allocated_lines_order_id_and_line_item == \
           {(line['order_id'], line['line_item']) for line in three_coils_and_lines['three_lines']}
    assert output_medium_coil['allocations'] == []
    assert output_bigger_coil['allocations'] == []


@pytest.mark.django_db(transaction=True)
def test_allocate_a_line_raise_input_validation_error():
    # order_id имеет неверное имя, quantity имеет отрицательные значение.
    # Итого два несоответствия OrderLineBaseModel
    line = {"order_id": "Закfз-034", "line_item": "Позиция-002",
              "product_id": 'АВВГ_2х6', "quantity": -20}
    client = APIClient()
    input_data = json.dumps(line, ensure_ascii=False)

    response = client.post('/v1/allocate', data=input_data, format='json')
    output_data = json.loads(response.data)

    assert '2 validation errors for OrderLineBaseModel' in output_data['message']
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_allocate_a_line_raise_output_validation_error():
    # запись добавляется в базу данных с помощью UnitOfWork.
    # Запись имеет ошибки в reference и recommended_balance,
    # Итого два несоответствия CoilBaseModel
    coil_data = {'reference': 'Бухт-035', 'product_id': 'АВВГ_2х6',
            'quantity': 150, 'recommended_balance': -10, 'acceptable_loss': 2}
    uow = unit_of_work.DjangoCoilUnitOfWork()
    with uow:
        coil = domain_logic.Coil(coil_data['reference'], coil_data['product_id'], coil_data['quantity'],
                                 coil_data['recommended_balance'], coil_data['acceptable_loss'])
        uow.coil_repo.add(coil)
        uow.commit()
    # Добавление orderline в базу данных с помощью post запроса
    client = APIClient()
    line_data = {"order_id": "Заказ-036", "line_item": "Позиция-001",
                 "product_id": "АВВГ_2х6", "quantity": 85}
    input_line_data = json.dumps(line_data, ensure_ascii=False)
    client.post('/v1/orderlines', data=input_line_data, format='json')

    response = client.post('/v1/allocate', data=input_line_data, format='json')
    output_data = json.loads(response.data)

    assert '2 validation errors for CoilBaseModel' in output_data['message']
    assert response.status_code == 500


@pytest.mark.django_db(transaction=True)
def test_allocate_a_line_raise_out_of_stock_exception(three_coils_and_lines):
    client = APIClient()
    # Добавление coil в базу данных с помощью post запросов
    for coil_data in three_coils_and_lines['three_coils']:
        input_coil_data = json.dumps(coil_data, ensure_ascii=False)
        client.post('/v1/coils', data=input_coil_data, format='json')
    # Добавление orderline в базу данных с помощью post запроса
    # Orderline имеет заведомо большую величину quantity
    line_data = {"order_id": "Заказ-035", "line_item": "Позиция-002",
                 "product_id": "АВВГ_2х6", "quantity": 600}
    input_line_data = json.dumps(line_data, ensure_ascii=False)
    client.post('/v1/orderlines', data=input_line_data, format='json')

    response = client.post('/v1/allocate', data=input_line_data, format='json')
    output_data = json.loads(response.data)

    assert output_data['message'] == 'Недостаточное количество материала с product_id=АВВГ_2х6'
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_allocate_a_line_raise_not_exist_exception(three_coils_and_lines):
    client = APIClient()
    # Добавление coil в базу данных с помощью post запросов
    for coil_data in three_coils_and_lines['three_coils']:
        input_coil_data = json.dumps(coil_data, ensure_ascii=False)
        client.post('/v1/coils', data=input_coil_data, format='json')
    # Создание orderline без добавления в базу данных
    line_data = {"order_id": "Заказ-036", "line_item": "Позиция-004",
                 "product_id": "АВВГ_2х6", "quantity": 20}
    input_line_data = json.dumps(line_data, ensure_ascii=False)

    response = client.post('/v1/allocate', data=input_line_data, format='json')
    output_data = json.loads(response.data)

    assert output_data['message'] == \
           f"Запись с order_id={line_data['order_id']} и line_item={line_data['line_item']}"\
           f" отсутствует в таблице OrderLine базы данных"
    assert response.status_code == 400
