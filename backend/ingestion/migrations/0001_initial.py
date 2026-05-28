from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Tenant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("slug", models.SlugField(unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="SourceBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_type", models.CharField(choices=[("sap", "SAP"), ("utility", "Utility"), ("travel", "Travel")], max_length=32)),
                ("source_system", models.CharField(max_length=120)),
                ("source_format", models.CharField(max_length=50)),
                ("original_filename", models.CharField(max_length=255)),
                ("source_reference", models.CharField(max_length=120)),
                ("notes", models.TextField(blank=True)),
                ("received_at", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="batches", to="ingestion.tenant")),
            ],
        ),
        migrations.CreateModel(
            name="RawRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("row_number", models.PositiveIntegerField()),
                ("external_id", models.CharField(max_length=120)),
                ("payload", models.JSONField()),
                ("source_hash", models.CharField(max_length=128)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("batch", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="raw_records", to="ingestion.sourcebatch")),
            ],
        ),
        migrations.CreateModel(
            name="EmissionRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_type", models.CharField(max_length=32)),
                ("source_system", models.CharField(max_length=120)),
                ("source_filename", models.CharField(max_length=255)),
                ("source_reference", models.CharField(max_length=120)),
                ("external_id", models.CharField(max_length=120)),
                ("scope", models.CharField(max_length=20)),
                ("category", models.CharField(max_length=120)),
                ("activity_label", models.CharField(max_length=120)),
                ("reference_code", models.CharField(blank=True, max_length=120)),
                ("counterparty", models.CharField(blank=True, max_length=120)),
                ("location_code", models.CharField(blank=True, max_length=120)),
                ("activity_date", models.DateField()),
                ("period_start", models.DateField(blank=True, null=True)),
                ("period_end", models.DateField(blank=True, null=True)),
                ("quantity", models.DecimalField(decimal_places=3, max_digits=14)),
                ("original_unit", models.CharField(max_length=32)),
                ("normalized_quantity", models.DecimalField(decimal_places=3, max_digits=14)),
                ("normalized_unit", models.CharField(max_length=32)),
                ("co2e_kg", models.DecimalField(decimal_places=3, max_digits=14)),
                ("currency", models.CharField(blank=True, max_length=8)),
                ("review_status", models.CharField(choices=[("pending", "Pending"), ("flagged", "Flagged"), ("approved", "Approved"), ("rejected", "Rejected"), ("locked", "Locked")], default="pending", max_length=20)),
                ("suspicious_reason", models.CharField(blank=True, max_length=255)),
                ("confidence_score", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("source_created_at", models.DateTimeField(blank=True, null=True)),
                ("is_manual_override", models.BooleanField(default=False)),
                ("notes", models.TextField(blank=True)),
                ("edited_by_name", models.CharField(blank=True, max_length=120)),
                ("edited_at", models.DateTimeField(blank=True, null=True)),
                ("approved_by_name", models.CharField(blank=True, max_length=120)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("locked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("batch", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="records", to="ingestion.sourcebatch")),
                ("raw_record", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="normalized_record", to="ingestion.rawrecord")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="records", to="ingestion.tenant")),
            ],
            options={
                "ordering": ["-created_at", "-id"],
            },
        ),
    ]
