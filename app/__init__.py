# Keep the app package importable and load the demo template with a compatibility fix.
import sys
import types
from pathlib import Path


def _load_demo_template_compat():
    module_name = __name__ + '.demo_template'
    if module_name in sys.modules:
        return sys.modules[module_name]

    source_path = Path(__file__).with_name('demo_template.py')
    source = source_path.read_text(encoding='utf-8')

    nested = "{''.join(f'<div class=\"trust-item\">{x}</div>' for x in trust_items)}"
    if nested in source:
        anchor = "    schema = {k: v for k, v in schema.items() if v is not None}\n\n"
        insertion = "    trust_html = ''.join(f'<div class=\"trust-item\">{x}</div>' for x in trust_items)\n\n"
        if anchor in source and insertion not in source:
            source = source.replace(anchor, anchor + insertion, 1)
        source = source.replace(nested, '{trust_html}', 1)

    module = types.ModuleType(module_name)
    module.__file__ = str(source_path)
    module.__package__ = __name__
    sys.modules[module_name] = module
    try:
        code = compile(source, str(source_path), 'exec')
        exec(code, module.__dict__)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


_load_demo_template_compat()
