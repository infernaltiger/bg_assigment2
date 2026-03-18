
"""
Hybrid Model Data Loading Script
Load data to appropriate databases based on data type
"""

import pandas as pd
import os
from pymongo import MongoClient
from neo4j import GraphDatabase
import psycopg2

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..', 'output', 'cleaned'))

# PostgreSQL (Core reference data)
PSQL_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'bigdata_hybrid',
    'user': 'postgres',
    'password': ''
}

# MongoDB (Events, Messages)
MONGO_URI = 'mongodb://localhost:27017/'
MONGO_DB = 'bigdata_hybrid'

# Neo4j (Social graph)
NEO4J_URI = 'bolt://localhost:7687'
NEO4J_USER = 'neo4j'
NEO4J_PASSWORD = 'password'
NEO4J_DB = 'neo4j'


# =============================================================================
# LOADING FUNCTIONS
# =============================================================================

def load_to_postgresql():
    #Load reference data to PostgreSQL
    print("\n" + "=" * 80)
    print(" LOADING TO POSTGRESQL (Reference Data)")
    print("=" * 80)

    conn = psycopg2.connect(**PSQL_CONFIG)
    cur = conn.cursor()

    # Load users (unique list)
    messages_df = pd.read_csv(os.path.join(DATA_DIR, 'messages_cleaned.csv'), low_memory=False)
    user_ids = messages_df['user_id'].dropna().unique()

    print(f"  Loading {len(user_ids):,} users...")
    for uid in user_ids:
        cur.execute(
            "INSERT INTO users (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING",
            (int(uid),)
        )

    conn.commit()
    print(f" Users loaded")

    # Load products
    events_df = pd.read_csv(os.path.join(DATA_DIR, 'events_cleaned.csv'))
    products = events_df[['product_id', 'brand']].drop_duplicates()

    print(f"  Loading {len(products):,} products...")
    for _, row in products.iterrows():
        if pd.notna(row['product_id']):
            cur.execute(
                "INSERT INTO products (product_id, brand) VALUES (%s, %s) ON CONFLICT (product_id) DO NOTHING",
                (int(row['product_id']), row['brand'] if pd.notna(row['brand']) else None)
            )

    conn.commit()
    print(f" Products loaded")

    cur.close()
    conn.close()


def load_to_mongodb():
    #Load events and messages to MongoDB
    print("\n" + "=" * 80)
    print(" LOADING TO MONGODB (Events + Messages)")
    print("=" * 80)

    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]

    # Load events
    events_df = pd.read_csv(os.path.join(DATA_DIR, 'events_cleaned.csv'))
    events_df['event_time'] = pd.to_datetime(events_df['event_time'])

    print(f"  Loading {len(events_df):,} events...")
    events = events_df.to_dict('records')
    db.events.insert_many(events)
    print(f"  Events loaded")

    # Load messages
    messages_df = pd.read_csv(os.path.join(DATA_DIR, 'messages_cleaned.csv'), low_memory=False)

    print(f"  Loading {len(messages_df):,} messages...")
    messages = messages_df.to_dict('records')
    db.messages.insert_many(messages)
    print(f"  Messages loaded")

    # Create indexes
    db.events.create_index([('user_id', 1)])
    db.events.create_index([('product_id', 1)])
    db.events.create_index([('event_type', 1)])

    db.messages.create_index([('user_id', 1)])
    db.messages.create_index([('campaign_id', 1)])
    db.messages.create_index([('is_purchased', 1)])

    print(f" Indexes created")

    client.close()


def load_to_neo4j():
    #Load social graph to Neo4j
    print("\n" + "=" * 80)
    print(" LOADING TO NEO4J (Social Graph)")
    print("=" * 80)

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    with driver.session(database=NEO4J_DB) as session:
        # Load users
        messages_df = pd.read_csv(os.path.join(DATA_DIR, 'messages_cleaned.csv'), low_memory=False)
        user_ids = messages_df['user_id'].dropna().unique()

        print(f"  Loading {len(user_ids):,} users...")
        for uid in user_ids:
            session.run("MERGE (u:User {user_id: $uid})", uid=int(uid))
        print(f" Users loaded")

        # Load friends
        friends_df = pd.read_csv(os.path.join(DATA_DIR, 'friends_cleaned.csv'))

        print(f"  Loading {len(friends_df):,} friendships...")
        for _, row in friends_df.iterrows():
            session.run("""
                MATCH (u1:User {user_id: $uid1})
                MATCH (u2:User {user_id: $uid2})
                MERGE (u1)-[:FRIENDS_WITH]->(u2)
            """, uid1=int(row['user_id']), uid2=int(row['friend_id']))
        print(f" Friendships loaded")

    driver.close()


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print(" HYBRID MODEL DATA LOADING")
    print("=" * 80)

    try:
        load_to_postgresql()
        load_to_mongodb()
        load_to_neo4j()

        print("\n" + "=" * 80)
        print(" HYBRID MODEL DATA LOADING COMPLETED!")
        print("=" * 80)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        raise


if __name__ == "__main__":
    main()