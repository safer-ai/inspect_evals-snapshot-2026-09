# About this snapshot

This repository is a one-time snapshot of SaferAI's private copy of [UKGovernmentBEIS/inspect_evals](https://github.com/UKGovernmentBEIS/inspect_evals), taken on 2026-09-21 at commit 5f4344fdd. It is not maintained; upstream Inspect Evals is the place for issues and contributions.

## What SaferAI added

Everything in this tree is upstream Inspect Evals (synced to upstream as of 2026-08-10) except:

- **BioMysteryBench** (`src/inspect_evals/biomysterybench/`, task `bio_mystery_bench`): an Inspect implementation of Anthropic's open-ended agentic bioinformatics benchmark. See its README for dataset access, sandbox images and scoring.
- **LAB-Bench code-tools variants** (`src/inspect_evals/lab_bench/`, tasks `lab_bench_<subtask>_codetools`): the eight LAB-Bench subtasks with a bash and python sandbox and a content-filter-aware scorer. The stock tasks are unchanged.
- A retrying HuggingFace download helper in `src/inspect_evals/utils/huggingface.py`.

SaferAI's CI configuration was removed from this snapshot.

## Running BioMysteryBench elsewhere

The eval is Inspect-native and uses Inspect's docker sandbox (`compose.yaml`). It has only been run on SaferAI's Kubernetes cluster so far. To run it you need:

1. inspect-ai 0.3.245 or later.
2. Access to the gated dataset `Anthropic/BioMysteryBench-full` on HuggingFace and an `HF_TOKEN`. `Anthropic/BioMysteryBench-preview` (5 open problems) needs no token and can be used for smoke-tests. 
3. A container registry. `build_and_push.sh` builds a base image and one image per problem (the 155 GB dataset is baked into the images at build time) and pushes them to the prefix you give in `BP_PREFIX`. 
4. `BMB_IMAGE_PREFIX` set to that prefix at run time, and a grader model set through the `grader` model role. If the grader role is unset the model grades its own answer.
5. Enough disk on the sandbox hosts: five problems need 13 to 27 GB of data each.

Smoke test on the preview set, after building its images with `BP_SOURCE=preview`:

```bash
BMB_IMAGE_PREFIX=<prefix> uv run inspect eval inspect_evals/bio_mystery_bench \
  -T source=preview --limit 2 --model <solver-model> --model-role grader=<grader-model>
```

## Agentic evals: images, where they live, how they run

Every agentic eval has an eval directory which holds a `compose.yaml` that Inspect's sandbox provider starts once per sample. Image references in the compose file are either fixed or come from the sample's metadata, which Inspect exposes to compose as `SAMPLE_METADATA_<KEY>` variables. The requirements for running these evals anywhere are: a container registry your sandbox hosts can pull from, the images built and pushed there (where the eval does not use public ones), and an Inspect sandbox provider. The docker provider runs the compose file on a single machine and is the path Inspect documents. The Inspect Kubernetes sandbox provider runs the same services as pods, for scale. SaferAI's own setup is the second kind: a Kubernetes cluster on AWS driven by hawk, METR's eval runner, which installs this package at a pinned revision per run and renders these compose files onto the cluster. Nothing in this repository depends on hawk; other Kubernetes setups have not been tested by SaferAI.

| Eval | Who builds the images | Where they live | How the run finds them |
|---|---|---|---|
| BioMysteryBench (SaferAI) | You. `src/inspect_evals/biomysterybench/build_and_push.sh` builds one base image (`Dockerfile.base`, the bioinformatics toolset) and one image per problem (`Dockerfile`, the problem's data baked in). Needs `HF_TOKEN` for the gated dataset and push rights to your registry. Options: `BP_SOURCE=preview` for the 5 open problems, `BP_IDS`, `BP_MAX_GB` to skip the largest archives, `BP_SKIP_EXISTING=1` to resume. Total data 155 GB; five problems carry 13 to 27 GB each. Allow hours. | Any registry you can push to and your sandbox hosts can pull from. SaferAI uses AWS ECR. | Set `BMB_IMAGE_PREFIX` to the same prefix you built with. The task puts `<prefix><problem_id>` into sample metadata and `compose.yaml` reads `${SAMPLE_METADATA_BMB_IMAGE}`. Set the `grader` model role. Sandbox needs network access to NCBI, Ensembl, UniProt and package channels. |
| LAB-Bench code-tools (SaferAI) | You. `src/inspect_evals/lab_bench/build_and_push.sh` builds one image from the `Dockerfile` (biopython, pydna, primer3-py, pandas, numpy, curl). | Your registry. | Set `LABBENCH_SANDBOX_IMAGE` to the image reference at build time and at run time; the task records it in task and sample metadata and `compose.yaml` uses it. The sandbox needs internet. The eight stock `lab_bench_*` tasks need no sandbox. |
| CyberGym (upstream, unchanged by SaferAI) | Nobody, mostly. The agent sandbox is the public `aisiuk/evals-cybench-agent-sandbox`; the vulnerable and fixed program images come from the sample metadata (`${SAMPLE_METADATA_IMAGE_VULNERABLE}`, `${SAMPLE_METADATA_IMAGE_FIXED}`, the ARVO and OSS-Fuzz images). The `cybergym-inspect-controller` image is built locally by compose from `src/inspect_evals/cybergym/task_template/controller/Dockerfile` the first time a sample starts. | Public registries, pulled at run time. | `compose.yml` in `task_template/` starts four containers per sample (solver, vulnerable, fixed, controller). The solver sandbox has no internet. Known rough edge (SaferAI issue, not fixed): the scorer errors rather than scoring 0 when a proof of concept hangs. |
| SWE-bench (upstream, unchanged) | Nobody. Uses Epoch AI's pre-built per-instance images. | `ghcr.io/epoch-research/swe-bench.eval.{arch}.{id}`; log in with `gh auth token | docker login ghcr.io -u USERNAME --password-stdin`. | `sandbox_type` is `docker` or `k8s`; `image_name_template` can point at your own mirror. Upstream advises at most 32 containers at once on one machine. |
| SWE-Bench Pro | Not in this repository. | | SaferAI runs it through the separate [Inspect Harbor](https://github.com/meridianlabs-ai/inspect_harbor) package, as upstream's README section "Harbor Framework Evaluations" describes. |

