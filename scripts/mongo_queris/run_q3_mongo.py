"""
Task 5: Full-Text Search on Products
Execute q3.js via pymongo and display results

IMPORTANT: Uses Q2 results (hardcoded) from MongoDB q2.js output
"""

from pymongo import MongoClient
import pandas as pd
import os
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

MONGO_URI = 'mongodb://localhost:27017/'
DB_NAME = 'bigdata'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..','..', 'output', 'mongo_queries_results'))

os.makedirs(OUTPUT_DIR, exist_ok=True)

TARGET_USER_ID = 560126337

# Q2 Results - Product IDs (from MongoDB q2.js output)
Q2_PRODUCT_IDS = [
    1004749, 1005232, 26401412, 2900926, 2600218,
    1005265, 3601060, 1005008, 1004905, 1004751,
    2900864, 1004708, 1004749, 1004751, 26300087,
    1005173, 3600253, 1801906, 3801134, 1005203
]

# Q2 Categories (from MongoDB q2.js output - denormalized)
Q2_CATEGORIES = [
    'electronics.smartphone',
    'construction.tools.light',
    'auto.accessories.compressor',
    'furniture.bedroom.blanket',
    'appliances.kitchen.washer',
    'appliances.kitchen.coffee_grinder',
    'appliances.personal.massager',
    'appliances.iron'
]


# =============================================================================
# QUERY FUNCTION
# =============================================================================

def execute_query(js_file, db):
    """
    Execute MongoDB aggregation pipeline for full-text search
    Uses hardcoded Q2 results for performance
    """

    # Extract unique keywords from Q2 categories
    keywords = set()
    for category in Q2_CATEGORIES:
        if category:
            keywords.update(category.split('.'))
    keywords = list(keywords)

    # MongoDB aggregation pipeline
    pipeline = [
        # Stage 1: Create keywords array

        {
            '$addFields': {
                'q2_categories': Q2_CATEGORIES,
                'q2_product_ids': Q2_PRODUCT_IDS
            }
        },
        {
            '$unwind': '$q2_categories'
        },
        {
            '$addFields': {
                'category_parts': {'$split': ['$q2_categories', '.']}
            }
        },
        {
            '$unwind': '$category_parts'
        },
        {
            '$group': {
                '_id': None,
                'keywords': {'$addToSet': '$category_parts'},
                'q2_product_ids': {'$first': '$q2_product_ids'}
            }
        },

        # Stage 2: Lookup products matching keywords
        {
            '$lookup': {
                'from': 'events',
                'let': {
                    'keywords': '$keywords',
                    'q2_ids': '$q2_product_ids'
                },
                'pipeline': [
                    {
                        '$match': {
                            '$expr': {
                                '$and': [
                                    {'$ne': ['$category_code', None]},
                                    {'$ne': ['$category_code', '']}
                                ]
                            }
                        }
                    },
                    {
                        '$addFields': {
                            'category_parts': {'$split': ['$category_code', '.']}
                        }
                    },
                    {
                        '$unwind': '$category_parts'
                    },
                    {
                        '$match': {
                            '$expr': {
                                '$in': ['$category_parts', '$$keywords']
                            }
                        }
                    },
                    {
                        '$group': {
                            '_id': {
                                'product_id': '$product_id',
                                'brand': '$brand',
                                'category_code': '$category_code'
                            },
                            'matched_keywords': {'$addToSet': '$category_parts'}
                        }
                    },
                    {
                        '$match': {
                            '$expr': {
                                '$not': {'$in': ['$_id.product_id', '$$q2_ids']}
                            }
                        }
                    }
                ],
                'as': 'product_matches'
            }
        },
        {'$unwind': '$product_matches'},

        # Stage 3: Calculate relevance score
        {
            '$project': {
                '_id': 0,
                'product_id': '$product_matches._id.product_id',
                'brand': '$product_matches._id.brand',
                'category_code': '$product_matches._id.category_code',
                'matched_keywords': '$product_matches.matched_keywords',
                'relevance_score': {'$size': '$product_matches.matched_keywords'}
            }
        },

        # Stage 4: Add match quality
        {
            '$addFields': {
                'match_quality': {
                    '$switch': {
                        'branches': [
                            {'case': {'$gte': ['$relevance_score', 3]}, 'then': 'High Match'},
                            {'case': {'$gte': ['$relevance_score', 2]}, 'then': 'Medium Match'}
                        ],
                        'default': 'Low Match'
                    }
                }
            }
        },

        # Stage 5: Sort and limit
        {
            '$sort': {'relevance_score': -1, 'product_id': 1}
        },
        {'$limit': 20},

        # Stage 6: Final projection
        {
            '$project': {
                'product_id': 1,
                'brand': 1,
                'category_code': 1,
                'relevance_score': 1,
                'matched_keywords': 1,
                'match_quality': 1
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
    print(" Task 5: Full-Text Search on Products")
    print("=" * 80)

    # Connect to MongoDB
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    print(f" Connected to MongoDB ({DB_NAME})")
    print()

    # Execute query
    js_file = os.path.join(SCRIPT_DIR, 'q3.js')
    print(f"Query definition: {js_file}")
    print(f"Target User ID: {TARGET_USER_ID}")
    print(f"Q2 Products excluded: {len(Q2_PRODUCT_IDS)}")
    print(f"Q2 Categories used: {len(Q2_CATEGORIES)}")
    print(f"Executing pipeline in Python (reliable execution)")
    print()

    start_time = datetime.now()
    df = execute_query(js_file, db)
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
        avg_score = df['relevance_score'].mean()
        high_count = len(df[df['match_quality'] == 'High Match'])
        med_count = len(df[df['match_quality'] == 'Medium Match'])
        low_count = len(df[df['match_quality'] == 'Low Match'])

        print(f"Average relevance score: {avg_score:.2f}")
        print(f"High Match: {high_count}")
        print(f"Medium Match: {med_count}")
        print(f"Low Match: {low_count}")

    client.close()
    print("\n Connection closed")


if __name__ == "__main__":
    main()