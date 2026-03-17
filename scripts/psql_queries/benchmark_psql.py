
"""
PostgreSQL Benchmark Script
Run each query 5 times and record execution times
"""

import psycopg2
import pandas as pd
import os
import time


#Configuration of psql. I assume db bigbata is already created and have data in it
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'bigdata',
    'user': 'postgres',
    'password': ''   #i will make this empty, please use your own password, i don't want to show mine
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..', 'output', 'sql_queries_results'))
os.makedirs(OUTPUT_DIR, exist_ok=True)
NUM_RUNS = 5


def execute_query_timed(query):
    #Execute query and return execution time in seconds
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    start_time = time.perf_counter()
    cur.execute(query)
    _ = cur.fetchall()  # Fetch all to ensure complete execution
    end_time = time.perf_counter()

    cur.close()
    conn.close()

    return end_time - start_time


def benchmark_query(name, sql_file, user_id=548203521):
    #Run query multiple times and return statistics
    print(f"\n{'=' * 60}")
    print(f" Benchmarking: {name}")
    print(f"{'=' * 60}")

    # Read SQL file
    with open(sql_file, 'r', encoding='utf-8') as f:
        query = f.read()

    # Replace user_id if present
    query = query.replace('548203521', str(user_id))

    # Run multiple times
    times = []
    for i in range(NUM_RUNS):
        exec_time = execute_query_timed(query)
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


def main():
    print("=" * 80)
    print(" PostgreSQL Benchmark (5 runs per query)")
    print("=" * 80)
    print(f" Number of runs: {NUM_RUNS}")

    results = []

    # Benchmark each query
    queries = [
        ('Task 3 - Campaign Analysis', 'q1.sql'),
        ('Task 4 - Recommendations', 'q2.sql'),
        ('Task 5 - Full-Text Search', 'q3.sql'),
    ]
    user_id = 560126337
    for name, sql_file in queries:
        result = benchmark_query(name, os.path.join(SCRIPT_DIR, sql_file), user_id)
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
    output_file = os.path.join(OUTPUT_DIR, 'benchmark_psql_results.csv')
    summary_df.to_csv(output_file, index=False)
    print(f"\n Results saved to: {output_file}")

    # Save detailed results
    detailed_file = os.path.join(OUTPUT_DIR, 'benchmark_psql_detailed.csv')
    with open(detailed_file, 'w') as f:
        f.write('Query,Run,Time (s)\n')
        for result in results:
            for i, time_val in enumerate(result['runs']):
                f.write(f"{result['query']},{i + 1},{time_val:.4f}\n")
    print(f" Detailed results saved to: {detailed_file}")


if __name__ == "__main__":
    main()