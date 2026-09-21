"""
LAB-Bench code-tools variant

The eight LAB-Bench subtasks with a code-execution sandbox: the model gets
`bash` and `python` tools in a container with common biology packages, and may
run code before answering.

FigQA and TableQA are image-based subtasks and need a vision-capable target
model; the other six are text-only.

# run one subtask
inspect eval inspect_evals/lab_bench_seqqa_codetools
"""

import os
from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import Dataset
from inspect_ai.solver import Solver, multiple_choice, system_message, use_tools
from inspect_ai.tool import bash, python

from inspect_evals.lab_bench.lab_bench import (
    MULTIPLE_CHOICE_TEMPLATE,
    DatasetSubsets,
    retrieve_hf_dataset,
    task_base,
)
from inspect_evals.lab_bench.record_to_sample_helpers import (
    UNCERTAIN_ANSWER_CHOICE,
    record_to_sample_base,
    record_to_sample_figqa,
    record_to_sample_protocolqa,
    record_to_sample_suppqa,
    record_to_sample_tableqa,
)
from inspect_evals.lab_bench.scorer import cf_aware_precision_choice

TOOL_TIMEOUT_SECONDS = 300

CODETOOLS_SYSTEM_PROMPT = (
    "You have access to a sandboxed Linux environment with Python 3 and Bash (with "
    "internet access), available through the `python` and `bash` tools. The Python "
    "packages biopython, pydna, primer3-py, pandas and numpy are installed, and you can "
    "read and write files in the working directory. Whether and how to use these tools "
    "is entirely up to you. When you are ready, give your final answer in the requested "
    "'ANSWER: $LETTER' format."
)

_SANDBOX = ("docker", str(Path(__file__).parent / "compose.yaml"))


def _codetools_solver() -> list[Solver]:
    return [
        system_message(CODETOOLS_SYSTEM_PROMPT),
        use_tools(
            bash(timeout=TOOL_TIMEOUT_SECONDS),
            python(timeout=TOOL_TIMEOUT_SECONDS),
        ),
        multiple_choice(template=MULTIPLE_CHOICE_TEMPLATE, cot=True),
    ]


SANDBOX_IMAGE_ENV = "LABBENCH_SANDBOX_IMAGE"


def _sandbox_image() -> str:
    image = os.environ.get(SANDBOX_IMAGE_ENV)
    if not image:
        raise ValueError(
            f"set {SANDBOX_IMAGE_ENV} to the code-tools sandbox image (see README.md)"
        )
    return image


def _codetools_task(dataset: Dataset) -> Task:
    # The image reaches compose.yaml through sample metadata
    # (${SAMPLE_METADATA_LABBENCH_IMAGE}): the k8s sandbox provider only
    # interpolates SAMPLE_METADATA_* variables, not the runner's environment.
    image = _sandbox_image()
    for sample in dataset:
        sample.metadata = {**(sample.metadata or {}), "LABBENCH_IMAGE": image}
    return task_base(
        dataset,
        solver=_codetools_solver(),
        scorer=cf_aware_precision_choice(no_answer=UNCERTAIN_ANSWER_CHOICE),
        sandbox=_SANDBOX,
        extra_metadata={"sandbox_image": image},
    )


@task
def lab_bench_litqa_codetools() -> Task:
    """LAB-Bench LitQA with a code-execution sandbox"""
    return _codetools_task(
        retrieve_hf_dataset(DatasetSubsets.LitQA2.value, record_to_sample_base)
    )


@task
def lab_bench_suppqa_codetools() -> Task:
    """LAB-Bench SuppQA with a code-execution sandbox"""
    return _codetools_task(
        retrieve_hf_dataset(DatasetSubsets.SuppQA.value, record_to_sample_suppqa)
    )


@task
def lab_bench_figqa_codetools() -> Task:
    """LAB-Bench FigQA with a code-execution sandbox"""
    return _codetools_task(
        retrieve_hf_dataset(DatasetSubsets.FigQA.value, record_to_sample_figqa)
    )


@task
def lab_bench_tableqa_codetools() -> Task:
    """LAB-Bench TableQA with a code-execution sandbox"""
    return _codetools_task(
        retrieve_hf_dataset(DatasetSubsets.TableQA.value, record_to_sample_tableqa)
    )


@task
def lab_bench_dbqa_codetools() -> Task:
    """LAB-Bench DbQA with a code-execution sandbox"""
    return _codetools_task(
        retrieve_hf_dataset(DatasetSubsets.DbQA.value, record_to_sample_base)
    )


@task
def lab_bench_protocolqa_codetools() -> Task:
    """LAB-Bench ProtocolQA with a code-execution sandbox"""
    return _codetools_task(
        retrieve_hf_dataset(
            DatasetSubsets.ProtocolQA.value, record_to_sample_protocolqa
        )
    )


@task
def lab_bench_seqqa_codetools() -> Task:
    """LAB-Bench SeqQA with a code-execution sandbox"""
    return _codetools_task(
        retrieve_hf_dataset(DatasetSubsets.SeqQA.value, record_to_sample_base)
    )


@task
def lab_bench_cloning_scenarios_codetools() -> Task:
    """LAB-Bench CloningScenarios with a code-execution sandbox"""
    return _codetools_task(
        retrieve_hf_dataset(
            DatasetSubsets.CloningScenarios.value, record_to_sample_base
        )
    )
