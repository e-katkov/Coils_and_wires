import json

from drf_spectacular.utils import OpenApiParameter, extend_schema

from pydantic import BaseModel, Field, ValidationError

from rest_framework.response import Response
from rest_framework.views import APIView

from allocation.domain.domain_logic import Coil, OrderLine
from allocation.exceptions import exceptions
from allocation.services import services, unit_of_work

from coils_and_wires import drf_spectacular


class CoilBaseModel(BaseModel):
    """
    Принимает данные для инициализации экземпляра класса, выполняет их синтаксический анализ и проверку.
    Возвращает экземпляр класса, поля которого соответствуют типам полей, определенных в классе.
    Генерирует ошибку ValidationError, возникающую в случае указанного несоответствия.
    """
    reference: str = Field(regex='^(Бухта|fake)')
    product_id: str
    quantity: int = Field(gt=0)
    recommended_balance: int = Field(gt=0)
    acceptable_loss: int = Field(gt=0)
    allocations: list = []


class OrderLineBaseModel(BaseModel):
    """
    Принимает данные для инициализации экземпляра класса, выполняет их синтаксический анализ и проверку.
    Возвращает экземпляр класса, поля которого соответствуют типам полей, определенных в классе.
    Генерирует ошибку ValidationError, возникающую в случае указанного несоответствия.
    """
    order_id: str = Field(regex='^Заказ')
    line_item: str = Field(regex='^Позиция')
    product_id: str
    quantity: int = Field(gt=0)


def serialize_coil_domain_instance_to_json(domain_instance: Coil) -> str:
    """
    Принимает бухту - экземпляр класса Coil доменной модели, создает соответствующий ей
    экземпляр класса CoilBaseModel, выполняя тем самым синтаксический анализ и проверку.
    Сериализует экземпляр класса в объект JSON и возвращает его.
    Экземпляры класса OrderLine доменной модели, находящиеся в allocations, также
    проверяются и сериализуются в объекты JSON.
    """
    model_instance = CoilBaseModel(
        reference=domain_instance.reference,
        product_id=domain_instance.product_id,
        quantity=domain_instance.initial_quantity,
        recommended_balance=domain_instance.recommended_balance,
        acceptable_loss=domain_instance.acceptable_loss,
        allocations=[serialize_order_line_domain_instance_to_json(line)
                     for line in domain_instance.allocations],
    )
    return model_instance.json(ensure_ascii=False)


def serialize_order_line_domain_instance_to_json(domain_instance: OrderLine) -> str:
    """
    Принимает товарную позицию - экземпляр класса OrderLine доменной модели,
    создает соответствующий ей экземпляр класса OrderLineBaseModel,
    выполняя тем самым синтаксический анализ и проверку.
    Сериализует экземпляр класса в объект JSON и возвращает его.
    """
    model_instance = OrderLineBaseModel(
        order_id=domain_instance.order_id,
        line_item=domain_instance.line_item,
        product_id=domain_instance.product_id,
        quantity=domain_instance.quantity,
    )
    return model_instance.json(ensure_ascii=False)


class CoilView(APIView):
    @extend_schema(
        tags=['Бухты'],
        description=drf_spectacular.coils_descriptions['post'],
        responses=drf_spectacular.coils_responses['post'],
        request=CoilBaseModel,
        examples=drf_spectacular.coils_request_examples,
    )
    def post(self, request):
        try:
            input_data = CoilBaseModel.parse_obj(request.data)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=400)
        try:
            services.add_a_coil(
                input_data.reference,
                input_data.product_id,
                input_data.quantity,
                input_data.recommended_balance,
                input_data.acceptable_loss,
                unit_of_work.DjangoCoilUnitOfWork(),
            )
        except exceptions.DBCoilRecordAlreadyExist as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=409)
        output_data = json.dumps({"message": "Created"})
        return Response(data=output_data, status=201)


class CoilDetailView(APIView):
    @extend_schema(
        tags=['Бухты'],
        description=drf_spectacular.coils_descriptions['get'],
        responses=drf_spectacular.coils_responses['get'],
        parameters=[
            OpenApiParameter(
                name='reference',
                location='path',
                description='Идентификатор бухты',
                examples=drf_spectacular.coils_reference_request_examples,
            ),
        ],
    )
    def get(self, request, **kwargs):
        reference = self.kwargs['reference']
        try:
            coil = services.get_a_coil(
                reference,
                unit_of_work.DjangoCoilUnitOfWork(),
            )
        except exceptions.DBCoilRecordDoesNotExist as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=404)
        try:
            output_data = serialize_coil_domain_instance_to_json(coil)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=500)
        return Response(data=output_data, status=200)

    @extend_schema(
        tags=['Бухты'],
        description=drf_spectacular.coils_descriptions['put'],
        responses=drf_spectacular.coils_responses['put'],
        request=CoilBaseModel,
        examples=drf_spectacular.coils_request_examples,
        parameters=[OpenApiParameter(
            name='reference',
            location='path',
            description='Идентификатор бухты',
            examples=drf_spectacular.coils_reference_request_examples,
        ),
        ],
    )
    def put(self, request, **kwargs):
        reference = self.kwargs['reference']
        try:
            input_data = CoilBaseModel.parse_obj(request.data)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=400)
        try:
            deallocated_lines = services.update_a_coil(
                reference,
                input_data.product_id,
                input_data.quantity,
                input_data.recommended_balance,
                input_data.acceptable_loss,
                unit_of_work.DjangoCoilUnitOfWork(),
            )
        except exceptions.DBCoilRecordDoesNotExist as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=404)
        serialized_deallocated_lines = \
            [serialize_order_line_domain_instance_to_json(line) for line in deallocated_lines]
        output_data = json.dumps(serialized_deallocated_lines, ensure_ascii=False)
        return Response(data=output_data, status=200)

    @extend_schema(
        tags=['Бухты'],
        description=drf_spectacular.coils_descriptions['delete'],
        responses=drf_spectacular.coils_responses['delete'],
        parameters=[
            OpenApiParameter(
                name='reference',
                location='path',
                description='Идентификатор бухты',
                examples=drf_spectacular.coils_reference_request_examples,
            ),
        ],
    )
    def delete(self, request, **kwargs):
        reference = self.kwargs['reference']
        try:
            deallocated_lines = services.delete_a_coil(
                reference,
                unit_of_work.DjangoCoilUnitOfWork(),
            )
        except exceptions.DBCoilRecordDoesNotExist as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=404)
        serialized_deallocated_lines = \
            [serialize_order_line_domain_instance_to_json(line) for line in deallocated_lines]
        output_data = json.dumps(serialized_deallocated_lines, ensure_ascii=False)
        return Response(data=output_data, status=200)


class OrderLineView(APIView):
    @extend_schema(
        tags=['Товарные позиции'],
        description=drf_spectacular.lines_descriptions['post'],
        responses=drf_spectacular.lines_responses['post'],
        request=OrderLineBaseModel,
        examples=drf_spectacular.lines_request_examples,
    )
    def post(self, request):
        try:
            input_data = OrderLineBaseModel.parse_obj(request.data)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=400)
        try:
            services.add_a_line(
                input_data.order_id,
                input_data.line_item,
                input_data.product_id,
                input_data.quantity,
                unit_of_work.DjangoOrderLineUnitOfWork(),
            )
        except exceptions.DBOrderLineRecordAlreadyExist as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=409)
        output_data = json.dumps({"message": "Created"})
        return Response(data=output_data, status=201)


class OrderLineDetailView(APIView):
    @extend_schema(
        tags=['Товарные позиции'],
        description=drf_spectacular.lines_descriptions['get'],
        responses=drf_spectacular.lines_responses['get'],
        parameters=[OpenApiParameter(name='order_id',
                                     location='path',
                                     description='Идентификатор заказа',
                                     examples=drf_spectacular.lines_order_id_request_examples),
                    OpenApiParameter(name='line_item',
                                     location='path',
                                     description='Номер товарной позиции в заказе',
                                     examples=drf_spectacular.lines_line_item_request_examples),
                    ],
    )
    def get(self, request, **kwargs):
        order_id = self.kwargs['order_id']
        line_item = self.kwargs['line_item']
        try:
            line = services.get_a_line(
                order_id,
                line_item,
                unit_of_work.DjangoOrderLineUnitOfWork(),
            )
        except exceptions.DBOrderLineRecordDoesNotExist as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=404)
        try:
            output_data = serialize_order_line_domain_instance_to_json(line)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=500)
        return Response(data=output_data, status=200)

    @extend_schema(
        tags=['Товарные позиции'],
        description=drf_spectacular.lines_descriptions['put'],
        responses=drf_spectacular.lines_responses['put'],
        request=OrderLineBaseModel,
        examples=drf_spectacular.lines_request_examples,
        parameters=[OpenApiParameter(name='order_id',
                                     location='path',
                                     description='Идентификатор заказа',
                                     examples=drf_spectacular.lines_order_id_request_examples),
                    OpenApiParameter(name='line_item',
                                     location='path',
                                     description='Номер товарной позиции в заказе',
                                     examples=drf_spectacular.lines_line_item_request_examples),
                    ],
    )
    def put(self, request, **kwargs):
        order_id = self.kwargs['order_id']
        line_item = self.kwargs['line_item']
        try:
            input_data = OrderLineBaseModel.parse_obj(request.data)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=400)
        try:
            allocation_coil = services.update_a_line(
                order_id,
                line_item,
                input_data.product_id,
                input_data.quantity,
                unit_of_work.DjangoOrderLineUnitOfWork(),
                unit_of_work.DjangoCoilUnitOfWork(),
            )
        except exceptions.DBOrderLineRecordDoesNotExist as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=404)
        try:
            output_data = serialize_coil_domain_instance_to_json(allocation_coil)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=500)
        return Response(data=output_data, status=200)

    @extend_schema(
        tags=['Товарные позиции'],
        description=drf_spectacular.lines_descriptions['delete'],
        responses=drf_spectacular.lines_responses['delete'],
        parameters=[OpenApiParameter(name='order_id',
                                     location='path',
                                     description='Идентификатор заказа',
                                     examples=drf_spectacular.lines_order_id_request_examples),
                    OpenApiParameter(name='line_item',
                                     location='path',
                                     description='Номер товарной позиции в заказе',
                                     examples=drf_spectacular.lines_line_item_request_examples),
                    ],
    )
    def delete(self, request, **kwargs):
        order_id = self.kwargs['order_id']
        line_item = self.kwargs['line_item']
        try:
            allocation_coil = services.delete_a_line(
                order_id,
                line_item,
                unit_of_work.DjangoOrderLineUnitOfWork(),
                unit_of_work.DjangoCoilUnitOfWork(),
            )
        except exceptions.DBOrderLineRecordDoesNotExist as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=404)
        try:
            output_data = serialize_coil_domain_instance_to_json(allocation_coil)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=500)
        return Response(data=output_data, status=200)


class AllocateView(APIView):
    @extend_schema(
        tags=['Размещение товарных позиций'],
        description=drf_spectacular.allocate_descriptions['post'],
        responses=drf_spectacular.allocate_responses['post'],
        request=CoilBaseModel,
        examples=drf_spectacular.lines_request_examples,
    )
    def post(self, request):
        order_id = request.data['order_id']
        line_item = request.data['line_item']
        try:
            coil = services.allocate(
                order_id,
                line_item,
                unit_of_work.DjangoOrderLineUnitOfWork(),
                unit_of_work.DjangoCoilUnitOfWork(),
            )
        except exceptions.DBOrderLineRecordDoesNotExist as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=404)
        except exceptions.OutOfStock as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=422)
        try:
            output_data = serialize_coil_domain_instance_to_json(coil)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=500)
        return Response(data=output_data, status=200)


class AllocateDetailView(APIView):
    @extend_schema(
        tags=['Размещение товарных позиций'],
        description=drf_spectacular.allocate_descriptions['get'],
        responses=drf_spectacular.allocate_responses['get'],
        parameters=[OpenApiParameter(name='order_id',
                                     location='path',
                                     description='Идентификатор заказа',
                                     examples=drf_spectacular.lines_order_id_request_examples),
                    OpenApiParameter(name='line_item',
                                     location='path',
                                     description='Номер товарной позиции в заказе',
                                     examples=drf_spectacular.lines_line_item_request_examples),
                    ],
    )
    def get(self, request, **kwargs):
        order_id = self.kwargs['order_id']
        line_item = self.kwargs['line_item']
        try:
            allocation_coil = services.get_an_allocation_coil(
                order_id,
                line_item,
                unit_of_work.DjangoOrderLineUnitOfWork(),
                unit_of_work.DjangoCoilUnitOfWork(),
            )
        except exceptions.DBOrderLineRecordDoesNotExist as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=404)
        try:
            output_data = serialize_coil_domain_instance_to_json(allocation_coil)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=500)
        return Response(data=output_data, status=200)

    @extend_schema(
        tags=['Размещение товарных позиций'],
        description=drf_spectacular.allocate_descriptions['delete'],
        responses=drf_spectacular.allocate_responses['delete'],
        parameters=[OpenApiParameter(name='order_id',
                                     location='path',
                                     description='Идентификатор заказа',
                                     examples=drf_spectacular.lines_order_id_request_examples),
                    OpenApiParameter(name='line_item',
                                     location='path',
                                     description='Номер товарной позиции в заказе',
                                     examples=drf_spectacular.lines_line_item_request_examples),
                    ],
    )
    def delete(self, request, **kwargs):
        order_id = self.kwargs['order_id']
        line_item = self.kwargs['line_item']
        try:
            allocation_coil = services.deallocate(
                order_id,
                line_item,
                unit_of_work.DjangoOrderLineUnitOfWork(),
                unit_of_work.DjangoCoilUnitOfWork(),
            )
        except exceptions.DBOrderLineRecordDoesNotExist as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=404)
        try:
            output_data = serialize_coil_domain_instance_to_json(allocation_coil)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=500)
        return Response(data=output_data, status=200)
