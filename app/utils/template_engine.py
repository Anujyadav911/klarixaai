from jinja2 import Template, TemplateSyntaxError, UndefinedError

from app.core.exceptions import TemplateRenderError


def render_template(template_str: str, variables: dict[str, str]) -> str:
    try:
        template = Template(template_str)
        return template.render(**variables)
    except (TemplateSyntaxError, UndefinedError) as exc:
        raise TemplateRenderError("inline", str(exc)) from exc
