
"""
Task 4: Personalized Product Recommendations
Execute q2.cypher via neo4j driver and display results
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

# User ID to analyze - same as always
USER_ID = 560126337


# =============================================================================
# QUERY FUNCTION
# =============================================================================

def execute_query(cypher_file, user_id=USER_ID):
    #Execute Cypher file with user_id parameter and return results as df

    # Read Cypher file
    with open(cypher_file, 'r', encoding='utf-8') as f:
        query = f.read()

    # Connect and execute
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    with driver.session(database=DATABASE) as session:
        # Execute with parameter
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
    print(" Task 4: Personalized Product Recommendations")
    print("=" * 80)


    # User ID to analyze
    print(f"Analyzing recommendations for user_id: {USER_ID}")
    print()

    # Execute query
    cypher_file = os.path.join(SCRIPT_DIR, 'q2.cypher')
    print(f"Executing: {cypher_file}")

    start_time = datetime.now()
    df = execute_query(cypher_file, USER_ID)
    end_time = datetime.now()

    # Display results
    print(f"\n Query executed in {(end_time - start_time).total_seconds():.3f} seconds")
    print(f" Results: {len(df)} recommended products")
    print()

    # Show results
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 50)

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
    if len(df) > 0:
        print(f"High recommendations: {len(df[df['recommendation_level'] == 'High Recommendation'])}")
        print(f"Medium recommendations: {len(df[df['recommendation_level'] == 'Medium Recommendation'])}")
        print(f"Low recommendations: {len(df[df['recommendation_level'] == 'Low Recommendation'])}")
        print(f"Average interaction score: {df['total_score'].mean():.2f}")


if __name__ == "__main__":
    main()