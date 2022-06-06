from django.urls import path

from allocation.api.api_views import Coil, OrderLine, CoilDetail, OrderLineDetail

urlpatterns = [
    path('coils', Coil.as_view()),
    path('orderlines', OrderLine.as_view()),
    path('coils/<str:reference>', CoilDetail.as_view()),
    path('orderlines/<str:order_id>/<str:line_item>', OrderLineDetail.as_view()),
]
