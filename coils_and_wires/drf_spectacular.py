from django.urls import path

from drf_spectacular.utils import OpenApiExample, OpenApiResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


urlpatterns = [
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]


coils_descriptions = {
    'get': 'Получить из базы данных бухту с заданным идентификатором reference',
    'post': 'Создать в базе данных новую бухту',
    'put': 'Обновить в базе данных бухту с заданным идентификатором reference',
    'delete': 'Удалить из базы данных бухту с заданным идентификатором reference',
}

lines_descriptions = {
    'get': 'Получить товарную позицию с заданными идентификаторами order_id и line_item',
    'post': 'Создать в базе данных новую товарную позицию',
    'put': 'Обновить в базе данных товарную позицию с заданными идентификаторами order_id и line_item',
    'delete': 'Удалить из базы данных товарную позицию с заданными идентификаторами order_id и line_item',
}

allocate_descriptions = {
    'get': 'Получить из базы данных бухту, в которой размещена товарная позиция '
           'с заданными идентификаторами order_id и line_item',
    'post': 'Разместить товарную позицию в бухте',
    'delete': 'Отменить размещение в бухте товарной позиции '
              'с заданными идентификаторами order_id и line_item',
}


coils_request_examples = [
    OpenApiExample(name='Пример 1',
                   summary='Бухта-001 в базе данных, в ней не размещены товарные позиции',
                   value={"reference": "Бухта-001",
                          "product_id": "АВВГ_2х2,5",
                          "quantity": 200,
                          "recommended_balance": 12,
                          "acceptable_loss": 2}),
    OpenApiExample(name='Пример 2',
                   summary='Бухта-002 в базе данных, в ней не размещены товарные позиции',
                   value={"reference": "Бухта-002",
                          "product_id": "АВВГ_4х16",
                          "quantity": 150,
                          "recommended_balance": 20,
                          "acceptable_loss": 5}),
    OpenApiExample(name='Пример 3',
                   summary='Бухта-003 в базе данных, в ней размещены товарные позиции',
                   value={"reference": "Бухта-003",
                          "product_id": "АВВГ_2х2,5",
                          "quantity": 100,
                          "recommended_balance": 12,
                          "acceptable_loss": 2}),
    OpenApiExample(name='Пример 4',
                   summary='Бухта-004 в базе данных, в ней размещены товарные позиции',
                   value={"reference": "Бухта-004",
                          "product_id": "АВВГ_4х16",
                          "quantity": 70,
                          "recommended_balance": 15,
                          "acceptable_loss": 5}),
    OpenApiExample(name='Пример 5',
                   summary='Бухта-005 не в базе данных',
                   value={"reference": "Бухта-005",
                          "product_id": "АВВГ_2х2,5",
                          "quantity": 50,
                          "recommended_balance": 8,
                          "acceptable_loss": 2}),
    OpenApiExample(name='Пример 6',
                   summary='Бухта-006 не в базе данных',
                   value={"reference": "Бухта-006",
                          "product_id": "АВВГ_2х2,5",
                          "quantity": 60,
                          "recommended_balance": 8,
                          "acceptable_loss": 2}),
    OpenApiExample(name='Пример 7',
                   summary='Бухта-007 не в базе данных',
                   value={"reference": "Бухта-007",
                          "product_id": "АВВГ_4х16",
                          "quantity": 60,
                          "recommended_balance": 15,
                          "acceptable_loss": 5}),
    OpenApiExample(name='Пример 8',
                   summary='Бухта-008 не в базе данных',
                   value={"reference": "Бухта-008",
                          "product_id": "АВВГ_4х16",
                          "quantity": 50,
                          "recommended_balance": 15,
                          "acceptable_loss": 5}),
]

lines_request_examples = [
    OpenApiExample(name='Пример 1',
                   summary='Товарная позиция (Заказ-001, Позиция-001) в базе данных, не размещенная в бухте',
                   value={"order_id": "Заказ-001",
                          "line_item": "Позиция-001",
                          "product_id": "АВВГ_2х2,5",
                          "quantity": 24}),
    OpenApiExample(name='Пример 2',
                   summary='Товарная позиция (Заказ-002, Позиция-003) в базе данных, не размещенная в бухте',
                   value={"order_id": "Заказ-002",
                          "line_item": "Позиция-003",
                          "product_id": "АВВГ_4х16",
                          "quantity": 50}),
    OpenApiExample(name='Пример 3',
                   summary='Товарная позиция (Заказ-003, Позиция-002) в базе данных, размещенная в бухте',
                   value={"order_id": "Заказ-003",
                          "line_item": "Позиция-002",
                          "product_id": "АВВГ_2х2,5",
                          "quantity": 17}),
    OpenApiExample(name='Пример 4',
                   summary='Товарная позиция (Заказ-004, Позиция-004) в базе данных, размещенная в бухте',
                   value={"order_id": "Заказ-004",
                          "line_item": "Позиция-004",
                          "product_id": "АВВГ_4х16",
                          "quantity": 45}),
    OpenApiExample(name='Пример 5',
                   summary='Товарная позиция (Заказ-005, Позиция-001) не в базе данных',
                   value={"order_id": "Заказ-005",
                          "line_item": "Позиция-001",
                          "product_id": "АВВГ_2х2,5",
                          "quantity": 25}),
    OpenApiExample(name='Пример 6',
                   summary='Товарная позиция (Заказ-006, Позиция-004) не в базе данных',
                   value={"order_id": "Заказ-006",
                          "line_item": "Позиция-004",
                          "product_id": "АВВГ_2х2,5",
                          "quantity": 14}),
    OpenApiExample(name='Пример 7',
                   summary='Товарная позиция (Заказ-007, Позиция-005) не в базе данных',
                   value={"order_id": "Заказ-007",
                          "line_item": "Позиция-005",
                          "product_id": "АВВГ_4х16",
                          "quantity": 40}),
    OpenApiExample(name='Пример 8',
                   summary='Товарная позиция (Заказ-008, Позиция-003) не в базе данных',
                   value={"order_id": "Заказ-008",
                          "line_item": "Позиция-003",
                          "product_id": "АВВГ_4х16",
                          "quantity": 65}),
]


coils_reference_request_examples = [
    OpenApiExample(name='Пример 1',
                   summary='Идентификатор Бухты-001 в базе данных, в ней не размещены товарные позиции',
                   value="Бухта-001"),
    OpenApiExample(name='Пример 2',
                   summary='Идентификатор Бухты-002 в базе данных, в ней не размещены товарные позиции',
                   value="Бухта-002"),
    OpenApiExample(name='Пример 3',
                   summary='Идентификатор Бухты-003 в базе данных, в ней размещены товарные позиции',
                   value="Бухта-003"),
    OpenApiExample(name='Пример 4',
                   summary='Идентификатор Бухты-004 в базе данных, в ней размещены товарные позиции',
                   value="Бухта-004"),
    OpenApiExample(name='Пример 5',
                   summary='Идентификатор Бухты-005 не в базе данных',
                   value="Бухта-005"),
    OpenApiExample(name='Пример 6',
                   summary='Идентификатор Бухты-006 не в базе данных',
                   value="Бухта-006"),
    OpenApiExample(name='Пример 7',
                   summary='Идентификатор Бухты-007 не в базе данных',
                   value="Бухта-007"),
    OpenApiExample(name='Пример 8',
                   summary='Идентификатор Бухты-008 не в базе данных',
                   value="Бухта-008"),
]

lines_order_id_request_examples = [
    OpenApiExample(name='Пример 1',
                   summary='Идентификатор order_id товарной позиции (Заказ-001, Позиция-001) в базе данных,'
                           ' не размещенной в бухте',
                   value="Заказ-001"),
    OpenApiExample(name='Пример 2',
                   summary='Идентификатор order_id товарной позиции (Заказ-002, Позиция-003) в базе данных,'
                           ' не размещенной в бухте',
                   value="Заказ-002"),
    OpenApiExample(name='Пример 3',
                   summary='Идентификатор order_id товарной позиции (Заказ-003, Позиция-002) в базе данных,'
                           ' размещенной в бухте',
                   value="Заказ-003"),
    OpenApiExample(name='Пример 4',
                   summary='Идентификатор order_id товарной позиции (Заказ-004, Позиция-004) в базе данных,'
                           ' размещенной в бухте',
                   value="Заказ-004"),
    OpenApiExample(name='Пример 5',
                   summary='Идентификатор order_id товарной позиции (Заказ-005, Позиция-001) не в базе данных',
                   value="Заказ-005"),
    OpenApiExample(name='Пример 6',
                   summary='Идентификатор order_id товарной позиции (Заказ-006, Позиция-004) не в базе данных',
                   value="Заказ-006"),
    OpenApiExample(name='Пример 7',
                   summary='Идентификатор order_id товарной позиции (Заказ-007, Позиция-005) не в базе данных',
                   value="Заказ-007"),
    OpenApiExample(name='Пример 8',
                   summary='Идентификатор order_id товарной позиции (Заказ-008, Позиция-003) не в базе данных',
                   value="Заказ-008"),
]

lines_line_item_request_examples = [
    OpenApiExample(name='Пример 1',
                   summary='Идентификатор line_item товарной позиции (Заказ-001, Позиция-001) в базе данных,'
                           ' не размещенной в бухте',
                   value="Позиция-001"),
    OpenApiExample(name='Пример 2',
                   summary='Идентификатор line_item товарной позиции (Заказ-002, Позиция-003) в базе данных,'
                           ' не размещенной в бухте',
                   value="Позиция-003"),
    OpenApiExample(name='Пример 3',
                   summary='Идентификатор line_item товарной позиции (Заказ-003, Позиция-002) в базе данных,'
                           ' размещенной в бухте',
                   value="Позиция-002"),
    OpenApiExample(name='Пример 4',
                   summary='Идентификатор line_item товарной позиции (Заказ-004, Позиция-004) в базе данных,'
                           ' размещенной в бухте',
                   value="Позиция-004"),
    OpenApiExample(name='Пример 5',
                   summary='Идентификатор line_item товарной позиции (Заказ-005, Позиция-001) не в базе данных',
                   value="Позиция-001"),
    OpenApiExample(name='Пример 6',
                   summary='Идентификатор line_item товарной позиции (Заказ-006, Позиция-004) не в базе данных',
                   value="Позиция-004"),
    OpenApiExample(name='Пример 7',
                   summary='Идентификатор line_item товарной позиции (Заказ-007, Позиция-005) не в базе данных',
                   value="Позиция-005"),
    OpenApiExample(name='Пример 8',
                   summary='Идентификатор line_item товарной позиции (Заказ-008, Позиция-003) не в базе данных',
                   value="Позиция-003"),
]


coils_responses = {
    'get': {
        200: OpenApiResponse(description="Бухта с заданным идентификатором reference "
                                         "получена из базы данных"),
        404: OpenApiResponse(description="Бухта с заданным идентификатором reference "
                                         "отсутствует в базе данных"),
        500: OpenApiResponse(description="Возвращаемая бухта с заданным идентификатором reference "
                                         "не прошла валидацию"),
    },
    'post': {
        201: OpenApiResponse(description="Бухта создана в соответствии с телом запроса"),
        400: OpenApiResponse(description="Бухта в теле запроса не прошла валидацию"),
        409: OpenApiResponse(description="Бухта со значением идентификатора reference, "
                                         "полученным из тела запроса, уже существует в базе данных"),
    },
    'put': {
        200: OpenApiResponse(description="Бухта с заданным идентификатором reference "
                                         "обновлена в базе данных в соответствии с телом запроса. "
                                         "Получен список товарных позиций, которые перестали быть "
                                         "размещенными после обновления бухты"),
        404: OpenApiResponse(description="Бухта с заданным идентификатором reference "
                                         "отсутствует в базе данных"),
        400: OpenApiResponse(description="Бухта в теле запроса не прошла валидацию"),
    },
    'delete': {
        200: OpenApiResponse(description="Бухта с заданным идентификатором reference "
                                         "удалена из базы данных. Получен список товарных позиций, "
                                         "которые перестали быть размещенными после удаления бухты"),
        404: OpenApiResponse(description="Бухта с заданным идентификатором reference "
                                         "отсутствует в базе данных"),
    },
}

lines_responses = {
    'get': {
        200: OpenApiResponse(description="Товарная позиция с заданными идентификаторами "
                                         "order_id и line_item получена из базы данных"),
        404: OpenApiResponse(description="Товарная позиция с заданными идентификаторами "
                                         "order_id и line_item отсутствует в базе данных"),
        500: OpenApiResponse(description="Возвращаемая товарная позиция с заданными идентификаторами "
                                         "order_id и line_item не прошла валидацию"),
    },
    'post': {
        201: OpenApiResponse(description="Товарная позиция создана в соответствии с телом запроса"),
        409: OpenApiResponse(description="Товарная позиция со значениями идентификаторов order_id и line_item, "
                                         "полученными из тела запроса, уже существует в базе данных"),
        400: OpenApiResponse(description="Товарная позиция в теле запроса не прошла валидацию"),
    },
    'put': {
        200: OpenApiResponse(description="Товарная позиция с заданными идентификаторами order_id и line_item "
                                         "обновлена в базе данных в соответствии с телом запроса. "
                                         "Получена бухта, в которой будет размещена товарная позиция после "
                                         "ее обновления или 'поддельная' бухта, если до обновления "
                                         "товарная позиция не была размещена"),
        404: OpenApiResponse(description="Товарная позиция с заданными идентификаторами "
                                         "order_id и line_item отсутствует в базе данных"),
        400: OpenApiResponse(description="Товарная позиция в теле запроса не прошла валидацию"),
        500: OpenApiResponse(description="Возвращаемая после обновления товарной позиции бухта "
                                         "не прошла валидацию"),
    },
    'delete': {
        200: OpenApiResponse(description="Товарная позиция с заданными идентификаторами order_id и line_item "
                                         "удалена из базы данных. Получена бухта, в которой была размещена "
                                         "товарная позиция или 'поддельная' бухта, если до обновления "
                                         "товарная позиция не была размещена"),
        404: OpenApiResponse(description="Товарная позиция с заданными идентификаторами "
                                         "order_id и line_item отсутствует в базе данных"),
        500: OpenApiResponse(description="Возвращаемая после удаления товарной позиции бухта "
                                         "не прошла валидацию"),
    },
}

allocate_responses = {
    'get': {
        200: OpenApiResponse(description="Получена бухта, в которой размещена товарная позиция "
                                         "с заданными идентификаторами order_id и line_item, или "
                                         "'поддельная' бухта, если товарная позиция не была размещена"),
        404: OpenApiResponse(description="Товарная позиция с заданными идентификаторами "
                                         "order_id и line_item отсутствует в базе данных"),
        500: OpenApiResponse(description="Возвращаемая бухта, в которой размещена товарная позиция, "
                                         "не прошла валидацию"),
    },
    'post': {
        200: OpenApiResponse(description="Получена бухта, в которую размещена товарная позиция с "
                                         "идентификаторами order_id и line_item, полученными из тела запроса"),
        404: OpenApiResponse(description="Товарная позиция с идентификаторами order_id и line_item, "
                                         "полученными из тела запроса, отсутствует в базе данных"),
        422: OpenApiResponse(description="Количество материала в каждой из бухт недостаточно, чтобы "
                                         "разместить товарную позицию"),
        500: OpenApiResponse(description="Возвращаемая бухта, в которой размещена товарная позиция, "
                                         "не прошла валидацию"),
    },
    'delete': {
        200: OpenApiResponse(description="Товарная позиция с заданными идентификаторами order_id и line_item "
                                         "перестала быть размещена в бухте. Получена бухта, в которой "
                                         "товарная позиция была размещена, или 'поддельная' бухта, если "
                                         "товарная позиция не была размещена"),
        404: OpenApiResponse(description="Товарная позиция с заданными идентификаторами order_id и line_item "
                                         "отсутствует в базе данных"),
        500: OpenApiResponse(description="Возвращаемая бухта, в которой была размещена товарная позиция, "
                                         "не прошла валидацию"),
    },
}
