"""
Tests for PRAVAH core services: expression evaluator, SSRF protection, node registry.
"""
import pytest
from app.services.expression_evaluator import (
    resolve_template,
    evaluate_condition,
    resolve_config_expressions,
)
from app.core.ssrf_protection import validate_url_safe, SSRFViolationError
from app.services.node_registry import NODE_REGISTRY, get_all_nodes, get_nodes_by_category


# ============================================================
# Expression Evaluator Tests
# ============================================================

class TestExpressionEvaluator:
    def _ctx(self):
        return {
            "trigger": {"event": "content_created", "content_id": "c123"},
            "nodes": {
                "gen": {"text": "Hello World #SaaS", "hashtags": ["#SaaS", "#Tech"], "tokens_used": 300},
                "cond": {"match": True, "branch": "true"},
                "filter": {"is_valid": False},
            },
            "org": {"id": "org123", "name": "TestOrg"},
            "vars": {"my_counter": 5, "platform": "linkedin"},
        }

    def test_simple_node_reference(self):
        ctx = self._ctx()
        result = resolve_template("Post: {{nodes.gen.text}}", ctx)
        assert result == "Post: Hello World #SaaS"

    def test_trigger_reference(self):
        ctx = self._ctx()
        result = resolve_template("Content {{trigger.content_id}}", ctx)
        assert result == "Content c123"

    def test_org_reference(self):
        ctx = self._ctx()
        result = resolve_template("Org: {{org.name}}", ctx)
        assert result == "Org: TestOrg"

    def test_vars_reference(self):
        ctx = self._ctx()
        result = resolve_template("Count: {{vars.my_counter}}", ctx)
        assert result == "Count: 5"

    def test_multiple_expressions(self):
        ctx = self._ctx()
        result = resolve_template("{{org.name}} - {{nodes.gen.text}}", ctx)
        assert result == "TestOrg - Hello World #SaaS"

    def test_unresolved_expression_passthrough(self):
        ctx = self._ctx()
        result = resolve_template("{{nonexistent.field}}", ctx)
        # Should leave unresolved expression as-is (safe fallback)
        assert "{{" in result or result == ""

    def test_condition_equals(self):
        ctx = self._ctx()
        assert evaluate_condition("nodes.cond.match", "equals", "true", ctx) == True
        assert evaluate_condition("org.name", "equals", "TestOrg", ctx) == True
        assert evaluate_condition("org.name", "equals", "WrongName", ctx) == False

    def test_condition_contains(self):
        ctx = self._ctx()
        assert evaluate_condition("nodes.gen.text", "contains", "Hello", ctx) == True
        assert evaluate_condition("nodes.gen.text", "contains", "goodbye", ctx) == False

    def test_condition_is_not_empty(self):
        ctx = self._ctx()
        assert evaluate_condition("nodes.gen.text", "is_not_empty", "", ctx) == True
        assert evaluate_condition("nodes.nonexistent.field", "is_empty", "", ctx) == True

    def test_condition_greater_than(self):
        ctx = self._ctx()
        assert evaluate_condition("nodes.gen.tokens_used", "greater_than", "100", ctx) == True
        assert evaluate_condition("nodes.gen.tokens_used", "greater_than", "500", ctx) == False

    def test_condition_boolean_false(self):
        ctx = self._ctx()
        assert evaluate_condition("nodes.filter.is_valid", "equals", "false", ctx) == True

    def test_config_resolution(self):
        ctx = self._ctx()
        config = {
            "body": "{{nodes.gen.text}}",
            "platform": "{{vars.platform}}",
            "org_name": "{{org.name}}",
            "static_value": "no_template",
        }
        resolved = resolve_config_expressions(config, ctx)
        assert resolved["body"] == "Hello World #SaaS"
        assert resolved["platform"] == "linkedin"
        assert resolved["org_name"] == "TestOrg"
        assert resolved["static_value"] == "no_template"

    def test_disallowed_root_returns_empty(self):
        ctx = self._ctx()
        # External/system root should not resolve
        result = resolve_template("{{system.secret}}", ctx)
        assert "system.secret" in result or result == ""  # passthrough, not crash


# ============================================================
# SSRF Protection Tests
# ============================================================

class TestSSRFProtection:
    def test_public_url_allowed(self):
        # These should pass without raising
        validate_url_safe("https://api.openai.com/v1/models")
        validate_url_safe("https://openrouter.ai/api/v1/chat/completions")
        validate_url_safe("https://graph.facebook.com/v19.0/me")

    def test_localhost_blocked(self):
        with pytest.raises(SSRFViolationError):
            validate_url_safe("http://localhost:3000/api/internal")

    def test_127_loopback_blocked(self):
        with pytest.raises(SSRFViolationError):
            validate_url_safe("http://127.0.0.1:8000/admin")

    def test_aws_metadata_blocked(self):
        with pytest.raises(SSRFViolationError):
            validate_url_safe("http://169.254.169.254/latest/meta-data/")

    def test_private_a_blocked(self):
        with pytest.raises(SSRFViolationError):
            validate_url_safe("http://10.0.0.1/internal-service")

    def test_private_b_blocked(self):
        with pytest.raises(SSRFViolationError):
            validate_url_safe("http://172.16.0.1/")

    def test_private_c_blocked(self):
        with pytest.raises(SSRFViolationError):
            validate_url_safe("http://192.168.1.100/api")

    def test_invalid_scheme_blocked(self):
        with pytest.raises(SSRFViolationError):
            validate_url_safe("ftp://files.example.com/export")

    def test_file_scheme_blocked(self):
        with pytest.raises(SSRFViolationError):
            validate_url_safe("file:///etc/passwd")


# ============================================================
# Node Registry Tests
# ============================================================

class TestNodeRegistry:
    def test_registry_has_nodes(self):
        nodes = get_all_nodes()
        assert len(nodes) > 0, "Node registry must have at least one node"

    def test_all_categories_present(self):
        by_cat = get_nodes_by_category()
        required = {"trigger", "ai", "social", "logic", "data", "time", "utility", "content"}
        present = set(by_cat.keys())
        missing = required - present
        assert not missing, f"Missing categories in registry: {missing}"

    def test_trigger_nodes_present(self):
        by_cat = get_nodes_by_category()
        triggers = by_cat.get("trigger", [])
        assert any(t["id"] == "trigger_manual" for t in triggers)
        assert any(t["id"] == "trigger_schedule" for t in triggers)

    def test_ai_nodes_present(self):
        by_cat = get_nodes_by_category()
        ai_nodes = by_cat.get("ai", [])
        ids = {n["id"] for n in ai_nodes}
        assert "ai_generate_text" in ids
        assert "ai_generate_hashtags" in ids
        assert "ai_recommend_time" in ids

    def test_social_nodes_present(self):
        by_cat = get_nodes_by_category()
        social = by_cat.get("social", [])
        ids = {n["id"] for n in social}
        assert "social_publish" in ids
        assert "social_content_validation" in ids

    def test_logic_nodes_present(self):
        by_cat = get_nodes_by_category()
        logic = by_cat.get("logic", [])
        ids = {n["id"] for n in logic}
        assert "logic_condition" in ids
        assert "logic_switch" in ids
        assert "logic_filter" in ids

    def test_utility_http_node_present(self):
        assert "utility_http_request" in NODE_REGISTRY

    def test_every_node_has_required_fields(self):
        nodes = get_all_nodes()
        required_fields = {"id", "name", "category", "description", "icon", "status", "inputs", "outputs", "config_schema"}
        for node in nodes:
            missing = required_fields - set(node.keys())
            assert not missing, f"Node {node.get('id')} missing fields: {missing}"

    def test_active_nodes_have_category(self):
        nodes = get_all_nodes()
        for node in nodes:
            if node["status"] == "active":
                assert node["category"], f"Active node {node['id']} has no category"

    def test_config_schema_fields_valid(self):
        nodes = get_all_nodes()
        valid_field_types = {
            "text", "textarea", "select", "number", "boolean",
            "secret_ref", "json", "expression",
        }
        for node in nodes:
            for field in node.get("config_schema", []):
                assert field["field_type"] in valid_field_types, (
                    f"Node {node['id']}: field {field['key']} has invalid type {field['field_type']}"
                )
