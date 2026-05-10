import importlib.util
import sys
import sysconfig
from pathlib import Path


def _load_stdlib_calendar():
    stdlib_path = Path(sysconfig.get_path("stdlib")) / "calendar.py"
    spec = importlib.util.spec_from_file_location("_solfasol_stdlib_calendar", stdlib_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_stdlib_calendar = _load_stdlib_calendar()
__all__ = list(getattr(_stdlib_calendar, "__all__", []))

for _name in dir(_stdlib_calendar):
    if _name.startswith("__") and _name not in {"__doc__"}:
        continue
    globals()[_name] = getattr(_stdlib_calendar, _name)
