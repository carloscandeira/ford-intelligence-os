"""
Tests for app/pages/specs_comparison.py — _merge_price_only_rows.

Covers:
- FIPE long-name price rows fold into the short-name spec vehicle
- 'Limited+' price does NOT merge into 'Limited' (token equality)
- price rows without a matching spec vehicle stay standalone
- most specific versao wins when several candidates match
"""

from app.pages.specs_comparison import _merge_price_only_rows


def _spec(potencia="397"):
    return {"potencia": (potencia, "cv"), "torque": ("59,4", "kgfm")}


def _preco(valor="495991"):
    return {"preco_fipe": (valor, "BRL")}


class TestMergePriceOnlyRows:
    def test_fipe_long_name_merges_into_spec_vehicle(self):
        data = {
            ("Ford", "Ranger", "Raptor"): _spec(),
            ("Ford", "Ranger", "Raptor 3.0 V6 Bi-Turbo 4WD AUT."): _preco(),
        }
        out = _merge_price_only_rows(data)
        assert ("Ford", "Ranger", "Raptor 3.0 V6 Bi-Turbo 4WD AUT.") not in out
        assert out[("Ford", "Ranger", "Raptor")]["preco_fipe"] == ("495991", "BRL")

    def test_limited_plus_does_not_merge_into_limited(self):
        data = {
            ("Ford", "Ranger", "Limited"): _spec("250"),
            ("Ford", "Ranger", "Limited+ 3.0 V6 4x4 CD TB Die Aut"): _preco("364172"),
        }
        out = _merge_price_only_rows(data)
        # 'Limited+' is a different trim — phantom must stay standalone
        assert ("Ford", "Ranger", "Limited+ 3.0 V6 4x4 CD TB Die Aut") in out
        assert "preco_fipe" not in out[("Ford", "Ranger", "Limited")]

    def test_unmatched_price_row_stays(self):
        data = {
            ("Toyota", "Hilux", "SRX"): _spec("204"),
            ("Toyota", "Hilux", "CD SRV 4x4 2.8 TDI Diesel Aut."): _preco("307249"),
        }
        out = _merge_price_only_rows(data)
        assert ("Toyota", "Hilux", "CD SRV 4x4 2.8 TDI Diesel Aut.") in out

    def test_most_specific_versao_wins(self):
        data = {
            ("Ford", "Ranger", "XL"): _spec("170"),
            ("Ford", "Ranger", "XL 4x4"): _spec("170"),
            ("Ford", "Ranger", "XL 2.0 4x4 CD Diesel Mec."): _preco("250550"),
        }
        out = _merge_price_only_rows(data)
        assert "preco_fipe" in out[("Ford", "Ranger", "XL 4x4")]
        assert "preco_fipe" not in out[("Ford", "Ranger", "XL")]

    def test_cross_modelo_naming_merges(self):
        # specs say modelo='L200 Triton'/versao='Savana'; FIPE says
        # modelo='Triton'/versao='L200 Savana 2.4 4x4 Die. Aut.'
        data = {
            ("Mitsubishi", "L200 Triton", "Savana"): _spec("205"),
            ("Mitsubishi", "Triton", "L200 Savana 2.4 4x4 Die. Aut."): _preco("233274"),
        }
        out = _merge_price_only_rows(data)
        assert ("Mitsubishi", "Triton", "L200 Savana 2.4 4x4 Die. Aut.") not in out
        assert out[("Mitsubishi", "L200 Triton", "Savana")]["preco_fipe"] == ("233274", "BRL")

    def test_existing_price_not_overwritten(self):
        data = {
            ("Ford", "Ranger", "Raptor"): {**_spec(), "preco_fipe": ("111", "BRL")},
            ("Ford", "Ranger", "Raptor 3.0 V6"): _preco("495991"),
        }
        out = _merge_price_only_rows(data)
        assert out[("Ford", "Ranger", "Raptor")]["preco_fipe"] == ("111", "BRL")
