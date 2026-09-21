# BioMysteryBench

[BioMysteryBench](https://www.anthropic.com/research/Evaluating-Claude-For-Bioinformatics-With-BioMysteryBench) is Anthropic's open-ended agentic bioinformatics benchmark. Each problem provides a real, anonymized biological dataset and asks a question that requires genuine analysis (alignment, expression, variant calling, motif discovery, structure, ...) to answer — the source dataset cannot be looked up. The model works in a sandbox with canonical bioinformatics tools and internet access to NCBI/Ensembl/etc., then submits a free-form answer that is graded by a model judge against the problem's rubric.

<!-- Contributors: Automatically Generated -->

Contributed by [@jacobdaviessafer](https://github.com/jacobdaviessafer)

<!-- /Contributors: Automatically Generated -->

<!-- Usage: Automatically Generated -->

## Usage

### Installation

There are two ways of using Inspect Evals, from pypi as a dependency of your own project and as a standalone checked out GitHub repository.

If you are using it from pypi, install the package and its dependencies via:

```bash
pip install inspect-evals
```

If you are using Inspect Evals in its repository, start by installing the necessary dependencies with:

```bash
uv sync
```

### Running evaluations

Now you can start evaluating models. For simplicity's sake, this section assumes you are using Inspect Evals from the standalone repo. If that's not the case and you are not using `uv` to manage dependencies in your own project, you can use the same commands with `uv run` dropped.

```bash
uv run inspect eval inspect_evals/bio_mystery_bench --model openai/gpt-5-nano
```

You can also import tasks as normal Python objects and run them from python:

```python
from inspect_ai import eval
from inspect_evals.biomysterybench import bio_mystery_bench
eval(bio_mystery_bench)
```

After running evaluations, you can view their logs using the `inspect view` command:

```bash
uv run inspect view
```

For VS Code, you can also download [Inspect AI extension for viewing logs](https://inspect.ai-safety-institute.org.uk/log-viewer.html).

If you don't want to specify the `--model` each time you run an evaluation, create a `.env` configuration file in your working directory that defines the `INSPECT_EVAL_MODEL` environment variable along with your API key. For example:

```bash
INSPECT_EVAL_MODEL=anthropic/claude-opus-4-1-20250805
ANTHROPIC_API_KEY=<anthropic-api-key>
```

<!-- /Usage: Automatically Generated -->

<!-- Options: Automatically Generated -->

## Options

You can control a variety of options from the command line. For example:

```bash
uv run inspect eval inspect_evals/bio_mystery_bench --limit 10 --sample-shuffle
uv run inspect eval inspect_evals/bio_mystery_bench --max-connections 10
uv run inspect eval inspect_evals/bio_mystery_bench --temperature 0.5
```

See `uv run inspect eval --help` for all available options.

<!-- /Options: Automatically Generated -->

<!-- Parameters: Automatically Generated -->

## Parameters

### `bio_mystery_bench`

- `source` (`str`): "full" (90 gated problems) or "preview" (open 5-problem sample). (default: `'full'`)
- `ids` (`str | list[str] | None`): restrict to these problem ids. Accepts a list or a single id. (default: `None`)
- `limit` (`int | None`): keep only the first N problems (after filtering). (default: `None`)
- `human_solvable_only` (`bool`): keep only problems >=1 human solved. (default: `False`)
- `image_prefix` (`str | None`): per-problem image tag prefix; a sample's image is image_prefix + problem_id. Defaults to the BMB_IMAGE_PREFIX env var. (default: `None`)
- `with_sandbox` (`bool`): attach the docker sandbox (default True). False builds the task without a sandbox, for registration and offline tests. (default: `True`)
- `epochs` (`int`): trials per problem. (default: `1`)
- `tool_timeout` (`int`): per bash/python call timeout in seconds (passed to the solver). (default: `600`)
- `message_limit` (`int | None`): hard cap on messages per sample (default: `150`)
- `token_limit` (`int | None`): optional per-sample token cap (passed to the solver). (default: `None`)
- `max_tool_output` (`int | None`): truncate each tool result to this many bytes (passed to the solver). (default: `None`)

<!-- /Parameters: Automatically Generated -->

## Dataset

Two HuggingFace datasets, both pinned to a specific revision so runs are reproducible:

- [`Anthropic/BioMysteryBench-full`](https://huggingface.co/datasets/Anthropic/BioMysteryBench-full) — 90 problems, one `data/<id>.zip` per problem. 155 GB in total: the median archive is about 56 MB, but six exceed 10 GB and the largest is about 27 GB. **Gated** — the runner needs `HF_TOKEN` with accepted access.
- [`Anthropic/BioMysteryBench-preview`](https://huggingface.co/datasets/Anthropic/BioMysteryBench-preview) — an open 5-problem sample with a single bundled `data.zip`. Not gated, and needs no token. Used for pipeline smoke tests.

Each problem row has `id, question, answer_rubric, allowed_domains, human_solvable`.

`allowed_domains` is carried into sample metadata for transcript analysis but is **not enforced**. The sandbox has unrestricted network access, so the rule against looking up accession IDs and source publications rests on the system prompt and on the judge spotting a violation in the transcript. A model that fetches the source study anyway will only be caught if the judge notices.

The `human_solvable` flag marks the 73 problems that at least one human benchmarker solved; the other 17 are human-difficult. The **human-solvable subset is the headline metric** — Anthropic reports mean accuracy over 5 trials on it.

## How the data reaches the sandbox

The full dataset is 155 GB, far too large to download per run. Instead each problem's data is **baked into its own sandbox image** ahead of time, so at run time the model finds the files already extracted under `data/` and nothing is downloaded into the sandbox.

The task builder reads only `problems.csv` (a few KB) to get the questions and rubrics. For the gated full set that read needs `HF_TOKEN` on the runner; the sandboxes themselves need no token. A sample's image is `<image_prefix><id>`; set `image_prefix` (or the `BMB_IMAGE_PREFIX` env var) to your image repo, and the runner substitutes each sample's image into `compose.yaml` via `${SAMPLE_METADATA_BMB_IMAGE}`.

## Scoring

Model-graded (`biomystery_grader`, built on `model_graded_qa`). Each problem's `answer_rubric` contains the expected answer and the scoring rule. The judge sees the full transcript (`include_history=True`) so it can enforce the benchmark's anti-cheat rule: identifying the source dataset via GEO/SRA/ENA/BioProject accession lookups, the source publication, or study metadata disqualifies the answer; standard database use (gene/sequence lookup, reference download, BLAST) is allowed. `Score.metadata` records `human_solvable` and the model's `stop_reason` for downstream analysis.

Set the `grader` model role, or grading falls back to the target model and the model grades its own answer.

## Sandbox images

Two Dockerfiles build the images:

- `Dockerfile.base` — the shared bioinformatics toolset (miniforge; samtools, bcftools, bedtools, bwa, bowtie2, minimap2, STAR, salmon, subread, BLAST+, HMMER, MAFFT, seqkit, fastqc; biopython, pysam, pandas, numpy, scipy, scikit-learn). The model installs anything else at run time with conda or pip.
- `Dockerfile` — a per-problem image: `FROM` the base, with that problem's data copied under `data/`.

`build_and_push.sh` builds the base, then one image per problem, and pushes them. It needs `HF_TOKEN` (to fetch the data at build time) and push credentials for your registry:

```bash
HF_TOKEN=hf_... \
BP_PREFIX=<account>.dkr.ecr.<region>.amazonaws.com/prd/biomystery: \
./build_and_push.sh
```

Useful options: `BP_SOURCE=preview` (5-problem set), `BP_IDS="hb002 hb020"` (subset), `BP_MAX_GB=15` (skip the largest archives), `BP_SKIP_EXISTING=1` (resume). Then run with the same prefix:

```bash
export BMB_IMAGE_PREFIX=<account>.dkr.ecr.<region>.amazonaws.com/prd/biomystery:
```

## Changelog

### [1-A] - 2026-08-10

Initial version.
