"""
PRAVAH Safe Expression Evaluator
===================================
Safely resolves template expressions in workflow node configuration.

Supported expression patterns:
  {{trigger.field}}                  → trigger payload field
  {{nodes.NODE_KEY.field}}           → output of a previously executed node
  {{org.field}}                      → organisation context field
  {{vars.VARIABLE_NAME}}             → workflow-level variable
  {{env.CONFIG_KEY}}                 → safe environment/config value

Security: Uses only string template substitution and ast.literal_eval.
         No eval(), no exec(), no subprocess. Never used to execute code.
"""

import ast
import re
from typing import Any, Dict

# Pattern: {{ ... }} with content inside
_EXPR_PATTERN = re.compile(r"\{\{([^}]+)\}\}")


class ExpressionEvaluationError(Exception):
    """Raised when an expression cannot be resolved safely."""
    pass


def resolve_template(template: str, context: Dict[str, Any]) -> str:
    """
    Resolve all {{...}} expressions in a string template against the given context.

    Context structure:
      {
        "trigger": {...},          # trigger payload
        "nodes": {                 # node output map, keyed by node_key
          "node_key": {...}
        },
        "org": {...},              # organisation safe fields
        "vars": {...},             # workflow variables
      }
    """
    def _replace(match: re.Match) -> str:
        expr = match.group(1).strip()
        try:
            value = _evaluate_expr(expr, context)
            if value is None:
                return ""
            return str(value)
        except ExpressionEvaluationError:
            return match.group(0)  # Leave unresolved expression as-is (safe fallback)

    return _EXPR_PATTERN.sub(_replace, template)


def evaluate_condition(
    field_expr: str,
    operator: str,
    compare_value: Any,
    context: Dict[str, Any],
) -> bool:
    """
    Evaluate a binary condition: field_expr <operator> compare_value

    Supported operators:
      equals, not_equals, contains, not_contains,
      greater_than, less_than, greater_equal, less_equal,
      is_empty, is_not_empty, starts_with, ends_with,
      in, not_in
    """
    try:
        # Resolve the field value from context
        actual = _evaluate_expr(field_expr, context) if _EXPR_PATTERN.search(f"{{{{{field_expr}}}}}") else field_expr

        # Coerce compare_value if it's a string expression
        if isinstance(compare_value, str) and "{{" in compare_value:
            compare_value = resolve_template(compare_value, context)

        op = operator.lower().replace(" ", "_")

        if op == "equals":
            return str(actual).lower() == str(compare_value).lower()
        elif op == "not_equals":
            return str(actual).lower() != str(compare_value).lower()
        elif op == "contains":
            return str(compare_value).lower() in str(actual).lower()
        elif op == "not_contains":
            return str(compare_value).lower() not in str(actual).lower()
        elif op == "starts_with":
            return str(actual).lower().startswith(str(compare_value).lower())
        elif op == "ends_with":
            return str(actual).lower().endswith(str(compare_value).lower())
        elif op == "is_empty":
            return actual is None or str(actual).strip() == ""
        elif op == "is_not_empty":
            return actual is not None and str(actual).strip() != ""
        elif op in ("greater_than", "gt"):
            return float(actual) > float(compare_value)
        elif op in ("less_than", "lt"):
            return float(actual) < float(compare_value)
        elif op in ("greater_equal", "gte"):
            return float(actual) >= float(compare_value)
        elif op in ("less_equal", "lte"):
            return float(actual) <= float(compare_value)
        elif op == "in":
            items = compare_value if isinstance(compare_value, list) else str(compare_value).split(",")
            return str(actual).lower() in [str(i).strip().lower() for i in items]
        elif op == "not_in":
            items = compare_value if isinstance(compare_value, list) else str(compare_value).split(",")
            return str(actual).lower() not in [str(i).strip().lower() for i in items]
        else:
            raise ExpressionEvaluationError(f"Unknown operator: {operator!r}")
    except (TypeError, ValueError, KeyError):
        return False


def _evaluate_expr(expr: str, context: Dict[str, Any]) -> Any:
    """
    Resolve a dotted-path expression against the context dict.

    Examples:
      "trigger.payload.status"       → context["trigger"]["payload"]["status"]
      "nodes.ai_gen_1.content"       → context["nodes"]["ai_gen_1"]["content"]
      "org.name"                     → context["org"]["name"]
      "vars.my_counter"              → context["vars"]["my_counter"]
    """
    parts = expr.strip().split(".")
    if not parts:
        raise ExpressionEvaluationError(f"Empty expression: {expr!r}")

    root = parts[0].lower()
    # Safe root keys only
    ALLOWED_ROOTS = {"trigger", "nodes", "org", "vars", "env"}
    if root not in ALLOWED_ROOTS:
        # Try resolving as a literal
        try:
            return ast.literal_eval(expr)
        except Exception:
            raise ExpressionEvaluationError(
                f"Expression root {root!r} is not allowed. Must be one of: {ALLOWED_ROOTS}"
            )

    current: Any = context.get(root, {})
    for part in parts[1:]:
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            try:
                current = getattr(current, part, None)
            except Exception:
                return None

    return current


def resolve_config_expressions(config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively resolve all template expressions in a node config dictionary.
    Only processes string values; leaves non-string values unchanged.
    """
    result = {}
    for key, value in config.items():
        if isinstance(value, str) and "{{" in value:
            result[key] = resolve_template(value, context)
        elif isinstance(value, dict):
            result[key] = resolve_config_expressions(value, context)
        elif isinstance(value, list):
            result[key] = [
                resolve_template(item, context) if isinstance(item, str) and "{{" in item else item
                for item in value
            ]
        else:
            result[key] = value
    return result
