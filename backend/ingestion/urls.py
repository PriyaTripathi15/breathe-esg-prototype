from django.http import JsonResponse
from django.urls import path

from .views import DashboardAPIView, RecordDetailAPIView, RecordListAPIView, TenantListAPIView


def health(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("health/", health),
    path("tenants/", TenantListAPIView.as_view()),
    path("dashboard/", DashboardAPIView.as_view()),
    path("records/", RecordListAPIView.as_view()),
    path("records/<int:pk>/", RecordDetailAPIView.as_view()),
]
