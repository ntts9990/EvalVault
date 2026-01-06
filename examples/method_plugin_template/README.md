EvalVault Method Plugin Template
================================

Quick start
-----------
```bash
cd examples/method_plugin_template
pip install -e .
evalvault method list
```

The entry point is defined in `pyproject.toml`:
```
[project.entry-points."evalvault.methods"]
template_method = "method_plugin_template.methods:TemplateMethod"
```
