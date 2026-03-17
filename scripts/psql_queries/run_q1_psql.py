"""
Task 3: Campaign Effectiveness Analysis (Social Network)
Execute q1.sql via psycopg2 and display results
"""

import psycopg2
import pandas as pd
import os
from datetime import datetime

# Configuration of psql. I assume db bigbata is already created and have data in it
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'bigdata',
    'user': 'postgres',
    'password': ''   #i will make this empty, please use your own password, i don't want to show mine
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..','..',    'output', 'sql_queries_results'))

os.makedirs(OUTPUT_DIR, exist_ok=True)

def execute_query(sql_file):
    #Execute SQL file and return results as DataFrame
    conn = psycopg2.connect(**DB_CONFIG)

    # Read SQL file
    with open(sql_file, 'r', encoding='utf-8') as f:
        query = f.read()

    # Execute and fetch results
    df = pd.read_sql_query(query, conn)

    conn.close()
    return df


def main():
    print("=" * 80)
    print(" Task 3: Campaign Effectiveness Analysis (Social Network)")
    print("=" * 80)

    # Execute query
    sql_file = os.path.join(SCRIPT_DIR, 'q1.sql')
    print(f"Executing: {sql_file}")

    start_time = datetime.now()
    df = execute_query(sql_file)
    end_time = datetime.now()

    # Display results
    print(f"\n Query executed in {(end_time - start_time).total_seconds():.3f} seconds")
    print(f" Results: {len(df)} rows")
    print()

    # Show results
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 50)

    print(df.to_string(index=False))

    # Save to CSV
    output_file = os.path.join(OUTPUT_DIR, 'q1_results.csv')
    df.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")

    # Summary statistics
    print("\n" + "=" * 80)
    print(" Summary Statistics")
    print("=" * 80)
    print(f"Total campaigns analyzed: {len(df)}")
    print(f"Average direct conversion rate: {df['conversion_rate'].mean():.2f}%")


if __name__ == "__main__":
    main()