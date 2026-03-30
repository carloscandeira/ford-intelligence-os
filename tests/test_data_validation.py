"""
Tests for ingestion/load_data.py — data validation functions.

Covers:
- NULL normalization (Issue 4A)
- Numeric range validation
- Edge cases for Brazilian data formats
"""

import pytest

from ingestion.load_data import _normalize_null, _validate_numeric, RANGE_CHECKS


# ─────────────────────────────────────────────────────────────
# NULL normalization
# ─────────────────────────────────────────────────────────────

class TestNormalizeNull:
    def test_empty_string(self):
        assert _normalize_null("") is None

    def test_dash(self):
        assert _normalize_null("-") is None

    def test_em_dash(self):
        assert _normalize_null("—") is None

    def test_na_uppercase(self):
        assert _normalize_null("N/A") is None

    def test_na_lowercase(self):
        assert _normalize_null("n/a") is None

    def test_nd(self):
        assert _normalize_null("N/D") is None
        assert _normalize_null("nd") is None

    def test_null_string(self):
        assert _normalize_null("null") is None
        assert _normalize_null("None") is None

    def test_none_value(self):
        assert _normalize_null(None) is None

    def test_valid_value_passthrough(self):
        assert _normalize_null("400") == "400"
        assert _normalize_null("V6 3.0 Biturbo") == "V6 3.0 Biturbo"

    def test_whitespace_stripped(self):
        assert _normalize_null("  400  ") == "400"

    def test_whitespace_only_is_null(self):
        assert _normalize_null("   ") is None


# ─────────────────────────────────────────────────────────────
# Numeric validation
# ─────────────────────────────────────────────────────────────

class TestValidateNumeric:
    def test_none_value_passes(self):
        is_valid, val = _validate_numeric("potencia", None)
        assert is_valid is True
        assert val is None

    def test_valid_potencia(self):
        is_valid, val = _validate_numeric("potencia", "400")
        assert is_valid is True
        assert val == "400"

    def test_potencia_too_high(self):
        is_valid, val = _validate_numeric("potencia", "2000")
        assert is_valid is False
        assert val is None

    def test_potencia_too_low(self):
        is_valid, val = _validate_numeric("potencia", "10")
        assert is_valid is False
        assert val is None

    def test_torque_valid(self):
        is_valid, val = _validate_numeric("torque", "51")
        assert is_valid is True

    def test_torque_out_of_range(self):
        is_valid, val = _validate_numeric("torque", "600")
        assert is_valid is False

    def test_non_numeric_field_passthrough(self):
        """Fields not in RANGE_CHECKS should pass through."""
        is_valid, val = _validate_numeric("motor", "V6 3.0 Biturbo")
        assert is_valid is True
        assert val == "V6 3.0 Biturbo"

    def test_brazilian_comma_decimal(self):
        """Brazilian format uses comma as decimal separator."""
        is_valid, val = _validate_numeric("torque", "59,2")
        assert is_valid is True
        assert val == "59,2"

    def test_value_with_unit(self):
        """Value with unit suffix should still validate."""
        is_valid, val = _validate_numeric("potencia", "400 cv")
        assert is_valid is True

    def test_preco_valid(self):
        is_valid, val = _validate_numeric("preco_sugerido", "449990")
        assert is_valid is True

    def test_preco_too_low(self):
        is_valid, val = _validate_numeric("preco_sugerido", "1000")
        assert is_valid is False

    def test_all_range_checks_have_bounds(self):
        """Sanity: every field in RANGE_CHECKS has (low, high) tuple."""
        for campo, (lo, hi) in RANGE_CHECKS.items():
            assert lo < hi, f"{campo}: low ({lo}) >= high ({hi})"
