#!/usr/bin/env python3
"""Quick smoke test of the eligibility engine (no server required)."""

from hospital_service import get_service

svc = get_service()

print("=" * 60)
print("FPL Table")
print("=" * 60)
print(svc.get_fpl_table())

print("\n" + "=" * 60)
print("Hospitals")
print("=" * 60)
for h in svc.list_hospitals():
    print(f"  - {h['hospital_id']}: {h['display_name']} (ceiling {h['eligibility_ceiling_fpl_pct']}%)")

print("\n" + "=" * 60)
print("Persona A – Maria Gonzalez (Piedmont)")
print("=" * 60)
r = svc.check_eligibility(
    hospital_id="piedmont",
    household_size=3,
    annual_income=28400,
    uninsured=True,
    georgia_resident=True,
    bill_amount=8750,
)
print(f"Eligible: {r['eligible']}")
print(f"Discount: {r['discount_pct']}%")
print(f"Responsibility: ${r['patient_responsibility']}")
print(f"Message: {r['message']}")

print("\n" + "=" * 60)
print("Persona B – Thompson Family (Emory)")
print("=" * 60)
r = svc.check_eligibility(
    hospital_id="emory",
    household_size=3,
    annual_income=70500,
    uninsured=True,
    bill_amount=22400,
)
print(f"Eligible: {r['eligible']}")
print(f"Discount: {r['discount_pct']}%")
print(f"Responsibility: ${r['patient_responsibility']}")
print(f"Message: {r['message']}")

print("\n" + "=" * 60)
print("Emory borderline (David – above 350%)")
print("=" * 60)
r = svc.check_eligibility(
    hospital_id="emory",
    household_size=1,
    annual_income=62000,
    uninsured=True,
    bill_amount=15600,
)
print(f"Eligible: {r['eligible']}")
print(f"Discount: {r['discount_pct']}%")
print(f"Responsibility: ${r['patient_responsibility']}")
print(f"Message: {r['message']}")

print("\n" + "=" * 60)
print("Grady example (eligible, no published $ amount)")
print("=" * 60)
r = svc.check_eligibility(
    hospital_id="grady",
    household_size=2,
    annual_income=35000,
    fulton_or_dekalb=True,
    bill_amount=12000,
)
print(f"Eligible: {r['eligible']}")
print(f"Discount: {r['discount_pct']}")
print(f"Responsibility: {r['patient_responsibility']}")
print(f"Message: {r['message']}")
print("Notes:", r["special_notes"])
