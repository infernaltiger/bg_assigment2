"""
Task 5: Full-Text Search on Products
Execute q3.cypher via neo4j driver and display results
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
NEO4J_PASSWORD = '' #i will make this empty, please use your own password, i don't want to show mine
DATABASE = 'neo4j'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..', 'output', 'neo4j_queries_results'))

os.makedirs(OUTPUT_DIR, exist_ok=True)

# User ID (for consistency with q2, though not used in hardcoded version)
USER_ID = 560126337


# =============================================================================
# QUERY FUNCTION
# =============================================================================

def execute_query(cypher_file, user_id=USER_ID):
    #Execute Cypher file and return results as DataFrame

    # Read Cypher file
    with open(cypher_file, 'r', encoding='utf-8') as f:
        query = f.read()

    # Connect and execute
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    with driver.session(database=DATABASE) as session:
        # Execute with parameter (even though not used in hardcoded version)
        result = session.run(query, user_id=user_id)
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
    print(" Task 5: Full-Text Search on Products")
    print("=" * 80)


    # Execute query
    cypher_file = os.path.join(SCRIPT_DIR, 'q3.cypher')
    print(f"Executing: {cypher_file}")

    start_time = datetime.now()
    df = execute_query(cypher_file, USER_ID)
    end_time = datetime.now()

    # Display results
    print(f"\n Query executed in {(end_time - start_time).total_seconds():.3f} seconds")
    print(f" Results: {len(df)} products found")
    print()

    # Show results
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 50)

    print(df.to_string(index=False))

    # Save to CSV
    output_file = os.path.join(OUTPUT_DIR, 'q3_results.csv')
    df.to_csv(output_file, index=False)
    print(f"\n Results saved to: {output_file}")

    # Summary statistics
    print("\n" + "=" * 80)
    print(" Summary Statistics")
    print("=" * 80)
    print(f"Total products found: {len(df)}")
    if len(df) > 0:
        print(f"High Match: {len(df[df['match_quality'] == 'High Match'])}")
        print(f"Medium Match: {len(df[df['match_quality'] == 'Medium Match'])}")
        print(f"Low Match: {len(df[df['match_quality'] == 'Low Match'])}")
        print(f"Average relevance score: {df['relevance_score'].mean():.2f}")


if __name__ == "__main__":
    main()