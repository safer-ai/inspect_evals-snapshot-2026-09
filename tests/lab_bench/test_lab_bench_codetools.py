import pytest
from inspect_ai import eval
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import ChatMessageSystem, ChatMessageUser, ModelOutput, get_model
from inspect_ai.scorer import CORRECT

from inspect_evals.lab_bench import codetools
from inspect_evals.lab_bench.codetools import (
    _codetools_task,
    lab_bench_cloning_scenarios_codetools,
    lab_bench_dbqa_codetools,
    lab_bench_figqa_codetools,
    lab_bench_litqa_codetools,
    lab_bench_protocolqa_codetools,
    lab_bench_seqqa_codetools,
    lab_bench_suppqa_codetools,
    lab_bench_tableqa_codetools,
)
from inspect_evals.lab_bench.lab_bench import lab_bench_litqa, task_base
from tests.utils.task_assertions import assert_eval_success, assert_task_structure

ALL_CODETOOLS_TASKS = [
    lab_bench_cloning_scenarios_codetools,
    lab_bench_dbqa_codetools,
    lab_bench_figqa_codetools,
    lab_bench_litqa_codetools,
    lab_bench_protocolqa_codetools,
    lab_bench_seqqa_codetools,
    lab_bench_suppqa_codetools,
    lab_bench_tableqa_codetools,
]

# A distinctive line from MULTIPLE_CHOICE_TEMPLATE, used to check the rendered prompt.
_TEMPLATE_MARKER = "ANSWER: $LETTER"


@pytest.fixture(autouse=True)
def _sandbox_image_env(monkeypatch):
    monkeypatch.setenv("LABBENCH_SANDBOX_IMAGE", "example.registry/labbench:test")


def _mcq_dataset() -> MemoryDataset:
    return MemoryDataset(
        [
            Sample(
                input="Which base pairs with adenine in DNA?",
                choices=["Thymine", "Guanine", "Cytosine"],
                target="A",
            )
        ]
    )


def test_codetools_task_structure():
    task = _codetools_task(_mcq_dataset())
    assert_task_structure(task, sandbox_type="docker")
    assert str(task.sandbox.config).endswith("compose.yaml")
    # compose.yaml reads the image from ${SAMPLE_METADATA_LABBENCH_IMAGE}
    [sample] = task.dataset
    assert sample.metadata["LABBENCH_IMAGE"] == "example.registry/labbench:test"


def test_codetools_task_requires_sandbox_image(monkeypatch):
    monkeypatch.delenv("LABBENCH_SANDBOX_IMAGE", raising=False)
    with pytest.raises(ValueError, match="LABBENCH_SANDBOX_IMAGE"):
        _codetools_task(_mcq_dataset())


def test_codetools_task_pins_version_and_epochs():
    """The port must stay comparability-version 2 with a single epoch — not bumped."""
    task = _codetools_task(_mcq_dataset())
    assert task.version == 2
    assert task.metadata["full_task_version"] == "2-A"
    assert task.metadata["sandbox_image"] == "example.registry/labbench:test"
    assert task.epochs == 1
    # No task-level message cap: per-run limits are set in the eval-set config.
    assert task.message_limit is None


def test_end_to_end_offline_with_mockllm(tmp_path):
    """One sample end to end with a mock model, no sandbox and no network.

    Also checks the two composition invariants that matter: the system prompt is
    injected, and multiple_choice renders the stock MCQ template.
    """
    task = _codetools_task(_mcq_dataset())
    task.sandbox = None  # mock answers directly, so no sandbox/tools needed

    model = get_model(
        "mockllm/model",
        custom_outputs=[
            ModelOutput.from_content(model="mockllm/model", content="ANSWER: A")
        ],
    )
    [log] = eval(tasks=[task], model=model, limit=1, log_dir=str(tmp_path))

    assert_eval_success(log, expected_metric="accuracy")
    assert log.samples is not None
    sample = log.samples[0]

    score = sample.scores["cf_aware_precision_choice"]
    assert score.value == CORRECT
    assert score.metadata["content_filter"] is False
    assert "stop_reason" in score.metadata

    # system_message solver ran (its prompt is in the transcript)
    assert any(
        isinstance(m, ChatMessageSystem) and "sandboxed Linux" in m.text
        for m in sample.messages
    )
    # multiple_choice rendered the stock template (its instruction is in the user prompt)
    assert any(
        isinstance(m, ChatMessageUser) and _TEMPLATE_MARKER in m.text
        for m in sample.messages
    )


def test_codetools_solver_chain():
    """The codetools solver is system_message, use_tools, multiple_choice.

    This says nothing about the stock tasks. That invariant is checked by
    test_stock_task_still_non_sandboxed, which needs the dataset and so is
    marked huggingface.
    """
    codetools_solvers = codetools._codetools_solver()
    assert len(codetools_solvers) == 3  # system_message, use_tools, multiple_choice


def test_stock_task_offline_still_non_sandboxed():
    """Runs in default CI: the stock solver chain and no-sandbox invariant."""
    task = task_base(_mcq_dataset())
    assert task.sandbox is None
    assert len(task.solver) == 1


@pytest.mark.huggingface
def test_stock_task_still_non_sandboxed():
    task = lab_bench_litqa()
    assert task.sandbox is None
    assert len(task.solver) == 1


@pytest.mark.huggingface
def test_all_eight_tasks_construct():
    for fn in ALL_CODETOOLS_TASKS:
        task = fn()
        assert_task_structure(task, sandbox_type="docker")
