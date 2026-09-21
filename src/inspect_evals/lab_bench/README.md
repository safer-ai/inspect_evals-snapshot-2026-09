# LAB-Bench

[LAB-Bench](https://arxiv.org/abs/2407.10362) Tests LLMs and LLM-augmented agents abilities to answer questions on scientific research workflows in domains like chemistry, biology, materials science, as well as more general science tasks

<!-- Contributors: Automatically Generated -->

Contributed by [@matthewreed26](https://github.com/matthewreed26)

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
uv run inspect eval inspect_evals/lab_bench_litqa --model openai/gpt-5-nano
uv run inspect eval inspect_evals/lab_bench_suppqa --model openai/gpt-5-nano
uv run inspect eval inspect_evals/lab_bench_figqa --model openai/gpt-5-nano
uv run inspect eval inspect_evals/lab_bench_tableqa --model openai/gpt-5-nano
uv run inspect eval inspect_evals/lab_bench_dbqa --model openai/gpt-5-nano
uv run inspect eval inspect_evals/lab_bench_protocolqa --model openai/gpt-5-nano
uv run inspect eval inspect_evals/lab_bench_seqqa --model openai/gpt-5-nano
uv run inspect eval inspect_evals/lab_bench_cloning_scenarios --model openai/gpt-5-nano
uv run inspect eval inspect_evals/lab_bench_litqa_codetools --model openai/gpt-5-nano
uv run inspect eval inspect_evals/lab_bench_suppqa_codetools --model openai/gpt-5-nano
uv run inspect eval inspect_evals/lab_bench_figqa_codetools --model openai/gpt-5-nano
uv run inspect eval inspect_evals/lab_bench_tableqa_codetools --model openai/gpt-5-nano
uv run inspect eval inspect_evals/lab_bench_dbqa_codetools --model openai/gpt-5-nano
uv run inspect eval inspect_evals/lab_bench_protocolqa_codetools --model openai/gpt-5-nano
uv run inspect eval inspect_evals/lab_bench_seqqa_codetools --model openai/gpt-5-nano
uv run inspect eval inspect_evals/lab_bench_cloning_scenarios_codetools --model openai/gpt-5-nano
```

To run multiple tasks simultaneously use `inspect eval-set`:

```bash
uv run inspect eval-set inspect_evals/lab_bench_litqa inspect_evals/lab_bench_suppqa inspect_evals/lab_bench_figqa inspect_evals/lab_bench_tableqa inspect_evals/lab_bench_dbqa inspect_evals/lab_bench_protocolqa inspect_evals/lab_bench_seqqa inspect_evals/lab_bench_cloning_scenarios inspect_evals/lab_bench_litqa_codetools inspect_evals/lab_bench_suppqa_codetools inspect_evals/lab_bench_figqa_codetools inspect_evals/lab_bench_tableqa_codetools inspect_evals/lab_bench_dbqa_codetools inspect_evals/lab_bench_protocolqa_codetools inspect_evals/lab_bench_seqqa_codetools inspect_evals/lab_bench_cloning_scenarios_codetools
```

You can also import tasks as normal Python objects and run them from python:

```python
from inspect_ai import eval, eval_set
from inspect_evals.lab_bench import lab_bench_litqa, lab_bench_suppqa, lab_bench_figqa, lab_bench_tableqa, lab_bench_dbqa, lab_bench_protocolqa, lab_bench_seqqa, lab_bench_cloning_scenarios, lab_bench_litqa_codetools, lab_bench_suppqa_codetools, lab_bench_figqa_codetools, lab_bench_tableqa_codetools, lab_bench_dbqa_codetools, lab_bench_protocolqa_codetools, lab_bench_seqqa_codetools, lab_bench_cloning_scenarios_codetools
eval(lab_bench_litqa)
eval_set([lab_bench_litqa, lab_bench_suppqa, lab_bench_figqa, lab_bench_tableqa, lab_bench_dbqa, lab_bench_protocolqa, lab_bench_seqqa, lab_bench_cloning_scenarios, lab_bench_litqa_codetools, lab_bench_suppqa_codetools, lab_bench_figqa_codetools, lab_bench_tableqa_codetools, lab_bench_dbqa_codetools, lab_bench_protocolqa_codetools, lab_bench_seqqa_codetools, lab_bench_cloning_scenarios_codetools], log_dir='logs-run-42')
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
uv run inspect eval inspect_evals/lab_bench_litqa --limit 10 --sample-shuffle
uv run inspect eval inspect_evals/lab_bench_suppqa --max-connections 10
uv run inspect eval inspect_evals/lab_bench_figqa --temperature 0.5
```

See `uv run inspect eval --help` for all available options.

<!-- /Options: Automatically Generated -->

<!-- Parameters: Automatically Generated -->

## Parameters

### `lab_bench_litqa`, `lab_bench_suppqa`, `lab_bench_figqa`, `lab_bench_tableqa`, `lab_bench_dbqa`, `lab_bench_protocolqa`, `lab_bench_seqqa`, `lab_bench_cloning_scenarios`, `lab_bench_litqa_codetools`, `lab_bench_suppqa_codetools`, `lab_bench_figqa_codetools`, `lab_bench_tableqa_codetools`, `lab_bench_dbqa_codetools`, `lab_bench_protocolqa_codetools`, `lab_bench_seqqa_codetools`, `lab_bench_cloning_scenarios_codetools`

No task parameters.

<!-- /Parameters: Automatically Generated -->

## Dataset

The public dataset is [located on Hugging Face](https://huggingface.co/datasets/futurehouse/lab-bench) and [on GitHub](https://github.com/Future-House/LAB-Bench), but has been slightly reduced from the full private dataset Future House originally used to prevent model pre-training.

The dataset contains subsets of multiple choice questions that cover important practical research tasks that are largely universal across biology research like recall and reasoning over literature (LitQA2 and SuppQA), interpretation of figures (FigQA) and tables (TableQA), accessing databases (DbQA), writing protocols (ProtocolQA), and comprehending and manipulating DNA and protein sequences (SeqQA, CloningScenarios).

The Cloning Scenarios are “human-hard” multi-step multiple-choice questions that are expected to likely take a trained molecular biologist more than 10 minutes to answer completely.

- The LitQA task evaluates over 199 samples
- The SuppQA task evaluates over 82 samples
- The FigQA task evaluates over 181 samples
- The TableQA task evaluates over 244 samples
- The DbQA task evaluates over 520 samples
- The ProtocolQA task evaluates over 108 samples
- The SeqQA task evaluates over 600 samples
- The Cloning Scenarios task evaluates over 33 samples

For working examples from the datasets, look in: `/tests/lab_bench`

## Scoring

Performance is measured using Accuracy, Precision, and Coverage defined as follows:

- Accuracy, is defined as the number of correct multiple choice answers out of the total number of questions.
- Precision (also referred to in the literature as selective accuracy), is the number of correct answers out of the number of questions where the model did not pick the “Insufficient information” option.
- Coverage is the number of questions where the model did not pick the “Insufficient information” option out of the total number of questions.

Please do note: this Inspect implementation currently captures averaged results for DbQA and SeqQA. Whereas, original results of the white paper show Future House breaks DbQA and SeqQA specifically down into certain subtasks.

## Code-tools variant

Each subtask also has a `_codetools` twin (`lab_bench_seqqa_codetools`, ...) that gives the model `bash` and `python` tools in a Docker sandbox with biopython, pydna, primer3-py, pandas and numpy installed, and internet access. The prompt template and grading match the stock tasks; the scorer additionally records the model's stop reason and a content-filter flag in `Score.metadata`.

The tasks set no message or token limit. Set one in the eval-set config or with `--message-limit` / `--token-limit`. The limit is a backstop against runaway runs; pick a value well above what a normal attempt uses.

The sandbox image is supplied at run time via the `LABBENCH_SANDBOX_IMAGE` environment variable. `build_and_push.sh` in this directory builds it from the `Dockerfile` and pushes it:

```bash
LABBENCH_SANDBOX_IMAGE=<registry>/<repo>:labbench-bio-v2 src/inspect_evals/lab_bench/build_and_push.sh
export LABBENCH_SANDBOX_IMAGE=<registry>/<repo>:labbench-bio-v2
```

The task records the image in task and sample metadata, so every eval log carries the image it ran against.

## Changelog

### [2-A] - 2026-02-16

- Migrate version to new scheme. See [#907](https://github.com/UKGovernmentBEIS/inspect_evals/pull/907).

### [1.0.1] - 2025-12-18

- Adds backoff policy for functions that connect to huggingface servers.
