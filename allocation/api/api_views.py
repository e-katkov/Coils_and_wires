from pydantic import BaseModel, ValidationError, Field
from rest_framework.response import Response
from rest_framework.views import APIView

from allocation.exceptions import exceptions
from allocation.services import services, unit_of_work


class CoilBaseModel(BaseModel):
    reference: str = Field(regex='Бухта')
    product_id: str
    quantity: int = Field(gt=0)
    recommended_balance: int = Field(gt=0)
    acceptable_loss: int = Field(gt=0)


class Coil(APIView):
    def post(self, request):
        try:
            input_data = CoilBaseModel.parse_raw(request.data)
        except ValidationError as e:
            return Response({"message": str(e)}, status=400)
        try:
            services.add_coil(
                input_data.reference,
                input_data.product_id,
                input_data.quantity,
                input_data.recommended_balance,
                input_data.acceptable_loss,
                unit_of_work.DjangoCoilUnitOfWork(),
            )
        except exceptions.DBCoilRecordAlreadyExist as e:
            return Response({"message": str(e)}, status=400)
        return Response({"message": "OK"}, status=200)


class OrderLine(APIView):
    pass