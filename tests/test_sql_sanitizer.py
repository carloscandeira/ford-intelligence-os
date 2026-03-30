"""
Tests for nl_query/sql_generator.py — SQL sanitizer.

Covers:
- Valid SELECT queries pass
- DDL/DML blocked (DROP, INSERT, UPDATE, DELETE, CREATE, ALTER)
- SQL injection patterns blocked
- Multiple statements blocked
- CTE (WITH) queries allowed
"""

import pytest

from nl_query.sql_generator import sanitize_sql


class TestSanitizeSQL:
    # ─── Valid queries ────────────────────────────────────────
    def test_simple_select_passes(self):
        ok, reason = sanitize_sql("SELECT * FROM vehicle_spec WHERE mercado = 'BR'")
        assert ok is True

    def test_select_with_join_passes(self):
        sql = """
            SELECT vs.marca, vs.modelo, vs.valor
            FROM vehicle_spec vs
            JOIN retention_vehicles rv ON vs.modelo = rv.modelo
            WHERE vs.mercado = 'BR'
        """
        ok, reason = sanitize_sql(sql)
        assert ok is True

    def test_cte_with_passes(self):
        sql = """
            WITH ford_specs AS (
                SELECT * FROM vehicle_spec WHERE marca = 'Ford'
            )
            SELECT * FROM ford_specs
        """
        ok, reason = sanitize_sql(sql)
        assert ok is True

    def test_select_with_subquery_passes(self):
        sql = """
            SELECT marca, modelo, valor
            FROM vehicle_spec
            WHERE valor > (SELECT AVG(CAST(valor AS FLOAT)) FROM vehicle_spec WHERE campo = 'potencia')
        """
        ok, reason = sanitize_sql(sql)
        assert ok is True

    # ─── DDL blocked ──────────────────────────────────────────
    def test_drop_table_blocked(self):
        ok, reason = sanitize_sql("DROP TABLE vehicle_spec")
        assert ok is False

    def test_create_table_blocked(self):
        ok, reason = sanitize_sql("CREATE TABLE evil (id INT)")
        assert ok is False

    def test_alter_table_blocked(self):
        ok, reason = sanitize_sql("ALTER TABLE vehicle_spec ADD COLUMN evil TEXT")
        assert ok is False

    def test_truncate_blocked(self):
        ok, reason = sanitize_sql("TRUNCATE vehicle_spec")
        assert ok is False

    # ─── DML blocked ──────────────────────────────────────────
    def test_insert_blocked(self):
        ok, reason = sanitize_sql("INSERT INTO vehicle_spec (marca) VALUES ('evil')")
        assert ok is False

    def test_update_blocked(self):
        ok, reason = sanitize_sql("UPDATE vehicle_spec SET valor = 'hacked'")
        assert ok is False

    def test_delete_blocked(self):
        ok, reason = sanitize_sql("DELETE FROM vehicle_spec")
        assert ok is False

    # ─── Injection patterns ───────────────────────────────────
    def test_multiple_statements_blocked(self):
        ok, reason = sanitize_sql("SELECT 1; DROP TABLE vehicle_spec")
        assert ok is False

    def test_sql_comment_injection_blocked(self):
        ok, reason = sanitize_sql("SELECT * FROM vehicle_spec -- DROP TABLE")
        assert ok is False

    def test_block_comment_injection_blocked(self):
        ok, reason = sanitize_sql("SELECT * FROM vehicle_spec /* evil */")
        assert ok is False

    def test_grant_blocked(self):
        ok, reason = sanitize_sql("GRANT ALL ON vehicle_spec TO evil")
        assert ok is False

    def test_revoke_blocked(self):
        ok, reason = sanitize_sql("REVOKE ALL ON vehicle_spec FROM public")
        assert ok is False

    # ─── Edge cases ───────────────────────────────────────────
    def test_empty_string_blocked(self):
        ok, reason = sanitize_sql("")
        assert ok is False

    def test_whitespace_only_blocked(self):
        ok, reason = sanitize_sql("   ")
        assert ok is False

    def test_random_text_blocked(self):
        ok, reason = sanitize_sql("hello world")
        assert ok is False
