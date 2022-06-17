import json

from pydantic import BaseModel, ValidationError, Field
from rest_framework.response import Response
from rest_framework.views import APIView

from allocation.domain.domain_logic import Coil, OrderLine
from allocation.exceptions import exceptions
from allocation.services import services, unit_of_work


class CoilBaseModel(BaseModel):
    reference: str = Field(regex='^(Бухта|fake)')
    product_id: str
    quantity: int = Field(gt=0)
    recommended_balance: int = Field(gt=0)
    acceptable_loss: int = Field(gt=0)
    allocations: list = []


class OrderLineBaseModel(BaseModel):
    order_id: str = Field(regex='^Заказ')
    line_item: str = Field(regex='^Позиция')
    product_id: str
    quantity: int = Field(gt=0)


def serialize_coil_domain_instance_to_json(domain_instance: Coil) -> str:
    model_instance = CoilBaseModel(
        reference=domain_instance.reference,
        product_id=domain_instance.product_id,
        quantity=domain_instance.initial_quantity,
        recommended_balance=domain_instance.recommended_balance,
        acceptable_loss=domain_instance.acceptable_loss,
        allocations=[serialize_order_line_domain_instance_to_json(line) \
                     for line in domain_instance.allocations],
    )
    return model_instance.json(ensure_ascii=False)


def serialize_order_line_domain_instance_to_json(domain_instance: OrderLine) -> str:
    model_instance = OrderLineBaseModel(
        order_id=domain_instance.order_id,
        line_item=domain_instance.line_item,
        product_id=domain_instance.product_id,
        quantity=domain_instance.quantity
    )
    return model_instance.json(ensure_ascii=False)


class Coil(APIView):
    def post(self, request):
        try:
            input_data = CoilBaseModel.parse_raw(request.data)
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
            return Response(data=output_data, status=400)
        output_data = json.dumps({"message": "OK"})
        return Response(data=output_data, status=200)


class OrderLine(APIView):
    def post(self, request):
        try:
            input_data = OrderLineBaseModel.parse_raw(request.data)
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
            return Response(data=output_data, status=400)
        output_data = json.dumps({"message": "OK"})
        return Response(data=output_data, status=200)


class CoilDetail(APIView):
    def get(self, request, **kwargs):
        reference = self.kwargs['reference']
        try:
            coil = services.get_a_coil(
                reference,
                unit_of_work.DjangoCoilUnitOfWork()
            )
        except exceptions.DBCoilRecordDoesNotExist as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=400)
        try:
            output_data = serialize_coil_domain_instance_to_json(coil)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=500)
        return Response(data=output_data, status=200)

    def put(self, request, **kwargs):
        reference = self.kwargs['reference']
        try:
            input_data = CoilBaseModel.parse_raw(request.data)
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
            return Response(data=output_data, status=400)
        serialized_deallocated_lines = \
            [serialize_order_line_domain_instance_to_json(line) for line in deallocated_lines]
        output_data = json.dumps(serialized_deallocated_lines, ensure_ascii=False)
        return Response(data=output_data, status=200)


class OrderLineDetail(APIView):
    def get(self, request, **kwargs):
        order_id = self.kwargs['order_id']
        line_item = self.kwargs['line_item']
        try:
            line = services.get_a_line(
                order_id,
                line_item,
                unit_of_work.DjangoOrderLineUnitOfWork()
            )
        except exceptions.DBOrderLineRecordDoesNotExist as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=400)
        try:
            output_data = serialize_order_line_domain_instance_to_json(line)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=500)
        return Response(data=output_data, status=200)

    def put(self, request, **kwargs):
        order_id = self.kwargs['order_id']
        line_item = self.kwargs['line_item']
        try:
            input_data = OrderLineBaseModel.parse_raw(request.data)
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
            return Response(data=output_data, status=400)
        try:
            output_data = serialize_coil_domain_instance_to_json(allocation_coil)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=500)
        return Response(data=output_data, status=200)


class Allocate(APIView):
    def post(self, request):
        try:
            input_data = OrderLineBaseModel.parse_raw(request.data)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=400)
        try:
            coil = services.allocate(
                input_data.order_id,
                input_data.line_item,
                unit_of_work.DjangoOrderLineUnitOfWork(),
                unit_of_work.DjangoCoilUnitOfWork(),
            )
        except (exceptions.DBOrderLineRecordDoesNotExist, exceptions.OutOfStock) as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=400)
        try:
            output_data = serialize_coil_domain_instance_to_json(coil)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=500)
        return Response(data=output_data, status=200)
