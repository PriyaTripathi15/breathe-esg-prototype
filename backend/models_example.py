from django.db import models
from django.contrib.auth.models import User

class Tenant(models.Model):
    name = models.CharField(max_length=255)

class DataSource(models.Model):
    SOURCE_TYPES = [
        ("sap", "SAP"),
        ("utility", "Utility"),
        ("travel", "Travel")
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    source_type = models.CharField(max_length=50)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    original_filename = models.CharField(max_length=255)

class RawRecord(models.Model):
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE)
    raw_data = models.JSONField()

class NormalizedEmissionRecord(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    scope = models.CharField(max_length=20)
    category = models.CharField(max_length=100)
    quantity = models.FloatField()
    normalized_unit = models.CharField(max_length=50)
    co2e_kg = models.FloatField()
    review_status = models.CharField(max_length=20, default="pending")