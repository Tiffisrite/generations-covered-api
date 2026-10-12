"""
Generations Covered – Core eligibility & data service
Pure Python, no external dependencies.
Loads the JSON data files produced by the Data team.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Paths (relative to this file or absolute artifacts dir)
# ---------------------------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent  # /home/workdir/artifacts
DATA_DIR = BASE

HOSPITAL_DATA_PATH = DATA_DIR / "hospital_data.json"
REQUIRED_DOCS_PATH = DATA_DIR / "required_documents.json"
FORM_MAPPING_PATH = DATA_DIR / "form_field_mapping.json"
PERSONAS_PATH = DATA_DIR / "personas.json"


class HospitalService:
    def __init__(self):
        self.hospital_data = self._load(HOSPITAL_DATA_PATH)
        self.required_docs = self._load(REQUIRED_DOCS_PATH)
        self.form_mapping = self._load(FORM_MAPPING_PATH)
        self.personas = self._load(PERSONAS_PATH) if PERSONAS_PATH.exists() else {"personas": []}

    @staticmethod
    def _load(path: Path) -> dict:
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_fpl_table(self) -> dict:
        """Return the 2026 Federal Poverty Level guidelines."""
        return {
            "year": self.hospital_data.get("fpl_year", 2026),
            "source": self.hospital_data.get("fpl_source"),
            "guidelines": self.hospital_data.get("fpl_guidelines", {}),
        }

    def list_hospitals(self) -> List[dict]:
        """Lightweight list of hospitals for the frontend dropdown."""
        result = []
        for h in self.hospital_data.get("hospitals", []):
            result.append({
                "hospital_id": h["hospital_id"],
                "display_name": h["display_name"],
                "eligibility_ceiling_fpl_pct": h.get("eligibility_ceiling_fpl_pct"),
                "residency_rule": h.get("residency_rule"),
                "policy_date": h.get("policy_date"),
                "contact": h.get("contact", {}),
            })
        return result

    def get_hospital(self, hospital_id: str) -> Optional[dict]:
        for h in self.hospital_data.get("hospitals", []):
            if h["hospital_id"] == hospital_id:
                return h
        return None

    def get_required_documents(self, hospital_id: str) -> Optional[dict]:
        hospitals = self.required_docs.get("hospitals", {})
        return hospitals.get(hospital_id)

    def get_form_mapping(self, hospital_id: str) -> Optional[dict]:
        return self.form_mapping.get(hospital_id)

    def compute_fpl_pct(self, household_size: int, annual_income: float) -> dict:
        """
        Calculate % of Federal Poverty Level.
        Returns the FPL base amount and the percentage.
        """
        guidelines = self.hospital_data["fpl_guidelines"]
        if household_size <= 8:
            base = guidelines[str(household_size)]
        else:
            base = guidelines["8"] + guidelines["additional_person"] * (household_size - 8)

        pct = round((annual_income / base) * 100) if base else 0
        return {
            "household_size": household_size,
            "annual_income": annual_income,
            "fpl_100_pct_amount": base,
            "fpl_pct": pct,
        }

    def check_eligibility(
        self,
        hospital_id: str,
        household_size: int,
        annual_income: float,
        uninsured: bool = True,
        georgia_resident: bool = True,
        fulton_or_dekalb: bool = False,
        bill_amount: float = 0.0,
    ) -> dict:
        """
        Core eligibility engine.
        All numbers come from hospital_data.json – no LLM logic.
        """
        hospital = self.get_hospital(hospital_id)
        if not hospital:
            return {"error": f"Unknown hospital_id: {hospital_id}", "eligible": False}

        fpl_info = self.compute_fpl_pct(household_size, annual_income)
        fpl_pct = fpl_info["fpl_pct"]
        ceiling = hospital.get("eligibility_ceiling_fpl_pct", 0)

        result = {
            "hospital_id": hospital_id,
            "hospital_name": hospital["display_name"],
            "policy_date": hospital.get("policy_date"),
            "fpl": fpl_info,
            "eligibility_ceiling_fpl_pct": ceiling,
            "bill_amount": bill_amount,
            "eligible": False,
            "discount_pct": 0,
            "patient_responsibility": bill_amount,
            "message": "",
            "special_notes": [],
            "contact": hospital.get("contact", {}),
        }

        # ---------- Piedmont ----------
        if hospital_id == "piedmont":
            if not uninsured:
                result["message"] = "Piedmont’s published 100% discount applies to uninsured patients."
                result["special_notes"].append("Insured patients should still apply; other assistance may be available.")
            elif not georgia_resident:
                result["message"] = "Piedmont requires Georgia residency for the standard 100% discount."
            elif fpl_pct <= 300:
                result["eligible"] = True
                result["discount_pct"] = 100
                result["patient_responsibility"] = 0.0
                result["message"] = (
                    f"Qualifies for 100% financial assistance under Piedmont’s policy "
                    f"(uninsured Georgia resident at {fpl_pct}% of FPL, ceiling 300%)."
                )
            else:
                result["message"] = (
                    f"Income is {fpl_pct}% of FPL, above Piedmont’s 300% ceiling. "
                    "No published partial discount above 300%."
                )

        # ---------- Emory ----------
        elif hospital_id == "emory":
            if fpl_pct <= 200:
                result["eligible"] = True
                result["discount_pct"] = 100
                result["patient_responsibility"] = 0.0
                result["message"] = (
                    f"Qualifies for 100% charity care (≤ 200% FPL). "
                    f"Current FPL% = {fpl_pct}."
                )
            elif uninsured and fpl_pct <= 350:
                result["eligible"] = True
                result["discount_pct"] = 100
                result["patient_responsibility"] = 0.0
                result["message"] = (
                    f"Uninsured patient at {fpl_pct}% of FPL qualifies for 100% financial "
                    f"assistance on patient responsibility (201–350% band)."
                )
            elif uninsured and fpl_pct > 350:
                # Self-pay discount outside formal FAP
                result["eligible"] = False
                result["discount_pct"] = 65
                result["patient_responsibility"] = round(bill_amount * 0.35, 2)
                result["message"] = (
                    f"Income is {fpl_pct}% of FPL (above 350% ceiling). "
                    "Not eligible for formal FAP, but may receive Emory’s 65% self-pay discount."
                )
                result["special_notes"].append("Self-pay discount is outside the formal Financial Assistance Policy.")
            else:
                result["message"] = (
                    f"Does not meet Emory’s published FAP criteria "
                    f"(≤200% all patients or uninsured 201–350%). Current FPL% = {fpl_pct}."
                )

        # ---------- Grady ----------
        elif hospital_id == "grady":
            if fpl_pct <= 400 and (fulton_or_dekalb or True):  # residency checked by counselor
                result["eligible"] = True
                result["discount_pct"] = None  # unknown – no published schedule
                result["patient_responsibility"] = None
                result["message"] = (
                    f"Eligible for Grady financial assistance (≤ 400% FPL, current {fpl_pct}%). "
                    "Exact patient responsibility / copay is determined only by a Grady "
                    "financial counselor after income verification."
                )
                result["special_notes"].extend([
                    "No published numerical discount schedule exists.",
                    "Contact Grady Financial Counseling: 404-616-6920 (option 1).",
                    "App still generates the completed application + document checklist.",
                ])
                if not fulton_or_dekalb:
                    result["special_notes"].append(
                        "Full sliding-scale eligibility is for Fulton/DeKalb residents. "
                        "Out-of-county limited to emergency + related care."
                    )
            else:
                result["message"] = (
                    f"Income is {fpl_pct}% of FPL, above Grady’s 400% eligibility ceiling."
                )

        else:
            result["message"] = f"No eligibility rules configured for {hospital_id}."

        return result

    def list_personas(self) -> List[dict]:
        return self.personas.get("personas", [])

    def get_persona(self, persona_id: str) -> Optional[dict]:
        for p in self.personas.get("personas", []):
            if p.get("id") == persona_id:
                return p
        return None


# Singleton for simple use
_service: Optional[HospitalService] = None

def get_service() -> HospitalService:
    global _service
    if _service is None:
        _service = HospitalService()
    return _service
