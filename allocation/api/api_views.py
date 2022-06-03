import json

from pydantic import BaseModel, ValidationError, Field
from rest_framework.response import Response
from rest_framework.views import APIView

from allocation.exceptions import exceptions
from allocation.services import services, unit_of_work


class CoilBaseModel(BaseModel):
    reference: str = Field(regex='^Бухта')
    product_id: str
    quantity: int = Field(gt=0)
    recommended_balance: int = Field(gt=0)
    acceptable_loss: int = Field(gt=0)


class OrderLineBaseModel(BaseModel):
    order_id: str = Field(regex='^Заказ')
    line_item: str = Field(regex='^Позиция')
    product_id: str
    quantity: int = Field(gt=0)


class Coil(APIView):
    def post(self, request):
        try:
            input_data = CoilBaseModel.parse_raw(request.data)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=400)
        try:
            services.add_coil(
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
        output_data = json.dumps({"message": "OK"}, ensure_ascii=False)
        return Response(data=output_data, status=200)


class OrderLine(APIView):
    def post(self, request):
        try:
            input_data = OrderLineBaseModel.parse_raw(request.data)
        except ValidationError as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=400)
        try:
            services.add_line(
                input_data.order_id,
                input_data.line_item,
                input_data.product_id,
                input_data.quantity,
                unit_of_work.DjangoOrderLineUnitOfWork(),
            )
        except exceptions.DBOrderLineRecordAlreadyExist as error:
            output_data = json.dumps({"message": str(error)}, ensure_ascii=False)
            return Response(data=output_data, status=400)
        output_data = json.dumps({"message": "OK"}, ensure_ascii=False)
        return Response(data=output_data, status=200)
