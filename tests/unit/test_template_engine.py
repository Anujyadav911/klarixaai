import pytest

from app.utils.template_engine import render_template
from app.core.exceptions import TemplateRenderError


class TestTemplateEngine:
    def test_basic_substitution(self):
        result = render_template("Hello {{name}}", {"name": "Anuj"})
        assert result == "Hello Anuj"

    def test_multiple_variables(self):
        template = "Hello {{name}}, your order {{order_id}} has shipped."
        variables = {"name": "Anuj", "order_id": "ORD-001"}
        result = render_template(template, variables)
        assert result == "Hello Anuj, your order ORD-001 has shipped."

    def test_empty_variables(self):
        result = render_template("Hello World", {})
        assert result == "Hello World"

    def test_missing_variable_renders_empty(self):
        result = render_template("Hello {{name}}", {})
        assert result == "Hello "

    def test_special_characters_in_value(self):
        result = render_template("Hello {{name}}", {"name": "O'Brien & Co."})
        assert result == "Hello O'Brien & Co."

    def test_invalid_syntax_raises_error(self):
        with pytest.raises(TemplateRenderError):
            render_template("Hello {% invalid %}", {})
