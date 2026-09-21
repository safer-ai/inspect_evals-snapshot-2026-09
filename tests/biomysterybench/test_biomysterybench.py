"""Offline tests for BioMysteryBench (no HuggingFace / no model calls).

Covers the solver's construction, the model-graded scorer's metadata stamping (grader
model mocked), sample staging logic, and task wiring (agentic solver + grader + sandbox)
via an in-memory dataset. End-to-end behaviour (gated dataset download, real model,
sandbox execution, real judging) is exercised by a gated smoke run, not here.
"""

import asyncio
from types import SimpleNamespace

import pytest
from inspect_ai import eval
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.scorer import CORRECT, INCORRECT, Score

import inspect_evals.biomysterybench.biomysterybench as bmb
import inspect_evals.biomysterybench.scorer as scoring
import inspect_evals.biomysterybench.solver as solving
from inspect_evals.biomysterybench import bio_mystery_bench
from inspect_evals.biomysterybench.solver import biomystery_solver, require_problem_data
from tests.utils.solvers import mock_solver_with_output
from tests.utils.task_assertions import assert_eval_success

# --- solver / scorer / task construct ----------------------------------------


def test_solver_builds():
    assert callable(biomystery_solver(tool_timeout=30, message_limit=5))


def _sandbox_returning(stdout: str, success: bool = True):
    """Stub inspect_ai's sandbox() with one whose exec returns a fixed result."""

    async def fake_exec(cmd):
        return SimpleNamespace(success=success, stdout=stdout, stderr="")

    return lambda *a, **k: SimpleNamespace(exec=fake_exec)


def test_require_problem_data_passes_when_data_present(monkeypatch):
    monkeypatch.setattr(solving, "sandbox", _sandbox_returning("reads.fastq\n"))
    state = SimpleNamespace(sample_id="hb002", metadata={"BMB_IMAGE": "repo:hb002"})
    result = asyncio.run(require_problem_data()(state, None))
    assert result is state


def test_require_problem_data_raises_when_data_missing(monkeypatch):
    """An empty data/ is an infrastructure failure, not a wrong answer.

    A bad image must surface as an ERRORED sample rather than as a low score.
    """
    monkeypatch.setattr(solving, "sandbox", _sandbox_returning(""))
    state = SimpleNamespace(sample_id="hb002", metadata={"BMB_IMAGE": "repo:hb002"})
    with pytest.raises(RuntimeError, match="did not deliver its data"):
        asyncio.run(require_problem_data()(state, None))


def test_require_problem_data_raises_when_ls_fails(monkeypatch):
    monkeypatch.setattr(solving, "sandbox", _sandbox_returning("x", success=False))
    state = SimpleNamespace(sample_id="hb002", metadata={"BMB_IMAGE": "repo:hb002"})
    with pytest.raises(RuntimeError, match="did not deliver its data"):
        asyncio.run(require_problem_data()(state, None))


def test_task_is_callable_and_registered():
    # @task-decorated; importable and carries a registry name
    assert callable(bio_mystery_bench)


# --- scorer metadata stamping (grader model mocked) --------------------------


def _fake_state(stop_reason="stop", human_solvable="yes", pid="hb002"):
    return SimpleNamespace(
        output=SimpleNamespace(
            completion="Bacillus licheniformis", stop_reason=stop_reason
        ),
        metadata={"human_solvable": human_solvable, "problem_id": pid},
        sample_id=pid,
    )


def test_grader_stamps_metadata(monkeypatch):
    def fake_model_graded_qa(**kwargs):
        async def inner(state, target):
            return Score(
                value=CORRECT,
                answer=state.output.completion,
                explanation="matches rubric",
                metadata={"grader_model": "fake"},
            )

        return inner

    monkeypatch.setattr(scoring, "model_graded_qa", fake_model_graded_qa)
    result = asyncio.run(
        scoring.biomystery_grader()(_fake_state(), SimpleNamespace(text="rubric"))
    )
    assert result.value == CORRECT
    assert result.metadata["human_solvable"] == "yes"
    assert result.metadata["problem_id"] == "hb002"
    assert result.metadata["stop_reason"] == "stop"
    assert result.metadata["grader_model"] == "fake"  # inner metadata preserved


def test_grader_preserves_incorrect_and_limit_stop(monkeypatch):
    def fake_model_graded_qa(**kwargs):
        async def inner(state, target):
            return Score(value=INCORRECT, answer="", explanation="wrong", metadata={})

        return inner

    monkeypatch.setattr(scoring, "model_graded_qa", fake_model_graded_qa)
    state = _fake_state(stop_reason="message_limit", human_solvable="no")
    result = asyncio.run(
        scoring.biomystery_grader()(state, SimpleNamespace(text="rubric"))
    )
    assert result.value == INCORRECT
    assert result.metadata["human_solvable"] == "no"
    assert result.metadata["stop_reason"] == "message_limit"


# --- sample mapping + selection (no network) ---------------------------------

_REC = {
    "id": "hb002",
    "question": "What bacteria is found in this sequenced dataset?",
    "answer_rubric": "The answer is Bacillus licheniformis. Score 1.0 if correct.",
    "allowed_domains": "ncbi.nlm.nih.gov, ensembl.org",
    "human_solvable": "yes",
}


def test_make_sample_maps_fields():
    s = bmb._make_sample(_REC, "acct.dkr.ecr.eu-west-3.amazonaws.com/prd/biomystery:")
    assert isinstance(s, Sample)
    assert s.input == _REC["question"]
    assert s.target == _REC["answer_rubric"]  # rubric is the grader's criterion
    assert s.id == "hb002"
    assert s.metadata["human_solvable"] == "yes"
    assert s.metadata["allowed_domains"] == "ncbi.nlm.nih.gov, ensembl.org"
    # image tag = prefix + problem id; substituted into compose as SAMPLE_METADATA_BMB_IMAGE
    assert (
        s.metadata["BMB_IMAGE"]
        == "acct.dkr.ecr.eu-west-3.amazonaws.com/prd/biomystery:hb002"
    )
    # no eager data staging: images already carry the data
    assert s.files is None and s.setup is None


# --- task wiring (no HF: inject a MemoryDataset) -----------------------------


def test_create_task_declares_sandbox_and_grader():
    task = bmb._create_task(
        MemoryDataset([Sample(input="q", target="rubric", id="x")]),
        biomystery_solver(),
        sandbox=("docker", "compose.yaml"),
    )
    assert task.sandbox is not None
    assert getattr(task.sandbox, "type", None) == "docker"
    assert task.scorer is not None


def test_task_rejects_bad_source():
    with pytest.raises(ValueError, match="source must be"):
        bio_mystery_bench(source="nope", with_sandbox=False)


def test_ids_accepts_a_bare_string(monkeypatch):
    """`-T ids=hb002` reaches the task as a string, not a one-element list.

    Inspect's CLI collapses a single-element list back to a bare string. Treating
    that as a sequence gives a set of characters, so nothing matches and the task
    raises "No problems selected after filtering" for a valid id.
    """
    rows = [
        {"id": "hb002", "question": "q", "answer_rubric": "r", "human_solvable": "yes"},
        {"id": "hb003", "question": "q", "answer_rubric": "r", "human_solvable": "yes"},
    ]
    monkeypatch.setattr(bmb, "_load_problems", lambda *a, **k: rows)
    task = bio_mystery_bench(
        source="preview", ids="hb002", with_sandbox=False, image_prefix="repo:"
    )
    assert [s.id for s in task.dataset] == ["hb002"]


def test_ids_reports_unknown_ids(monkeypatch):
    rows = [
        {"id": "hb002", "question": "q", "answer_rubric": "r", "human_solvable": "yes"}
    ]
    monkeypatch.setattr(bmb, "_load_problems", lambda *a, **k: rows)
    with pytest.raises(ValueError, match="ids not in the dataset"):
        bio_mystery_bench(
            source="preview",
            ids=["hb002", "hb0O2"],
            with_sandbox=False,
            image_prefix="repo:",
        )


def test_task_requires_image_prefix_when_sandboxed(monkeypatch):
    monkeypatch.delenv("BMB_IMAGE_PREFIX", raising=False)
    with pytest.raises(ValueError, match="image_prefix is unset"):
        bio_mystery_bench(source="preview", with_sandbox=True, image_prefix=None)


@pytest.mark.slow(30)
def test_end_to_end_with_mockllm(tmp_path):
    """Run one sample end to end with a mock model, no sandbox and no network."""
    dataset = MemoryDataset(
        [
            Sample(
                input="Which organism does this genome belong to?",
                target=(
                    "The answer is Bacillus licheniformis. Score 1.0 if the model "
                    "did not cheat AND got the answer correct. Score 0 otherwise."
                ),
                id="hb002",
                metadata={"problem_id": "hb002", "human_solvable": "yes"},
            )
        ]
    )
    task = bmb._create_task(dataset, mock_solver_with_output("Bacillus licheniformis"))

    [log] = eval(tasks=[task], model="mockllm/model", limit=1, log_dir=str(tmp_path))

    assert_eval_success(log, min_samples=1)
    assert log.samples is not None
    assert log.samples[0].scores is not None
