"""Unix Research Workflow scripts package.

Expose the public API lazily so `python -m scripts.<module>` can run from the
repository root without triggering eager imports of sibling CLI modules.
"""

from importlib import import_module
from typing import Dict, Tuple

_EXPORTS: Dict[str, Tuple[str, str]] = {
    "Config": ("scripts.config", "Config"),
    "LogHook": ("scripts.log_hook", "LogHook"),
    "create_experiment": ("scripts.new_exp", "create_intent_yaml"),
    "list_experiments": ("scripts.list_exp", "list_experiments"),
    "validate_intent": ("scripts.validate_intent", "validate_intent"),
    "summarize": ("scripts.summarize", "summarize"),
    "remove_experiment": ("scripts.rm_exp", "remove_experiment"),
    "show_experiment": ("scripts.show_exp", "show_experiment"),
    "export_to_csv": ("scripts.export_csv", "export_to_csv"),
    "compare_experiments": ("scripts.compare_exp", "compare_experiments"),
    "ReportFactory": ("scripts.report_factory", "ReportFactory"),
    "ReportFormat": ("scripts.report_factory", "ReportFormat"),
    "MlflowHook": ("scripts.mlflow_integration", "MlflowHook"),
    "get_mlflow_tracking_command": (
        "scripts.mlflow_integration",
        "get_mlflow_tracking_command",
    ),
    "show_mlflow_info": ("scripts.mlflow_integration", "show_mlflow_info"),
}

__all__ = sorted(_EXPORTS)


def __getattr__(name: str):
    """Load public package attributes on demand."""
    if name not in _EXPORTS:
        raise AttributeError(f"module 'scripts' has no attribute '{name}'")

    module_name, attr_name = _EXPORTS[name]
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
