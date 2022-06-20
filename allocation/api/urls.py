from django.urls import path

from allocation.api.api_views import Coil, OrderLine, Allocate

urlpatterns = [
    path('coils', Coil.as_view()),
    path('coils/<str:reference>', Coil.as_view()),
    path('orderlines', OrderLine.as_view()),
    path('orderlines/<str:order_id>/<str:line_item>', OrderLine.as_view()),
    path('allocate', Allocate.as_view()),
    path('allocate/<str:order_id>/<str:line_item>', Allocate.as_view()),
]
