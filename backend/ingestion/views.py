from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .auth import create_demo_token, get_demo_user_from_request
from .models import EmissionRecord, Tenant
from .serializers import EmissionRecordSerializer, TenantSerializer


def require_demo_user(request):
    user = get_demo_user_from_request(request)
    if user is None:
        return None, Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
    return user, None


class LoginAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        password = request.data.get("password") or ""
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        token = create_demo_token(user)
        return Response(
            {
                "token": token,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.get_full_name(),
                },
            }
        )


class RegisterAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = (request.data.get("username") or request.data.get("email") or "").strip()
        email = (request.data.get("email") or username).strip()
        password = request.data.get("password") or ""
        full_name = (request.data.get("full_name") or "").strip()

        if not username:
            return Response({"detail": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not password:
            return Response({"detail": "Password is required."}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({"detail": "A user with this username already exists."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password)
        if full_name:
            first_name, _, last_name = full_name.partition(" ")
            user.first_name = first_name
            user.last_name = last_name
            user.save(update_fields=["first_name", "last_name"])

        token = create_demo_token(user)
        return Response(
            {
                "token": token,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.get_full_name() or user.username,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class MeAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user = get_demo_user_from_request(request)
        if user is None:
            return Response({"detail": "Unauthorized."}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.get_full_name(),
            }
        )


def resolve_tenant(request):
    tenant_slug = request.query_params.get("tenant")
    tenant = Tenant.objects.filter(slug=tenant_slug).first() if tenant_slug else None
    if tenant:
        return tenant
    return Tenant.objects.order_by("id").first()


class TenantListAPIView(APIView):
    def get(self, request):
        _user, error = require_demo_user(request)
        if error:
            return error
        tenants = Tenant.objects.order_by("name")
        return Response(TenantSerializer(tenants, many=True).data)


class DashboardAPIView(APIView):
    def get(self, request):
        _user, error = require_demo_user(request)
        if error:
            return error
        tenant = resolve_tenant(request)
        if tenant is None:
            return Response({"detail": "No tenants available."}, status=status.HTTP_404_NOT_FOUND)

        records = EmissionRecord.objects.filter(tenant=tenant)
        source_breakdown = list(
            records.values("source_type").annotate(count=Count("id"), co2e_kg=Sum("co2e_kg")).order_by("source_type")
        )
        scope_breakdown = list(records.values("scope").annotate(count=Count("id")).order_by("scope"))
        review_breakdown = list(records.values("review_status").annotate(count=Count("id")).order_by("review_status"))

        flagged_records = records.filter(review_status="flagged").order_by("-updated_at", "-id")[:5]
        pending_records = records.filter(review_status="pending").order_by("-updated_at", "-id")[:10]
        queue = list(flagged_records) + list(pending_records)

        summary = {
            "tenant": TenantSerializer(tenant).data,
            "totals": {
                "records": records.count(),
                "pending": records.filter(review_status="pending").count(),
                "flagged": records.filter(review_status="flagged").count(),
                "approved": records.filter(review_status="approved").count(),
                "locked": records.filter(review_status="locked").count(),
                "co2e_kg": float(records.aggregate(total=Sum("co2e_kg"))["total"] or 0),
            },
            "source_breakdown": source_breakdown,
            "scope_breakdown": scope_breakdown,
            "review_breakdown": review_breakdown,
            "queue": EmissionRecordSerializer(queue, many=True).data,
            "latest_records": EmissionRecordSerializer(records.order_by("-updated_at")[:8], many=True).data,
        }
        return Response(summary)


class RecordListAPIView(APIView):
    def get(self, request):
        _user, error = require_demo_user(request)
        if error:
            return error
        tenant = resolve_tenant(request)
        if tenant is None:
            return Response({"results": []})

        records = EmissionRecord.objects.filter(tenant=tenant)
        status_filter = request.query_params.get("status")
        source_filter = request.query_params.get("source_type")
        scope_filter = request.query_params.get("scope")
        search = request.query_params.get("search")

        if status_filter:
            records = records.filter(review_status=status_filter)
        if source_filter:
            records = records.filter(source_type=source_filter)
        if scope_filter:
            records = records.filter(scope=scope_filter)
        if search:
            records = records.filter(category__icontains=search) | records.filter(counterparty__icontains=search) | records.filter(reference_code__icontains=search)

        records = records.distinct().order_by("-updated_at", "-id")
        return Response({"results": EmissionRecordSerializer(records, many=True).data})


class RecordDetailAPIView(generics.RetrieveUpdateAPIView):
    queryset = EmissionRecord.objects.select_related("raw_record", "tenant", "batch")
    serializer_class = EmissionRecordSerializer

    def dispatch(self, request, *args, **kwargs):
        user, error = require_demo_user(request)
        if error:
            return error
        self.demo_user = user
        return super().dispatch(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save(edited_by_name=request.data.get("edited_by_name", "Analyst"), edited_at=timezone.now())

        review_status = request.data.get("review_status")
        if review_status == "approved":
            updated.approved_by_name = request.data.get("approved_by_name", request.data.get("edited_by_name", "Analyst"))
            updated.approved_at = timezone.now()
            updated.locked_at = timezone.now()
            updated.review_status = "approved"
            updated.save(update_fields=["approved_by_name", "approved_at", "locked_at", "review_status", "edited_at", "edited_by_name", "updated_at"])
        elif review_status == "locked":
            updated.locked_at = timezone.now()
            updated.review_status = "locked"
            updated.save(update_fields=["locked_at", "review_status", "edited_at", "edited_by_name", "updated_at"])

        return Response(self.get_serializer(updated).data)
