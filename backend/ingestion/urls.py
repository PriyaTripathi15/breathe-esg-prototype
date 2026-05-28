from django.http import JsonResponse
from django.urls import path

from .views import DashboardAPIView, LoginAPIView, MeAPIView, RecordDetailAPIView, RecordListAPIView, RegisterAPIView, TenantListAPIView


def health(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("health/", health),
    path("auth/login/", LoginAPIView.as_view()),
    path("auth/register/", RegisterAPIView.as_view()),
    path("auth/me/", MeAPIView.as_view()),
    path("tenants/", TenantListAPIView.as_view()),
    path("dashboard/", DashboardAPIView.as_view()),
    path("records/", RecordListAPIView.as_view()),
    path("records/<int:pk>/", RecordDetailAPIView.as_view()),
]
