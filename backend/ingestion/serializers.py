from rest_framework import serializers

from .models import EmissionRecord, RawRecord, SourceBatch, Tenant


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ["id", "name", "slug", "created_at"]


class SourceBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceBatch
        fields = [
            "id",
            "tenant",
            "source_type",
            "source_system",
            "source_format",
            "original_filename",
            "source_reference",
            "notes",
            "received_at",
        ]


class RawRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawRecord
        fields = ["id", "row_number", "external_id", "payload", "source_hash", "created_at"]


class EmissionRecordSerializer(serializers.ModelSerializer):
    raw_payload = serializers.SerializerMethodField()

    class Meta:
        model = EmissionRecord
        fields = [
            "id",
            "tenant",
            "batch",
            "raw_record",
            "raw_payload",
            "source_type",
            "source_system",
            "source_filename",
            "source_reference",
            "external_id",
            "scope",
            "category",
            "activity_label",
            "reference_code",
            "counterparty",
            "location_code",
            "activity_date",
            "period_start",
            "period_end",
            "quantity",
            "original_unit",
            "normalized_quantity",
            "normalized_unit",
            "co2e_kg",
            "currency",
            "review_status",
            "suspicious_reason",
            "confidence_score",
            "source_created_at",
            "is_manual_override",
            "notes",
            "edited_by_name",
            "edited_at",
            "approved_by_name",
            "approved_at",
            "locked_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "tenant",
            "batch",
            "raw_record",
            "raw_payload",
            "source_type",
            "source_system",
            "source_filename",
            "source_reference",
            "external_id",
            "scope",
            "category",
            "activity_label",
            "reference_code",
            "counterparty",
            "location_code",
            "activity_date",
            "period_start",
            "period_end",
            "quantity",
            "original_unit",
            "normalized_quantity",
            "normalized_unit",
            "co2e_kg",
            "currency",
            "confidence_score",
            "source_created_at",
            "is_manual_override",
            "created_at",
            "updated_at",
        ]

    def get_raw_payload(self, obj):
        return obj.raw_record.payload
