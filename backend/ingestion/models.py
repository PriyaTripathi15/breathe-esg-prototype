from django.db import models


class Tenant(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class SourceBatch(models.Model):
    SOURCE_TYPES = [
        ("sap", "SAP"),
        ("utility", "Utility"),
        ("travel", "Travel"),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="batches")
    source_type = models.CharField(max_length=32, choices=SOURCE_TYPES)
    source_system = models.CharField(max_length=120)
    source_format = models.CharField(max_length=50)
    original_filename = models.CharField(max_length=255)
    source_reference = models.CharField(max_length=120)
    notes = models.TextField(blank=True)
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tenant.slug}:{self.source_type}:{self.original_filename}"


class RawRecord(models.Model):
    batch = models.ForeignKey(SourceBatch, on_delete=models.CASCADE, related_name="raw_records")
    row_number = models.PositiveIntegerField()
    external_id = models.CharField(max_length=120)
    payload = models.JSONField()
    source_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.batch_id}:{self.external_id}"


class EmissionRecord(models.Model):
    REVIEW_STATUSES = [
        ("pending", "Pending"),
        ("flagged", "Flagged"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("locked", "Locked"),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="records")
    batch = models.ForeignKey(SourceBatch, on_delete=models.CASCADE, related_name="records")
    raw_record = models.OneToOneField(RawRecord, on_delete=models.CASCADE, related_name="normalized_record")
    source_type = models.CharField(max_length=32)
    source_system = models.CharField(max_length=120)
    source_filename = models.CharField(max_length=255)
    source_reference = models.CharField(max_length=120)
    external_id = models.CharField(max_length=120)
    scope = models.CharField(max_length=20)
    category = models.CharField(max_length=120)
    activity_label = models.CharField(max_length=120)
    reference_code = models.CharField(max_length=120, blank=True)
    counterparty = models.CharField(max_length=120, blank=True)
    location_code = models.CharField(max_length=120, blank=True)
    activity_date = models.DateField()
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    original_unit = models.CharField(max_length=32)
    normalized_quantity = models.DecimalField(max_digits=14, decimal_places=3)
    normalized_unit = models.CharField(max_length=32)
    co2e_kg = models.DecimalField(max_digits=14, decimal_places=3)
    currency = models.CharField(max_length=8, blank=True)
    review_status = models.CharField(max_length=20, choices=REVIEW_STATUSES, default="pending")
    suspicious_reason = models.CharField(max_length=255, blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    source_created_at = models.DateTimeField(null=True, blank=True)
    is_manual_override = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    edited_by_name = models.CharField(max_length=120, blank=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    approved_by_name = models.CharField(max_length=120, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.tenant.slug}:{self.category}:{self.external_id}"
