"""
Task 3: Campaign Effectiveness Analysis (Social Network)
Execute q1.js via pymongo and display results
"""

from pymongo import MongoClient
import pandas as pd
import os
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

# MongoDB connection. I assume db bigdata is already created and have data in it
MONGO_URI = 'mongodb://localhost:27017/'
DB_NAME = 'bigdata'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..', 'output', 'mongo_queries_results'))

os.makedirs(OUTPUT_DIR, exist_ok=True)


# =============================================================================
# QUERY FUNCTION
# =============================================================================

def execute_query(js_file, db):
    """
    Execute MongoDB aggregation pipeline

    Pipeline is defined in q1.js file, but we execute it directly in Python
    for reliability (i had problems with parsing JS format into python so i made the same query here )
    """

    # MongoDB aggregation pipeline (same as in q1.js)
    pipeline =  [
        # Stage 1: Match valid messages
        {
            '$match': {
                'campaign_id': {'$exists': True},
                'user_id': {'$exists': True},
                'campaign_data.id': {'$exists': True}
            }
        },

        # Stage 2: Group by user + campaign (deduplicate messages per user)
        {
            '$group': {
                '_id': {
                    'campaign_id': '$campaign_data.id',
                    'user_id': '$user_id'
                },
                'campaign_type': {'$first': '$campaign_data.campaign_type'},
                'channel': {'$first': '$campaign_data.channel'},
                'purchased': {'$max': '$engagement.is_purchased'}  # If ANY message = purchased
            }
        },

        # Stage 3: Group by campaign only (count unique users)
        {
            '$group': {
                '_id': {
                    'campaign_id': '$_id.campaign_id',
                    'campaign_type': '$campaign_type',
                    'channel': '$channel'
                },
                'message_recipients': {'$sum': 1},  # Each doc = 1 unique user
                'purchases': {'$sum': {'$cond': ['$purchased', 1, 0]}}
            }
        },

        # Stage 4: Calculate stats
        {
            '$project': {
                '_id': 0,
                'original_campaign_id': '$_id.campaign_id',
                'campaign_type': '$_id.campaign_type',
                'channel': '$_id.channel',
                'message_recipients': '$message_recipients',
                'purchases': '$purchases',
                'conversion_rate': {
                    '$round': [
                        {
                            '$multiply': [
                                {'$divide': ['$purchases', '$message_recipients']},
                                100
                            ]
                        },
                        2
                    ]
                }
            }
        },

        # Stage 5: Filter and sort
        {
            '$match': {'message_recipients': {'$gt': 0}}
        },
        {
            '$sort': {'purchases': -1}
        },
        {
            '$limit': 20
        }
    ]
    # Execute aggregation
    result = db.messages.aggregate(pipeline, allowDiskUse=True)

    # Convert to DataFrame
    df = pd.DataFrame(list(result))

    return df


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print(" Task 3: Campaign Effectiveness Analysis (Social Network)")
    print("=" * 80)

    # Connect to MongoDB
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    print(f" Connected to MongoDB ({DB_NAME})")
    print()

    # Execute query
    js_file = os.path.join(SCRIPT_DIR, 'q1.js')
    print(f"Query definition: {js_file}")
    print(f" Executing pipeline in Python (reliable execution)")
    print()

    start_time = datetime.now()
    df = execute_query(js_file, db)
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
        print(f"Total purchases: {df['purchases'].sum():,}")

    client.close()
    print("\n Connection closed")


if __name__ == "__main__":
    main()