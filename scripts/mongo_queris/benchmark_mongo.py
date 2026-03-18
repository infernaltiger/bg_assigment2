#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB Benchmark Script
Assignment 2 - Big Data Storage & Retrieval

Run each query 5 times and record execution times.
Uses SAME pipeline functions as run_*.py scripts for fair comparison.
"""

from pymongo import MongoClient
import pandas as pd
import os
import time
import sys

# =============================================================================
# CONFIGURATION
# =============================================================================

MONGO_URI = 'mongodb://localhost:27017/'
DB_NAME = 'bigdata'
NUM_RUNS = 5

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..','..', 'output', 'mongo_queries_results'))

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Add SCRIPT_DIR to path to import run_*.py modules
sys.path.insert(0, SCRIPT_DIR)

# =============================================================================
# IMPORT PIPELINE FUNCTIONS FROM RUN SCRIPTS
# =============================================================================

# Import execute_query functions from run scripts (they have the pipelines)
from run_q1_mongo import execute_query as q1_execute_query
from run_q2_mongo import execute_query as q2_execute_query
from run_q3_mongo import execute_query as q3_execute_query


# =============================================================================
# BENCHMARK FUNCTIONS
# =============================================================================

def benchmark_query_timed(name, execute_func, db):
    """Run query multiple times and return statistics"""
    print(f"\n{'=' * 60}")
    print(f" Benchmarking: {name}")
    print(f"{'=' * 60}")

    times = []
    for i in range(NUM_RUNS):
        start_time = time.perf_counter()

        # Execute query (same as run script)
        _ = execute_func(None, db)  # js_file=None, we use pipeline from function

        end_time = time.perf_counter()
        exec_time = end_time - start_time
        times.append(exec_time)
        print(f"  Run {i + 1}/{NUM_RUNS}: {exec_time:.4f} seconds")

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    print(f"\n  Statistics:")
    print(f"    Average: {avg_time:.4f} seconds")
    print(f"    Min: {min_time:.4f} seconds")
    print(f"    Max: {max_time:.4f} seconds")

    return {
        'query': name,
        'avg': avg_time,
        'min': min_time,
        'max': max_time,
        'runs': times
    }


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print(" MongoDB Benchmark (5 runs per query)")
    print("=" * 80)
    print(f" Number of runs: {NUM_RUNS}")
    print()

    # Connect to MongoDB
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    print(f"Connected to MongoDB ({DB_NAME})")

    results = []

    # Benchmark each query
    queries = [
        ('Task 3 - Campaign Analysis', q1_execute_query),
        ('Task 4 - Recommendations', q2_execute_query),
        ('Task 5 - Full-Text Search', q3_execute_query),
    ]

    for name, execute_func in queries:
        result = benchmark_query_timed(name, execute_func, db)
        results.append(result)

    # Summary table
    print("\n" + "=" * 80)
    print(" BENCHMARK SUMMARY")
    print("=" * 80)

    summary_df = pd.DataFrame(results)
    summary_df = summary_df[['query', 'avg', 'min', 'max']]
    summary_df.columns = ['Query', 'Avg (s)', 'Min (s)', 'Max (s)']

    print(summary_df.to_string(index=False))

    # Save results
    output_file = os.path.join(OUTPUT_DIR, 'benchmark_mongo_results.csv')
    summary_df.to_csv(output_file, index=False)
    print(f"\n Results saved to: {output_file}")

    # Save detailed results
    detailed_file = os.path.join(OUTPUT_DIR, 'benchmark_mongo_detailed.csv')
    with open(detailed_file, 'w') as f:
        f.write('Query,Run,Time (s)\n')
        for result in results:
            for i, time_val in enumerate(result['runs']):
                f.write(f"{result['query']},{i + 1},{time_val:.4f}\n")
    print(f" Detailed results saved to: {detailed_file}")

    client.close()
    print("\n Connection closed")


if __name__ == "__main__":
    main()