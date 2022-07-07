from django.urls import path

from allocation.api import api_views

urlpatterns = [
    path('coils', api_views.CoilView.as_view()),
    path('coils/<str:reference>', api_views.CoilDetailView.as_view()),
    path('orderlines', api_views.OrderLineView.as_view()),
    path('orderlines/<str:order_id>/<str:line_item>', api_views.OrderLineDetailView.as_view()),
    path('allocate', api_views.AllocateView.as_view()),
    path('allocate/<str:order_id>/<str:line_item>', api_views.AllocateDetailView.as_view()),
]
