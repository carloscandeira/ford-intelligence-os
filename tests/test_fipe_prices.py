"""
Tests for scraper/fipe_prices.py — pure helpers (no network).

Covers:
- _price_to_int: parses "R$ 1.234,56" style strings
- _parse_year: extracts year, handles "Zero KM"
- _clean_versao: strips the model name from the version label
"""

from datetime import date

from scraper.fipe_prices import _clean_versao, _parse_year, _price_to_int


class TestPriceToInt:
    def test_full_brl_string(self):
        assert _price_to_int("R$ 219.990,00") == 219990

    def test_high_value(self):
        assert _price_to_int("R$ 495.991,00") == 495991

    def test_empty(self):
        assert _price_to_int("") == 0

    def test_no_digits(self):
        assert _price_to_int("R$ -") == 0


class TestParseYear:
    def test_plain_year(self):
        assert _parse_year("2026 Diesel") == 2026

    def test_zero_km_word(self):
        assert _parse_year("Zero KM") == date.today().year

    def test_no_year(self):
        assert _parse_year("Diesel") == 0


class TestCleanVersao:
    def test_strips_leading_model(self):
        assert _clean_versao("Ranger Raptor 3.0 V6", "Ranger") == "Raptor 3.0 V6"

    def test_strips_model_anywhere(self):
        assert _clean_versao("L200 Triton Savana 2.4", "Triton") == "L200 Savana 2.4"

    def test_case_insensitive(self):
        assert _clean_versao("AMAROK Comfor. 3.0", "Amarok") == "Comfor. 3.0"

    def test_never_returns_empty(self):
        # If stripping would empty the string, keep the original.
        assert _clean_versao("Ranger", "Ranger") == "Ranger"
