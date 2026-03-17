"""
Task 4: Personalized Product Recommendations
Execute q2.sql via psycopg2 and display results
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
OUTPUT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..','..', 'output', 'sql_queries_results'))

os.makedirs(OUTPUT_DIR, exist_ok=True)


def execute_query(sql_file, user_id=560126337):
    #Execute SQL file with user_id parameter
    conn = psycopg2.connect(**DB_CONFIG)

    # Read SQL file
    with open(sql_file, 'r', encoding='utf-8') as f:
        query = f.read()

    # Replace user_id placeholder
    query = query.replace('560126337', str(user_id))

    # Execute and fetch results
    df = pd.read_sql_query(query, conn)

    conn.close()
    return df


def main():
    print("=" * 80)
    print(" Task 4: Personalized Product Recommendations")
    print("=" * 80)


    # User ID to analyze, change it depending on witch user you wabt to check
    # Run find_active_user to find users with most activity
    user_id = 560126337
    print(f"Analyzing recommendations for user_id: {user_id}")
    print()

    # Execute query
    sql_file = os.path.join(SCRIPT_DIR, 'q2.sql')
    print(f"Executing: {sql_file}")

    start_time = datetime.now()
    df = execute_query(sql_file, user_id)
    end_time = datetime.now()

    # Display results
    print(f"\n Query executed in {(end_time - start_time).total_seconds():.3f} seconds")
    print(f" Results: {len(df)} recommended products")
    print()

    # Show results
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)

    print(df.to_string(index=False))

    # Save to CSV
    output_file = os.path.join(OUTPUT_DIR, 'q2_results.csv')
    df.to_csv(output_file, index=False)
    print(f"\n Results saved to: {output_file}")

    # Summary statistics
    print("\n" + "=" * 80)
    print(" Summary Statistics")
    print("=" * 80)
    print(f"Total recommended products: {len(df)}")
    print(f"High recommendations: {len(df[df['recommendation_level'] == 'High Recommendation'])}")
    print(f"Medium recommendations: {len(df[df['recommendation_level'] == 'Medium Recommendation'])}")
    print(f"Low recommendations: {len(df[df['recommendation_level'] == 'Low Recommendation'])}")
    print(f"Average interaction score: {df['total_score'].mean():.2f}")


if __name__ == "__main__":
    main()