Method Plugins
==============

EvalVault supports a method plugin interface to run team-specific RAG pipelines
against a shared base dataset and then evaluate the outputs with the standard
metrics and analysis tools.

Sources
-------
- Internal registry: `config/methods.yaml`
- External packages: entry points under `evalvault.methods`

Base Dataset Template
---------------------
Use the question-first template at `dataset_templates/method_input_template.json`.
It only needs question/ground_truth/contexts/metadata and stays stable across teams.

Internal Registry Example
-------------------------
```yaml
methods:
  baseline_oracle:
    class_path: "evalvault.adapters.outbound.methods.baseline_oracle:BaselineOracleMethod"
    description: "Use ground truth as the answer when available."
    tags: ["baseline", "oracle"]
```

Entry Point Example (external package)
--------------------------------------
```toml
[project.entry-points."evalvault.methods"]
my_team_method = "my_team_pkg.methods:MyTeamMethod"
```
See `examples/method_plugin_template` for a working scaffold.

External Command (dependency isolation)
---------------------------------------
When method dependencies conflict, run them in a separate venv/container.
Configure a command-based method in `config/methods.yaml`:

```yaml
methods:
  team_method_external:
    runner: external
    command: "bash -lc 'cd ../team_method && uv run python -m team_method.run --input \"$EVALVAULT_METHOD_INPUT\" --output \"$EVALVAULT_METHOD_OUTPUT\"'"
    shell: true
    timeout_seconds: 3600
    description: "Team method executed in its own env"
```

Environment variables passed to the command:
- `EVALVAULT_METHOD_INPUT`: base dataset path
- `EVALVAULT_METHOD_OUTPUT`: output JSON path (method outputs)
- `EVALVAULT_METHOD_DOCS`: docs path if provided
- `EVALVAULT_METHOD_CONFIG`: method config path if provided
- `EVALVAULT_METHOD_RUN_ID`: run id
- `EVALVAULT_METHOD_ARTIFACTS`: artifacts directory

External output format:
```json
{
  "outputs": [
    {
      "id": "tc-001",
      "answer": "...",
      "contexts": ["..."],
      "metadata": {},
      "retrieval_metadata": {}
    }
  ]
}
```
Placeholders supported in `command`:
`{input}`, `{output}`, `{docs}`, `{config}`, `{run_id}`, `{artifacts}`, `{method}`

Method Interface (minimal)
--------------------------
```python
from evalvault.domain.entities.method import MethodInput, MethodOutput
from evalvault.ports.outbound.method_port import MethodRuntime, RagMethodPort


class MyTeamMethod(RagMethodPort):
    name = "my_team_method"
    version = "0.1.0"
    description = "Team-specific RAG pipeline"

    def run(self, inputs, *, runtime: MethodRuntime, config=None):
        outputs = []
        for case in inputs:
            outputs.append(
                MethodOutput(
                    id=case.id,
                    answer="...",
                    contexts=["..."],
                    metadata={"method": self.name},
                )
            )
        return outputs
```

CLI Usage
---------
```bash
# List available methods
evalvault method list

# Run a method and evaluate
evalvault method run data/base_questions.json --method my_team_method --metrics faithfulness

# Save dataset output without evaluation
evalvault method run data/base_questions.json --method my_team_method --no-evaluate
```
Optional inputs:
- `--docs` for domain corpus (json/jsonl/txt)
- `--method-config` or `--method-config-file` for method parameters

Logging & Outputs
-----------------
- Method outputs: `reports/experiments/<method>/<run_id>/method_outputs.json`
- Evaluation dataset: `reports/experiments/<method>/<run_id>/dataset.json`
- Evaluation results: saved to `data/db/evalvault.db` when `--db` is enabled
- Run metadata: method name/version/config + runtime info stored in tracker metadata
