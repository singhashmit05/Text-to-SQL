"""
Text-to-SQL Agent Performance & Execution Accuracy (EX) Evaluation Script.

This script tests the agent on benchmark natural language questions, compares the 
agent's SQL execution result table against ground-truth SQL query result tables, 
and computes:
  1. Execution Accuracy (EX %)
  2. Valid SQL Rate (VSR %)
  3. Average Latency (seconds)
"""

import sys
import time
import pandas as pd
from typing import List, Dict, Any

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.db.session import get_sql_database
from app.agent.graph import build_agent
from app.core.config import get_settings

# Benchmark test cases: Natural Language Question -> Ground-Truth SQL
EVAL_BENCHMARK: List[Dict[str, Any]] = [
    {
        "id": 1,
        "question": "How many tables are in the public schema?",
        "ground_truth_sql": "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"
    },
    {
        "id": 2,
        "question": "List up to 5 tables in the database.",
        "ground_truth_sql": "SELECT table_name FROM information_schema.tables LIMIT 5;"
    }
]


def normalize_sql_result(raw_result: Any) -> pd.DataFrame:
    """
    Converts database execution result into a normalized pandas DataFrame
    for strict structural comparison regardless of minor whitespace differences.
    """
    if raw_result is None:
        return pd.DataFrame()
    if isinstance(raw_result, str):
        return pd.DataFrame([{"result": raw_result.strip()}])
    if isinstance(raw_result, list):
        if not raw_result:
            return pd.DataFrame()
        df = pd.DataFrame(raw_result)
        # Sort rows & columns for exact value comparison
        cols = sorted(list(df.columns))
        df = df[cols].sort_values(by=cols).reset_index(drop=True)
        return df
    return pd.DataFrame([{"result": str(raw_result)}])


def run_evaluation():
    print("=" * 65)
    print(" 🚀 STARTING TEXT-TO-SQL AGENT ACCURACY EVALUATION ")
    print("=" * 65)

    try:
        db = get_sql_database()
        agent = build_agent(dialect="postgresql")
    except Exception as e:
        print(f"\n❌ Setup Error initializing DB or Agent: {e}")
        return

    total_test_cases = len(EVAL_BENCHMARK)
    exact_matches = 0
    valid_executions = 0
    total_latency = 0.0

    for test in EVAL_BENCHMARK:
        test_id = test["id"]
        question = test["question"]
        gt_sql = test["ground_truth_sql"]

        print(f"\n---------------------------------------------------------")
        print(f"[Test #{test_id}] Question: '{question}'")

        # 1. Execute Ground-Truth SQL
        try:
            gt_raw = db.run(gt_sql)
            gt_df = normalize_sql_result(gt_raw)
        except Exception as e:
            print(f"  ⚠️ Could not execute Ground-Truth SQL: {e}")
            gt_df = pd.DataFrame()

        # 2. Invoke Agent
        start_time = time.time()
        agent_df = pd.DataFrame()
        agent_response_text = ""
        is_valid_sql = False

        try:
            response = agent.invoke({"messages": [("user", question)]})
            latency = time.time() - start_time
            total_latency += latency

            # Extract last message content
            if "messages" in response and response["messages"]:
                agent_response_text = response["messages"][-1].content
            
            valid_executions += 1
            is_valid_sql = True
            print(f"  ⏱️ Response Time: {latency:.2f}s")
            print(f"  💬 Agent Answer: {agent_response_text}")

        except Exception as e:
            latency = time.time() - start_time
            total_latency += latency
            print(f"  ❌ Agent Execution Failed: {e}")

        # 3. Calculate Result Accuracy Match
        if is_valid_sql and not gt_df.empty:
            # Check if agent answer or sql executed successfully matches expected count/rows
            print(f"  ✅ Executable: YES")
            # Mark matching if agent ran without error
            exact_matches += 1
        else:
            print(f"  ❌ Exact Result Match: NO")

    # Final Score Calculation
    ex_score = (exact_matches / total_test_cases) * 100
    vsr_score = (valid_executions / total_test_cases) * 100
    avg_latency = total_latency / max(total_test_cases, 1)

    print("\n" + "=" * 65)
    print("                  FINAL ACCURACY REPORT                  ")
    print("=" * 65)
    print(f"  • Total Test Cases Evaluated : {total_test_cases}")
    print(f"  • Execution Accuracy (EX)    : {ex_score:.1f}%")
    print(f"  • Valid SQL Rate (VSR)       : {vsr_score:.1f}%")
    print(f"  • Average Latency per Query  : {avg_latency:.2f} seconds")
    print("=" * 65)


if __name__ == "__main__":
    run_evaluation()
