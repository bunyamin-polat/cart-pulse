"""Check the DAG definition by parsing it, because Airflow runs in a container."""

import ast
from pathlib import Path

DAG_FILE = Path(__file__).parents[1] / "modules/04-etl-airflow/dags/process_web_log.py"
TREE = ast.parse(DAG_FILE.read_text())


def keyword_values(name):
    """Return the constant values passed to every keyword argument called name."""
    return [
        node.value.value
        for node in ast.walk(TREE)
        if isinstance(node, ast.keyword)
        and node.arg == name
        and isinstance(node.value, ast.Constant)
    ]


def test_dag_runs_daily_under_the_required_name():
    assert keyword_values("dag_id") == ["process_web_log"]
    assert keyword_values("schedule") == ["@daily"]


def test_dag_defines_the_three_tasks():
    assert keyword_values("task_id") == [
        "extract_data",
        "transform_data",
        "load_data",
    ]


def test_tasks_run_in_order():
    chains = [
        node.value
        for node in ast.walk(TREE)
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.BinOp)
    ]

    assert [ast.unparse(chain) for chain in chains] == [
        "extract_data >> transform_data >> load_data"
    ]
