from django.urls import path

from allocation.api.api_views import Coil, OrderLine

urlpatterns = [
    path('coils', Coil.as_view()),
    path('orderlines', OrderLine.as_view()),
]
