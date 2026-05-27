from django.contrib import admin

from .models import EmissionRecord, RawRecord, SourceBatch, Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")


@admin.register(SourceBatch)
class SourceBatchAdmin(admin.ModelAdmin):
    list_display = ("tenant", "source_type", "source_system", "original_filename", "received_at")
    list_filter = ("source_type", "tenant")
    search_fields = ("original_filename", "source_system")


@admin.register(RawRecord)
class RawRecordAdmin(admin.ModelAdmin):
    list_display = ("batch", "external_id", "row_number", "created_at")
    search_fields = ("external_id",)


@admin.register(EmissionRecord)
class EmissionRecordAdmin(admin.ModelAdmin):
    list_display = ("tenant", "source_type", "scope", "category", "review_status", "co2e_kg")
    list_filter = ("source_type", "scope", "review_status", "tenant")
    search_fields = ("category", "counterparty", "reference_code")
