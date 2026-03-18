
"""
Task 3: Campaign Effectiveness Analysis
Execute q1.cypher via neo4j driver and display results
"""

from neo4j import GraphDatabase
import pandas as pd
import os
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

# Neo4j connection
NEO4J_URI = 'bolt://localhost:7687'
NEO4J_USER = 'neo4j'
NEO4J_PASSWORD = ''  #i will make this empty, please use your own password, i don't want to show mine
DATABASE = 'neo4j'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..', 'output', 'neo4j_queries_results'))

os.makedirs(OUTPUT_DIR, exist_ok=True)


# =============================================================================
# QUERY FUNCTION
# =============================================================================

def execute_query(cypher_file):
    #Execute Cypher file and return results as DataFrame"""

    # Read Cypher file
    with open(cypher_file, 'r', encoding='utf-8') as f:
        query = f.read()

    # Connect and execute
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    with driver.session(database=DATABASE) as session:
        result = session.run(query)
        records = list(result)

        # Convert to DataFrame
        df = pd.DataFrame([dict(record) for record in records])

    driver.close()
    return df


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print(" Task 3: Campaign Effectiveness Analysis")
    print("=" * 80)
    print()

    # Execute query
    cypher_file = os.path.join(SCRIPT_DIR, 'q1.cypher')
    print(f"Executing: {cypher_file}")

    start_time = datetime.now()
    df = execute_query(cypher_file)
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
    print(f"\n Results saved to: {output_file}")

    # Summary statistics
    print("\n" + "=" * 80)
    print(" Summary Statistics")
    print("=" * 80)
    print(f"Total campaigns analyzed: {len(df)}")
    if len(df) > 0:
        print(f"Average conversion rate: {df['conversion_rate'].mean():.2f}%")
        print(f"Total message recipients: {df['message_recipients'].sum():,}")
        print(f"Total purchases: {df['purchases'].sum():,}")


if __name__ == "__main__":
    main()