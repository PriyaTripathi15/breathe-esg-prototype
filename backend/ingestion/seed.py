from __future__ import annotations

import hashlib
import random
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import EmissionRecord, RawRecord, SourceBatch, Tenant


AIRPORTS = {
    "DEL": {"city": "Delhi", "lat": 28.5562, "lon": 77.1000},
    "BLR": {"city": "Bengaluru", "lat": 13.1986, "lon": 77.7066},
    "BOM": {"city": "Mumbai", "lat": 19.0896, "lon": 72.8656},
    "HYD": {"city": "Hyderabad", "lat": 17.2403, "lon": 78.4294},
    "MAA": {"city": "Chennai", "lat": 12.9941, "lon": 80.1709},
    "CCU": {"city": "Kolkata", "lat": 22.6520, "lon": 88.4467},
}


def _decimal(value: float | int | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.001"))


def _hash_payload(payload: dict) -> str:
    return hashlib.sha1(str(sorted(payload.items())).encode("utf-8")).hexdigest()


def _distance_between(origin: str, destination: str) -> float:
    first = AIRPORTS[origin]
    second = AIRPORTS[destination]
    from math import asin, cos, radians, sin, sqrt

    radius_km = 6371.0
    lat1 = radians(first["lat"])
    lat2 = radians(second["lat"])
    dlat = radians(second["lat"] - first["lat"])
    dlon = radians(second["lon"] - first["lon"])
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return radius_km * (2 * asin(sqrt(a)))


def _sap_row(rng: random.Random, index: int):
    fuel_rows = index % 2 == 0
    if fuel_rows:
        fuel_type = rng.choice(["Diesel", "Natural Gas", "Petrol"])
        unit = rng.choice(["L", "gal", "m3"])
        quantity = rng.uniform(120, 1800)
        plant_code = f"PLANT_{rng.randint(100, 199)}"
        payload = {
            "Buchungsdatum": (date(2026, 1, 1) + timedelta(days=index % 27)).strftime("%d.%m.%Y"),
            "Werk": plant_code,
            "Kraftstoff": fuel_type,
            "Menge": round(quantity, 2),
            "Einheit": unit,
            "Kostenstelle": f"CC-{rng.randint(1000, 1999)}",
            "Lieferant": rng.choice(["Shell", "BP", "TotalEnergies"]),
        }
        if fuel_type == "Natural Gas":
            normalized_unit = "kWh"
            if unit == "m3":
                normalized_quantity = quantity * 10.55
            elif unit == "gal":
                normalized_quantity = quantity * 3.78541 * 8.9
            else:
                normalized_quantity = quantity * 9.8
            co2e = normalized_quantity * 0.183
            category = "stationary_combustion"
            scope = "1"
            label = f"Natural gas at {plant_code}"
            suspicious_reason = "" if quantity < 1500 else "Consumption spike versus trailing average"
        else:
            normalized_unit = "kWh"
            litres = quantity if unit == "L" else quantity * 3.78541
            if fuel_type == "Diesel":
                normalized_quantity = litres * 10.7
                co2e = litres * 2.68
            else:
                normalized_quantity = litres * 8.9
                co2e = litres * 2.31
            category = "mobile_combustion"
            scope = "1"
            label = f"{fuel_type} at {plant_code}"
            suspicious_reason = "" if quantity < 1400 else "High fuel volume needs approval"

        review_status = "flagged" if suspicious_reason else ("approved" if index % 5 == 0 else "pending")
        return payload, scope, category, label, quantity, unit, normalized_quantity, normalized_unit, co2e, suspicious_reason, review_status, plant_code, ""

    quantity = rng.uniform(60, 900)
    unit = rng.choice(["kg", "EA", "tonne"])
    payload = {
        "Buchungsdatum": (date(2026, 1, 1) + timedelta(days=index % 27)).strftime("%d.%m.%Y"),
        "Werk": f"PLANT_{rng.randint(100, 199)}",
        "Material": rng.choice(["Office Paper", "Packaging", "IT Hardware", "Cleaning Supplies"]),
        "Menge": round(quantity, 2),
        "Einheit": unit,
        "Kostenstelle": f"CC-{rng.randint(2000, 2999)}",
        "Lieferant": rng.choice(["Staples", "Grainger", "Amazon Business", "Viking"]),
    }
    if unit == "tonne":
        normalized_quantity = quantity * 1000
    elif unit == "EA":
        normalized_quantity = quantity * 2.5
    else:
        normalized_quantity = quantity
    normalized_unit = "kg"
    co2e = normalized_quantity * 0.62
    suspicious_reason = "" if quantity < 800 else "Large procurement line item"
    review_status = "flagged" if suspicious_reason else ("approved" if index % 6 == 0 else "pending")
    return payload, "3", "purchased_goods_and_services", payload["Material"], quantity, unit, normalized_quantity, normalized_unit, co2e, suspicious_reason, review_status, payload["Werk"], payload["Lieferant"]


def _utility_row(rng: random.Random, index: int):
    start_date = date(2026, 1, 1) + timedelta(days=index * 28)
    end_date = start_date + timedelta(days=rng.choice([27, 28, 29, 30, 31]))
    kwh = rng.uniform(4500, 28000)
    billing_days = (end_date - start_date).days
    payload = {
        "meter_id": f"MTR-{rng.randint(1000, 1999)}",
        "billing_period_start": start_date.isoformat(),
        "billing_period_end": end_date.isoformat(),
        "read_type": rng.choice(["actual", "estimated"]),
        "kwh": round(kwh, 2),
        "cost": round(kwh * rng.uniform(0.09, 0.19), 2),
        "currency": "USD",
        "tariff": rng.choice(["TOU-A", "Flat-01", "Demand-Plus"]),
        "facility": rng.choice(["HQ", "Warehouse", "R&D", "Call Center"]),
    }
    suspicious_reason = "" if billing_days in {28, 29, 30, 31} else "Billing period does not match portal export"
    if index % 7 == 0:
        suspicious_reason = "Estimated meter read requires reconciliation"
    review_status = "flagged" if suspicious_reason else ("approved" if index % 4 == 0 else "pending")
    co2e = kwh * 0.386
    return payload, "2", "purchased_electricity", payload["facility"], kwh, "kWh", kwh, "kWh", co2e, suspicious_reason, review_status, payload["meter_id"], payload["facility"]


def _travel_row(rng: random.Random, tenant_slug: str, index: int):
    category = rng.choice(["flight", "hotel", "ground_transport"])
    origin = rng.choice(list(AIRPORTS.keys()))
    destination = rng.choice([code for code in AIRPORTS.keys() if code != origin]) if category == "flight" else ""
    if category == "flight":
        distance_km = _distance_between(origin, destination)
        payload = {
            "trip_id": f"TRIP-{tenant_slug[:3].upper()}-{index:03d}",
            "employee_id": f"EMP-{rng.randint(100, 999)}",
            "category": "flight",
            "from_airport": origin,
            "to_airport": destination,
            "distance_km": round(distance_km, 1) if index % 3 else None,
            "cabin_class": rng.choice(["economy", "premium_economy", "business"]),
            "currency": "USD",
            "cost": round(rng.uniform(120, 1200), 2),
        }
        normalized_quantity = distance_km
        normalized_unit = "passenger_km"
        co2e = distance_km * rng.uniform(0.075, 0.11)
        suspicious_reason = "" if payload["distance_km"] else "Missing distance, derived from airport codes"
        activity_label = f"Flight {origin}-{destination}"
        scope = "3"
        source_quantity = distance_km
        source_unit = "km"
        reference_code = f"{origin}-{destination}"
        counterparty = "Concur"
    elif category == "hotel":
        nights = rng.randint(1, 7)
        payload = {
            "trip_id": f"TRIP-{tenant_slug[:3].upper()}-{index:03d}",
            "employee_id": f"EMP-{rng.randint(100, 999)}",
            "category": "hotel",
            "nights": nights,
            "city": rng.choice([airport["city"] for airport in AIRPORTS.values()]),
            "currency": "USD",
            "cost": round(rng.uniform(80, 350) * nights, 2),
            "hotel_chain": rng.choice(["Marriott", "Hilton", "Accor", "IHG"]),
        }
        normalized_quantity = nights
        normalized_unit = "room_night"
        co2e = nights * 14.8
        suspicious_reason = "" if nights <= 5 else "Extended stay above standard approval threshold"
        activity_label = f"Hotel stay in {payload['city']}"
        scope = "3"
        source_quantity = nights
        source_unit = "night"
        reference_code = payload["hotel_chain"]
        counterparty = payload["hotel_chain"]
    else:
        distance_km = rng.uniform(5, 180)
        payload = {
            "trip_id": f"TRIP-{tenant_slug[:3].upper()}-{index:03d}",
            "employee_id": f"EMP-{rng.randint(100, 999)}",
            "category": "ground_transport",
            "mode": rng.choice(["taxi", "rail", "rideshare"]),
            "distance_km": round(distance_km, 1),
            "currency": "USD",
            "cost": round(rng.uniform(12, 180), 2),
        }
        normalized_quantity = distance_km
        normalized_unit = "vehicle_km"
        co2e = distance_km * rng.uniform(0.08, 0.2)
        suspicious_reason = "" if distance_km < 140 else "Long ground transport leg"
        activity_label = f"{payload['mode'].title()} transfer"
        scope = "3"
        source_quantity = distance_km
        source_unit = "km"
        reference_code = payload["mode"]
        counterparty = payload["mode"].title()

    review_status = "flagged" if suspicious_reason else ("approved" if index % 5 == 0 else "pending")
    return payload, scope, f"{category}_travel", activity_label, source_quantity, source_unit, normalized_quantity, normalized_unit, co2e, suspicious_reason, review_status, reference_code, counterparty


def _build_record(source_type, payload, scope, category, activity_label, quantity, original_unit, normalized_quantity, normalized_unit, co2e, suspicious_reason, review_status, reference_code, counterparty, tenant, batch, raw_record, index):
    activity_date = date(2026, 1, 1) + timedelta(days=index % 27)
    source_created_at = timezone.make_aware(datetime.combine(activity_date, datetime.min.time())) + timedelta(hours=index % 18)
    return EmissionRecord(
        tenant=tenant,
        batch=batch,
        raw_record=raw_record,
        source_type=source_type,
        source_system=batch.source_system,
        source_filename=batch.original_filename,
        source_reference=batch.source_reference,
        external_id=raw_record.external_id,
        scope=scope,
        category=category,
        activity_label=activity_label,
        reference_code=reference_code,
        counterparty=counterparty,
        location_code=payload.get("Werk") or payload.get("facility") or payload.get("meter_id") or "",
        activity_date=activity_date,
        period_start=date.fromisoformat(payload.get("billing_period_start")) if payload.get("billing_period_start") else None,
        period_end=date.fromisoformat(payload.get("billing_period_end")) if payload.get("billing_period_end") else None,
        quantity=_decimal(quantity),
        original_unit=original_unit,
        normalized_quantity=_decimal(normalized_quantity),
        normalized_unit=normalized_unit,
        co2e_kg=_decimal(co2e),
        currency=payload.get("currency", ""),
        review_status=review_status,
        suspicious_reason=suspicious_reason,
        confidence_score=_decimal(0.82 if not suspicious_reason else 0.51),
        source_created_at=source_created_at,
        is_manual_override=False,
    )


def _create_batch(tenant, source_type: str, source_system: str, source_format: str, filename: str, reference: str, notes: str):
    return SourceBatch.objects.create(
        tenant=tenant,
        source_type=source_type,
        source_system=source_system,
        source_format=source_format,
        original_filename=filename,
        source_reference=reference,
        notes=notes,
    )


@transaction.atomic
def seed_demo_data():
    if Tenant.objects.exists():
        return

    rng = random.Random(42)
    tenants = [
        Tenant.objects.create(name="Northstar Mobility", slug="northstar-mobility"),
        Tenant.objects.create(name="Aster Retail Group", slug="aster-retail-group"),
    ]

    for tenant in tenants:
        sap_batch = _create_batch(
            tenant,
            "sap",
            "SAP ECC",
            "csv",
            f"{tenant.slug}-sap-export-2026-01.csv",
            f"sap::{tenant.slug}::2026-01",
            "Mixed SAP fuel and procurement export with German headers and inconsistent units.",
        )
        utility_batch = _create_batch(
            tenant,
            "utility",
            "Utility Portal",
            "csv",
            f"{tenant.slug}-utility-portal-2026-q1.csv",
            f"utility::{tenant.slug}::2026-q1",
            "Facility portal export with billing periods that do not always align to calendar months.",
        )
        travel_batch = _create_batch(
            tenant,
            "travel",
            "Concur",
            "json",
            f"{tenant.slug}-travel-export-2026-01.json",
            f"travel::{tenant.slug}::2026-01",
            "Corporate travel API payload shaped after Concur-style itinerary exports.",
        )

        for index in range(20):
            payload, scope, category, label, quantity, original_unit, normalized_quantity, normalized_unit, co2e, suspicious_reason, review_status, reference_code, counterparty = _sap_row(rng, index)
            raw_record = RawRecord.objects.create(
                batch=sap_batch,
                row_number=index + 1,
                external_id=f"SAP-{tenant.slug[:3].upper()}-{index + 1:03d}",
                payload=payload,
                source_hash=_hash_payload(payload),
            )
            record = _build_record("sap", payload, scope, category, label, quantity, original_unit, normalized_quantity, normalized_unit, co2e, suspicious_reason, review_status, reference_code, counterparty, tenant, sap_batch, raw_record, index)
            record.save()

        for index in range(20):
            payload, scope, category, label, quantity, original_unit, normalized_quantity, normalized_unit, co2e, suspicious_reason, review_status, reference_code, counterparty = _utility_row(rng, index)
            raw_record = RawRecord.objects.create(
                batch=utility_batch,
                row_number=index + 1,
                external_id=f"UTL-{tenant.slug[:3].upper()}-{index + 1:03d}",
                payload=payload,
                source_hash=_hash_payload(payload),
            )
            record = _build_record("utility", payload, scope, category, label, quantity, original_unit, normalized_quantity, normalized_unit, co2e, suspicious_reason, review_status, reference_code, counterparty, tenant, utility_batch, raw_record, index)
            record.save()

        for index in range(20):
            payload, scope, category, label, quantity, original_unit, normalized_quantity, normalized_unit, co2e, suspicious_reason, review_status, reference_code, counterparty = _travel_row(rng, tenant.slug, index)
            raw_record = RawRecord.objects.create(
                batch=travel_batch,
                row_number=index + 1,
                external_id=f"TRV-{tenant.slug[:3].upper()}-{index + 1:03d}",
                payload=payload,
                source_hash=_hash_payload(payload),
            )
            record = _build_record("travel", payload, scope, category, label, quantity, original_unit, normalized_quantity, normalized_unit, co2e, suspicious_reason, review_status, reference_code, counterparty, tenant, travel_batch, raw_record, index)
            record.save()
