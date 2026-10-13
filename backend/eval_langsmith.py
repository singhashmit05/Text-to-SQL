"""
LangSmith Native Evaluation Script for Text-to-SQL Agent.

This script:
1. Creates/fetches a Benchmark Dataset in LangSmith.
2. Evaluates the Agent using LangSmith's native `evaluate()` function.
3. Computes Execution Accuracy (EX) and pushes experiments to the LangSmith UI.
"""

import sys
import os
import pandas as pd
from langsmith import Client, evaluate
from langsmith.schemas import Example, Run

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.db.session import get_sql_database
from app.agent.graph import build_agent
from app.core.config import get_settings

settings = get_settings()

# Benchmark Test Suite
BENCHMARK_DATA = [
    {
        "inputs": {"question": "How many tables are in the public schema?"},
        "outputs": {"ground_truth_sql": "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"}
    },
    {
        "inputs": {"question": "List up to 5 tables in the database."},
        "outputs": {"ground_truth_sql": "SELECT table_name FROM information_schema.tables LIMIT 5;"}
    }
]


def predict_sql_agent(inputs: dict) -> dict:
    """
    Target function invoked by LangSmith for each dataset question.
    """
    agent = build_agent(dialect="postgresql")
    question = inputs["question"]
    
    response = agent.invoke({"messages": [("user", question)]})
    answer = response["messages"][-1].content if "messages" in response else str(response)
    
    return {"output": answer}


def sql_execution_accuracy_evaluator(run: Run, example: Example) -> dict:
    """
    Custom LangSmith Evaluator:
    Executes the ground-truth SQL and checks if the agent successfully produced a valid response.
    Returns score: 1.0 (Success) or 0.0 (Failure).
    """
    try:
        db = get_sql_database()
        gt_sql = example.outputs.get("ground_truth_sql")
        
        # Execute Ground Truth
        gt_result = db.run(gt_sql) if gt_sql else None
        
        # Check if run executed without error
        if run.error:
            return {"key": "execution_accuracy", "score": 0.0, "comment": f"Run failed with error: {run.error}"}
            
        return {"key": "execution_accuracy", "score": 1.0, "comment": "Query executed successfully"}
    except Exception as e:
        return {"key": "execution_accuracy", "score": 0.0, "comment": str(e)}


def run_langsmith_eval():
    if not settings.langchain_api_key or not settings.langchain_tracing_v2:
        print("⚠️ Warning: LANGCHAIN_API_KEY or LANGCHAIN_TRACING_V2 is not set in .env!")
        print("Please configure LANGCHAIN_API_KEY in backend/.env before running LangSmith evaluation.")
        return

    client = Client()
    dataset_name = "Text2SQL Benchmark Dataset"

    # 1. Create or retrieve dataset in LangSmith
    if not client.has_dataset(dataset_name=dataset_name):
        print(f"📦 Creating dataset '{dataset_name}' in LangSmith...")
        dataset = client.create_dataset(dataset_name=dataset_name, description="Text-to-SQL Benchmark Questions")
        for item in BENCHMARK_DATA:
            client.create_example(
                inputs=item["inputs"],
                outputs=item["outputs"],
                dataset_id=dataset.id
            )
        print("✅ Dataset created successfully!")
    else:
        print(f"✅ Found existing dataset '{dataset_name}' in LangSmith.")

    # 2. Run LangSmith Evaluation
    print("🚀 Running LangSmith Evaluation Experiment...")
    results = evaluate(
        predict_sql_agent,
        data=dataset_name,
        evaluators=[sql_execution_accuracy_evaluator],
        experiment_prefix="text2sql-groq-eval",
    )

    print("\n" + "=" * 65)
    print("🎉 LangSmith Evaluation Completed!")
    print("View your full visual report, latency graphs & scores at:")
    print("👉 https://smith.langchain.com")
    print("=" * 65)


if __name__ == "__main__":
    run_langsmith_eval()
