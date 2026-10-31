import ast
from pathlib import Path

from cartpulse import pipeline

DAG_FILE = Path(__file__).parents[1] / "orchestration/dags/cartpulse_daily.py"


def test_quality_checks_run_before_the_marts_are_published():
    steps = [step.__name__ for step in pipeline.STEPS]

    assert steps.index("check_quality") < steps.index("refresh_marts")
    assert steps.index("build_warehouse") < steps.index("check_quality")


def test_dag_runs_every_pipeline_step():
    tree = ast.parse(DAG_FILE.read_text())
    tasks = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name != "cartpulse_daily"
    }

    assert tasks == {step.__name__ for step in pipeline.STEPS}


def test_dag_publishes_only_after_the_quality_gate():
    source = DAG_FILE.read_text()

    assert "built >> check_quality() >> refresh_marts()" in source
