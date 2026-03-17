"""
Task 4: Personalized Product Recommendations
Execute q2.js via pymongo and display results
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
OUTPUT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..','..', 'output', 'mongo_queries_results'))

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Target user ID (same as in q2.sql for comparison)
TARGET_USER_ID = 560126337


# =============================================================================
# QUERY FUNCTION
# =============================================================================

def execute_query(js_file, db):
    """
    Execute MongoDB aggregation pipeline for product recommendations

    Pipeline is defined in q1.js file, but we execute it directly in Python
    for reliability (i had problems with parsing JS format into python so i made the same query here )
    """

    # MongoDB aggregation pipeline (same as in q2.js)
    pipeline = [
        # Stage 1: Match user's events
        {
            '$match': {
                'user_id': TARGET_USER_ID
            }
        },

        # Stage 2: Calculate weighted interaction score per product
        {
            '$group': {
                '_id': {
                    'product_id': '$product_id',
                    'brand': '$brand',
                    'category_code': '$category_code'
                },
                'interaction_score': {
                    '$sum': {
                        '$switch': {
                            'branches': [
                                {'case': {'$eq': ['$event_type', 'purchase']}, 'then': 3},
                                {'case': {'$eq': ['$event_type', 'cart']}, 'then': 2},
                                {'case': {'$eq': ['$event_type', 'view']}, 'then': 1}
                            ],
                            'default': 0
                        }
                    }
                },
                'interaction_count': {'$sum': 1},
                'avg_price': {'$avg': '$price'}
            }
        },

        # Stage 3: Get user's friends
        {
            '$lookup': {
                'from': 'users',
                'let': {'user_id': TARGET_USER_ID},
                'pipeline': [
                    {
                        '$match': {
                            '$expr': {'$eq': ['$user_id', '$$user_id']}
                        }
                    },
                    {
                        '$project': {'friends': 1}
                    }
                ],
                'as': 'user_data'
            }
        },
        {
            '$unwind': {
                'path': '$user_data',
                'preserveNullAndEmptyArrays': True
            }
        },

        # Stage 4: Lookup friends' purchase events
        {
            '$lookup': {
                'from': 'events',
                'let': {
                    'friend_ids': '$user_data.friends',
                    'product_id': '$_id.product_id'
                },
                'pipeline': [
                    {
                        '$match': {
                            '$expr': {
                                '$and': [
                                    {'$in': ['$user_id', '$$friend_ids']},
                                    {'$eq': ['$event_type', 'purchase']},
                                    {'$eq': ['$product_id', '$$product_id']}
                                ]
                            }
                        }
                    },
                    {
                        '$group': {
                            '_id': None,
                            'friend_score': {'$sum': 2},
                            'friend_count': {'$sum': 1}
                        }
                    }
                ],
                'as': 'friend_stats'
            }
        },
        {
            '$unwind': {
                'path': '$friend_stats',
                'preserveNullAndEmptyArrays': True
            }
        },

        # Stage 5: Calculate total scores
        {
            '$project': {
                'product_id': '$_id.product_id',
                'brand': '$_id.brand',
                'category_code': '$_id.category_code',
                'user_score': '$interaction_score',
                'friend_score': {'$ifNull': ['$friend_stats.friend_score', 0]},
                'total_score': {
                    '$add': [
                        '$interaction_score',
                        {'$ifNull': ['$friend_stats.friend_score', 0]}
                    ]
                },
                'total_interactions': {
                    '$add': [
                        '$interaction_count',
                        {'$ifNull': ['$friend_stats.friend_count', 0]}
                    ]
                },
                'avg_price': {'$round': ['$avg_price', 2]}
            }
        },

        # Stage 6: Add recommendation level
        {
            '$addFields': {
                'recommendation_level': {
                    '$switch': {
                        'branches': [
                            {'case': {'$gte': ['$total_score', 10]}, 'then': 'High Recommendation'},
                            {'case': {'$gte': ['$total_score', 5]}, 'then': 'Medium Recommendation'}
                        ],
                        'default': 'Low Recommendation'
                    }
                }
            }
        },

        # Stage 7: Sort and limit
        {
            '$sort': {'total_score': -1, 'total_interactions': -1}
        },
        {
            '$limit': 20
        },

        # Stage 8: Final projection
        {
            '$project': {
                '_id': 0,
                'product_id': 1,
                'brand': 1,
                'category_code': 1,
                'total_score': 1,
                'total_interactions': 1,
                'avg_price': 1,
                'recommendation_level': 1
            }
        }
    ]

    # Execute aggregation
    result = db.events.aggregate(pipeline, allowDiskUse=True)

    # Convert to DataFrame
    df = pd.DataFrame(list(result))

    return df


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print(" Task 4: Personalized Product Recommendations")
    print("=" * 80)


    # Connect to MongoDB
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    print(f" Connected to MongoDB ({DB_NAME})")
    print()

    # Execute query
    js_file = os.path.join(SCRIPT_DIR, 'q2.js')
    print(f"Query definition: {js_file}")
    print(f"Target User ID: {TARGET_USER_ID}")
    print(f" Executing pipeline in Python (reliable execution)")
    print()

    start_time = datetime.now()
    df = execute_query(js_file, db)
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
    print(f"Total recommendations: {len(df)}")
    if len(df) > 0:
        avg_score = df['total_score'].mean()
        high_count = len(df[df['recommendation_level'] == 'High Recommendation'])
        med_count = len(df[df['recommendation_level'] == 'Medium Recommendation'])
        low_count = len(df[df['recommendation_level'] == 'Low Recommendation'])

        print(f"Average total score: {avg_score:.2f}")
        print(f"High recommendations: {high_count}")
        print(f"Medium recommendations: {med_count}")
        print(f"Low recommendations: {low_count}")

    client.close()
    print("\n Connection closed")


if __name__ == "__main__":
    main()