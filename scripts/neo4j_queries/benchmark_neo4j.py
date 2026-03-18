
"""
Neo4j Benchmark Script
Run each query 5 times and record execution times
"""

from neo4j import GraphDatabase
import pandas as pd
import os
import time

# =============================================================================
# CONFIGURATION
# =============================================================================

# Neo4j connection
NEO4J_URI = 'bolt://localhost:7687'
NEO4J_USER = 'neo4j'
NEO4J_PASSWORD = '' #i will make this empty, please use your own password, i don't want to show mine
DATABASE = 'neo4j'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..','..', 'output', 'neo4j_queries_results'))

os.makedirs(OUTPUT_DIR, exist_ok=True)

NUM_RUNS = 5

# User ID for Q2/Q3 (consistent with other benchmarks)
USER_ID = 560126337


# =============================================================================
# BENCHMARK FUNCTIONS
# =============================================================================

def execute_query_timed(query, user_id=USER_ID):
    #Execute query and return execution time in seconds

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    with driver.session(database=DATABASE) as session:
        start_time = time.perf_counter()

        # Execute query with parameter
        result = session.run(query, user_id=user_id)
        _ = list(result)  # Fetch all to ensure complete execution

        end_time = time.perf_counter()

    driver.close()

    return end_time - start_time


def benchmark_query(name, cypher_file, user_id=USER_ID):
    #Run query multiple times and return statistics

    print(f"\n{'=' * 60}")
    print(f" Benchmarking: {name}")
    print(f"{'=' * 60}")

    # Read Cypher file
    with open(cypher_file, 'r', encoding='utf-8') as f:
        query = f.read()

    # Run multiple times
    times = []
    for i in range(NUM_RUNS):
        exec_time = execute_query_timed(query, user_id)
        times.append(exec_time)
        print(f"  Run {i + 1}/{NUM_RUNS}: {exec_time:.4f} seconds")

    # Statistics
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
    print(" Neo4j Benchmark (5 runs per query)")
    print("=" * 80)
    print(f" Number of runs: {NUM_RUNS}")
    print(f" User ID: {USER_ID}")
    print()

    results = []

    # Benchmark each query
    queries = [
        ('Task 3 - Campaign Analysis', 'q1.cypher'),
        ('Task 4 - Recommendations', 'q2.cypher'),
        ('Task 5 - Full-Text Search', 'q3.cypher'),
    ]

    for name, cypher_file in queries:
        result = benchmark_query(name, os.path.join(SCRIPT_DIR, cypher_file), USER_ID)
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
    output_file = os.path.join(OUTPUT_DIR, 'benchmark_neo4j_results.csv')
    summary_df.to_csv(output_file, index=False)
    print(f"\n Results saved to: {output_file}")

    # Save detailed results
    detailed_file = os.path.join(OUTPUT_DIR, 'benchmark_neo4j_detailed.csv')
    with open(detailed_file, 'w') as f:
        f.write('Query,Run,Time (s)\n')
        for result in results:
            for i, time_val in enumerate(result['runs']):
                f.write(f"{result['query']},{i + 1},{time_val:.4f}\n")
    print(f" Detailed results saved to: {detailed_file}")


if __name__ == "__main__":
    main()