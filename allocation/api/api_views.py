import json
from typing import Any

from drf_spectacular.utils import OpenApiParameter, extend_schema
from pydantic import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from allocation.api import serializers
from allocation.exceptions import exceptions
from allocation.services import services, unit_of_work
from coils_and_wires import drf_spectacular


class CoilView(APIView):
    @extend_schema(
        tags=['Бухты'],
        description=drf_spectacular.coils_descriptions['post'],
        responses=drf_spectacular.coils_responses['post'],
        request=serializers.CoilBaseModel,
        examples=drf_spectacular.coils_request_examples,
    )
    def post(self, request: Request) -> Response:
        try:
            input_data = serializers.CoilBaseModel.parse_obj(request.data)
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
                unit_of_work.DjangoUnitOfWork(),
            )
        except exceptions.DBCoilRecordAlreadyExist as error:
            output_data = json.dumps({"message": error.message}, ensure_ascii=False)
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
    def get(self, request: Request, **kwargs: dict[str, Any]) -> Response:
        reference = self.kwargs['reference']
        try:
            coil = services.get_a_coil(
                reference,
                unit_of_work.DjangoUnitOfWork(),
            )
        except exceptions.DBCoilRecordDoesNotExist as error:
            output_data = json.dumps({"message": error.message}, ensure_ascii=False)
            return Response(data=output_data, status=404)
        try:
            output_data = serializers.serialize_coil_domain_instance_to_json(coil)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=403)
        return Response(data=output_data, status=200)

    @extend_schema(
        tags=['Бухты'],
        description=drf_spectacular.coils_descriptions['put'],
        responses=drf_spectacular.coils_responses['put'],
        request=serializers.CoilBaseModel,
        examples=drf_spectacular.coils_request_examples,
        parameters=[OpenApiParameter(
            name='reference',
            location='path',
            description='Идентификатор бухты',
            examples=drf_spectacular.coils_reference_request_examples,
        ),
        ],
    )
    def put(self, request: Request, **kwargs: dict[str, Any]) -> Response:
        reference = self.kwargs['reference']
        try:
            input_data = serializers.CoilBaseModel.parse_obj(request.data)
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
                unit_of_work.DjangoUnitOfWork(),
            )
        except exceptions.DBCoilRecordDoesNotExist as error:
            output_data = json.dumps({"message": error.message}, ensure_ascii=False)
            return Response(data=output_data, status=404)
        serialized_deallocated_lines = \
            [serializers.serialize_order_line_domain_instance_to_json(line) for line in deallocated_lines]
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
    def delete(self, request: Request, **kwargs: dict[str, Any]) -> Response:
        reference = self.kwargs['reference']
        try:
            deallocated_lines = services.delete_a_coil(
                reference,
                unit_of_work.DjangoUnitOfWork(),
            )
        except exceptions.DBCoilRecordDoesNotExist as error:
            output_data = json.dumps({"message": error.message}, ensure_ascii=False)
            return Response(data=output_data, status=404)
        serialized_deallocated_lines = \
            [serializers.serialize_order_line_domain_instance_to_json(line) for line in deallocated_lines]
        output_data = json.dumps(serialized_deallocated_lines, ensure_ascii=False)
        return Response(data=output_data, status=200)


class OrderLineView(APIView):
    @extend_schema(
        tags=['Товарные позиции'],
        description=drf_spectacular.lines_descriptions['post'],
        responses=drf_spectacular.lines_responses['post'],
        request=serializers.OrderLineBaseModel,
        examples=drf_spectacular.lines_request_examples,
    )
    def post(self, request: Request) -> Response:
        try:
            input_data = serializers.OrderLineBaseModel.parse_obj(request.data)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=400)
        try:
            services.add_a_line(
                input_data.order_id,
                input_data.line_item,
                input_data.product_id,
                input_data.quantity,
                unit_of_work.DjangoUnitOfWork(),
            )
        except exceptions.DBOrderLineRecordAlreadyExist as error:
            output_data = json.dumps({"message": error.message}, ensure_ascii=False)
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
    def get(self, request: Request, **kwargs: dict[str, Any]) -> Response:
        order_id = self.kwargs['order_id']
        line_item = self.kwargs['line_item']
        try:
            line = services.get_a_line(
                order_id,
                line_item,
                unit_of_work.DjangoUnitOfWork(),
            )
        except exceptions.DBOrderLineRecordDoesNotExist as error:
            output_data = json.dumps({"message": error.message}, ensure_ascii=False)
            return Response(data=output_data, status=404)
        try:
            output_data = serializers.serialize_order_line_domain_instance_to_json(line)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=403)
        return Response(data=output_data, status=200)

    @extend_schema(
        tags=['Товарные позиции'],
        description=drf_spectacular.lines_descriptions['put'],
        responses=drf_spectacular.lines_responses['put'],
        request=serializers.OrderLineBaseModel,
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
    def put(self, request: Request, **kwargs: dict[str, Any]) -> Response:
        order_id = self.kwargs['order_id']
        line_item = self.kwargs['line_item']
        try:
            input_data = serializers.OrderLineBaseModel.parse_obj(request.data)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=400)
        try:
            allocation_coil = services.update_a_line(
                order_id,
                line_item,
                input_data.product_id,
                input_data.quantity,
                unit_of_work.DjangoUnitOfWork(),
            )
        except exceptions.DBOrderLineRecordDoesNotExist as error:
            output_data = json.dumps({"message": error.message}, ensure_ascii=False)
            return Response(data=output_data, status=404)
        try:
            output_data = serializers.serialize_coil_domain_instance_to_json(allocation_coil)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=403)
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
    def delete(self, request: Request, **kwargs: dict[str, Any]) -> Response:
        order_id = self.kwargs['order_id']
        line_item = self.kwargs['line_item']
        try:
            allocation_coil = services.delete_a_line(
                order_id,
                line_item,
                unit_of_work.DjangoUnitOfWork(),
            )
        except exceptions.DBOrderLineRecordDoesNotExist as error:
            output_data = json.dumps({"message": error.message}, ensure_ascii=False)
            return Response(data=output_data, status=404)
        try:
            output_data = serializers.serialize_coil_domain_instance_to_json(allocation_coil)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=403)
        return Response(data=output_data, status=200)


class AllocateView(APIView):
    @extend_schema(
        tags=['Размещение товарных позиций'],
        description=drf_spectacular.allocate_descriptions['post'],
        responses=drf_spectacular.allocate_responses['post'],
        request=serializers.CoilBaseModel,
        examples=drf_spectacular.lines_request_examples,
    )
    def post(self, request: Request) -> Response:
        order_id = request.data['order_id']
        line_item = request.data['line_item']
        try:
            coil = services.allocate(
                order_id,
                line_item,
                unit_of_work.DjangoUnitOfWork(),
            )
        except exceptions.DBOrderLineRecordDoesNotExist as error:
            output_data = json.dumps({"message": error.message}, ensure_ascii=False)
            return Response(data=output_data, status=404)
        except exceptions.OutOfStock as error:
            output_data = json.dumps({"message": error.message}, ensure_ascii=False)
            return Response(data=output_data, status=422)
        try:
            output_data = serializers.serialize_coil_domain_instance_to_json(coil)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=403)
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
    def get(self, request: Request, **kwargs: dict[str, Any]) -> Response:
        order_id = self.kwargs['order_id']
        line_item = self.kwargs['line_item']
        try:
            allocation_coil = services.get_an_allocation_coil(
                order_id,
                line_item,
                unit_of_work.DjangoUnitOfWork(),
            )
        except exceptions.DBOrderLineRecordDoesNotExist as error:
            output_data = json.dumps({"message": error.message}, ensure_ascii=False)
            return Response(data=output_data, status=404)
        try:
            output_data = serializers.serialize_coil_domain_instance_to_json(allocation_coil)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=403)
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
    def delete(self, request: Request, **kwargs: dict[str, Any]) -> Response:
        order_id = self.kwargs['order_id']
        line_item = self.kwargs['line_item']
        try:
            allocation_coil = services.deallocate(
                order_id,
                line_item,
                unit_of_work.DjangoUnitOfWork(),
            )
        except exceptions.DBOrderLineRecordDoesNotExist as error:
            output_data = json.dumps({"message": error.message}, ensure_ascii=False)
            return Response(data=output_data, status=404)
        try:
            output_data = serializers.serialize_coil_domain_instance_to_json(allocation_coil)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=403)
        return Response(data=output_data, status=200)
