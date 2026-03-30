"""
Tests for bridge/template_generator.py — reviewer pass.

Covers:
- Numbers in template match input: pass
- Hallucinated numbers detected: fail
- Small numbers (days, months) allowed
- Templates with no numbers pass
- Fallback template generation
"""

import pytest

from bridge.template_generator import (
    TemplateInput,
    review_template,
    _extract_numbers,
    _fallback_template,
)


# ─────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────

def _make_input(**overrides) -> TemplateInput:
    defaults = {
        "vehicle_id": "VH-0001",
        "cliente_id": "CL-0001",
        "modelo": "Ranger",
        "versao": "Limited",
        "km_estimado": 42000,
        "ultimo_servico_pago": "garantia",
        "churn_score": 90,
        "diferencial_competitivo": "torque: 51 kgfm; capacidade_carga: 785 kg",
    }
    defaults.update(overrides)
    return TemplateInput(**defaults)


# ─────────────────────────────────────────────────────────────
# _extract_numbers
# ─────────────────────────────────────────────────────────────

class TestExtractNumbers:
    def test_extracts_integers(self):
        assert "42000" in _extract_numbers("com 42000 km")

    def test_extracts_decimals(self):
        assert "51" in _extract_numbers("torque: 51 kgfm")
        assert "50.9" in _extract_numbers("torque: 50.9 kgfm")

    def test_extracts_comma_decimals(self):
        assert "59,2" in _extract_numbers("torque: 59,2 kgfm")

    def test_empty_string(self):
        assert _extract_numbers("") == set()

    def test_no_numbers(self):
        assert _extract_numbers("sem numeros aqui") == set()


# ─────────────────────────────────────────────────────────────
# review_template
# ─────────────────────────────────────────────────────────────

class TestReviewTemplate:
    def test_matching_numbers_pass(self):
        """Template with only input numbers should pass."""
        template = "Seu Ranger com 42000 km e 51 kgfm de torque."
        inp = _make_input()
        passed, notes = review_template(template, inp)
        assert passed is True

    def test_hallucinated_number_fails(self):
        """Template with a number not in input should fail."""
        template = "Seu Ranger com 42000 km e 999 cv de potencia."
        inp = _make_input()
        passed, notes = review_template(template, inp)
        assert passed is False
        assert "999" in notes

    def test_no_numbers_passes(self):
        """Template without numbers should pass."""
        template = "Ola! Seu Ranger merece uma revisao."
        inp = _make_input()
        passed, notes = review_template(template, inp)
        assert passed is True

    def test_small_numbers_allowed(self):
        """Numbers <= 100 (days, months) should not trigger failure."""
        template = "Nos proximos 15 dias, agende sua revisao do Ranger com 42000 km."
        inp = _make_input()
        passed, notes = review_template(template, inp)
        assert passed is True

    def test_milestone_numbers_allowed(self):
        """Common km milestones are whitelisted."""
        template = "Seu Ranger com 42000 km esta proximo da revisao de 40000 km."
        inp = _make_input()
        passed, notes = review_template(template, inp)
        assert passed is True

    def test_no_diferencial_passes(self):
        """Template with no diferencial should pass without numbers."""
        template = "Ola! Seu Territory precisa de revisao. Agende aqui: [link]"
        inp = _make_input(diferencial_competitivo=None, km_estimado=None)
        passed, notes = review_template(template, inp)
        assert passed is True


# ─────────────────────────────────────────────────────────────
# Fallback template
# ─────────────────────────────────────────────────────────────

class TestFallbackTemplate:
    def test_includes_modelo(self):
        inp = _make_input()
        text = _fallback_template(inp)
        assert "Ranger" in text

    def test_includes_km(self):
        inp = _make_input(km_estimado=42000)
        text = _fallback_template(inp)
        assert "42000" in text

    def test_includes_call_to_action(self):
        inp = _make_input()
        text = _fallback_template(inp)
        assert "[link]" in text

    def test_includes_diferencial(self):
        inp = _make_input(diferencial_competitivo="suspensao: Fox 2.5 Live Valve")
        text = _fallback_template(inp)
        assert "Fox" in text

    def test_no_diferencial_still_works(self):
        inp = _make_input(diferencial_competitivo=None)
        text = _fallback_template(inp)
        assert "Ranger" in text
        assert "[link]" in text
