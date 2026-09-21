### Existing Evals

- LAB-Bench: added eight code-tools task variants (`lab_bench_<subtask>_codetools`) that give the model a `bash`/`python` sandbox with common biology packages, alongside a `cf_aware_precision_choice` scorer that records the model's stop reason and a content-filter flag. The existing eight tasks and `precision_choice` are unchanged.
- LAB-Bench: eval.yaml metadata gains `requires_internet: true` and `sandbox: [solver]`. Metadata is eval-wide, so the stock tasks carry both fields too.
