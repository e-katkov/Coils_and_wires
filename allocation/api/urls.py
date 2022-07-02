from django.urls import path

from allocation.api import api_views

urlpatterns = [
    path('coils', api_views.Coil.as_view()),
    path('coils/<str:reference>', api_views.CoilDetail.as_view()),
    path('orderlines', api_views.OrderLine.as_view()),
    path('orderlines/<str:order_id>/<str:line_item>', api_views.OrderLineDetail.as_view()),
    path('allocate', api_views.Allocate.as_view()),
    path('allocate/<str:order_id>/<str:line_item>', api_views.AllocateDetail.as_view()),
]
