"""
Validator service — validates parsed parameters against reference ranges.

Wraps the pure domain logic (reference_ranges, unit_converter) with
a service interface that produces BloodParameter objects.
"""

import logging
import re
from typing import Dict, List, Optional

from ..models.blood_parameter import BloodParameter, ParameterStatus
from ..domain.reference_ranges import get_reference_range, normalize_parameter_name
from ..domain.unit_converter import convert_to_standard, get_standard_unit
from ..domain.report_interpreter import compute_deviation

logger = logging.getLogger(__name__)

_RANGE_RE = re.compile(r"^\s*(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)")


def _report_range(text, builtin: Optional[dict]) -> Optional[dict]:
    """
    Parse the reference range printed on the report ("13.0 - 17.0").

    Returns {"min", "max"} or None if absent, malformed, or implausible. A range is
    implausible when it differs from the built-in one by more than 3x on either
    bound (guards against OCR noise like a date being read as a range).
    """
    m = _RANGE_RE.match(str(text or ""))
    if not m:
        return None
    lo, hi = float(m.group(1)), float(m.group(2))
    if lo >= hi:
        return None
    if builtin and builtin["max"] > 0 and not (1 / 3 <= hi / builtin["max"] <= 3):
        return None
    return {"min": lo, "max": hi}


class ValidatorService:
    """
    Validates blood parameters against age/gender-adjusted reference ranges.
    Produces fully-populated BloodParameter objects.
    """

    def validate(
        self,
        raw_params: Dict[str, dict],
        age: Optional[int] = None,
        gender: Optional[str] = None,
    ) -> List[BloodParameter]:
        """
        Validate a dict of raw parsed parameters.

        Args:
            raw_params: Dict of param_name → {value, unit, reference_range?}
            age: Patient age (optional, for adjusted ranges)
            gender: Patient gender (optional, for adjusted ranges)

        Returns:
            List of validated BloodParameter objects with status and severity set.
        """
        validated = []

        for raw_name, data in raw_params.items():
            try:
                param = self._validate_single(raw_name, data, age, gender)
                validated.append(param)
            except Exception as e:
                logger.warning(f"Skipping parameter '{raw_name}': {e}")
                continue

        return validated

    def _validate_single(
        self,
        raw_name: str,
        data: dict,
        age: Optional[int],
        gender: Optional[str],
    ) -> BloodParameter:
        """Validate a single parameter."""
        canonical = normalize_parameter_name(raw_name)
        value = float(data.get("value", 0))
        unit = data.get("unit", "N/A")

        # Convert to standard unit if possible
        reported_value = value
        standard_unit = get_standard_unit(canonical)
        if standard_unit and unit != "N/A":
            value, unit = convert_to_standard(canonical, value, unit)

        # Reference range: the report's own range wins (it is what the lab used);
        # built-in age/gender range is the fallback. Skip the report range if the
        # value was unit-converted, since the printed range is in the original unit.
        builtin = get_reference_range(canonical, age=age, gender=gender)
        ref = None
        if value == reported_value:
            ref = _report_range(data.get("reference_range"), builtin)
        if ref:
            ref["unit"] = unit
        else:
            ref = builtin

        ref_min = ref_max = deviation = severity = None
        ref_range_str = data.get("reference_range")
        status = ParameterStatus.UNKNOWN

        if ref:
            ref_min = ref["min"]
            ref_max = ref["max"]
            ref_unit = ref.get("unit", unit)

            if value < ref_min:
                status = ParameterStatus.LOW
            elif value > ref_max:
                status = ParameterStatus.HIGH
            else:
                status = ParameterStatus.NORMAL

            deviation, severity = compute_deviation(value, ref_min, ref_max)

            # Check for critical values (> 50% deviation)
            if deviation > 50:
                status = ParameterStatus.CRITICAL

            ref_range_str = f"{ref_min} - {ref_max} {ref_unit}"

        return BloodParameter(
            name=canonical,
            value=round(value, 2),
            unit=unit,
            status=status,
            reference_range=ref_range_str,
            reference_min=ref_min,
            reference_max=ref_max,
            deviation_percent=deviation,
            severity=severity,
        )
