
"""
This script creates all tables, constraints, and indexes based on the Hackolade schema.
SQL query in this script is based on exported schema in hackolade, just modified
This script:
1. Creates database 'bigdata' if it doesn't exist
2. Creates all tables, constraints, and indexes based on Hackolade schema


Run this BEFORE load_data_psql.py

"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os

# config
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# PostgreSQL default connection settings
# change depending on your params
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'postgres',  # Connect to default DB first
    'user': 'postgres',
    'password': ''  #i will make this empty, please use your own password, i don't want to show mine
}

TARGET_DB = 'bigdata' # Database we want to create

# =============================================================================
# DATABASE CONNECTION
# =============================================================================

def get_connection(database='postgres'):
    #Create PostgreSQL connection
    config = DB_CONFIG.copy()
    config['database'] = database
    conn = psycopg2.connect(**config)
    print(f" Connected to PostgreSQL ({database})")
    return conn


def execute_query(cur, query, description=""):
    #Execute query with error handling - running sql scripts through python need to be careful
    try:
        cur.execute(query)
        if description:
            print(f" {description}")
        return True
    except Exception as e:
        print(f" Error: {e}")
        print(f" Query: {query[:200]}...")
        return False

# =============================================================================
# CREATE DATABASE
# =============================================================================
def create_database():
    print("\n" + "=" * 80)
    print(" CREATING DATABASE")
    print("=" * 80)

    # Connect to postgres (default DB)
    conn = get_connection('postgres')
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)  # Required for CREATE DATABASE
    cur = conn.cursor()

    # Check if database exists
    cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{TARGET_DB}'")
    exists = cur.fetchone()

    if exists:
        print(f" Database '{TARGET_DB}' already exists")
    else:
        cur.execute(f"CREATE DATABASE {TARGET_DB}")
        print(f" Database '{TARGET_DB}' created")

    cur.close()
    conn.close()

    print(f"\n Database ready: {TARGET_DB}")


# =============================================================================
# 1. DROP EXISTING TABLES
# =============================================================================

def drop_existing_tables(cur):
    #Drop all tables in correct order
    print("\n" + "=" * 80)
    print(" DROPPING EXISTING TABLES")
    print("=" * 80)

    queries = [
        ("message_purchases", "DROP TABLE IF EXISTS message_purchases CASCADE"),
        ("message_negatives", "DROP TABLE IF EXISTS message_negatives CASCADE"),
        ("message_clicks", "DROP TABLE IF EXISTS message_clicks CASCADE"),
        ("message_opens", "DROP TABLE IF EXISTS message_opens CASCADE"),
        ("messages_device_info", "DROP TABLE IF EXISTS messages_device_info CASCADE"),
        ("messages_recipient", "DROP TABLE IF EXISTS messages_recipient CASCADE"),
        ("messages_category", "DROP TABLE IF EXISTS messages_category CASCADE"),
        ("email_providers", "DROP TABLE IF EXISTS email_providers CASCADE"),
        ("messages", "DROP TABLE IF EXISTS messages CASCADE"),
        ("campaign_position", "DROP TABLE IF EXISTS campaign_position CASCADE"),
        ("campaign_test", "DROP TABLE IF EXISTS campaign_test CASCADE"),
        ("campaign_hour_limit", "DROP TABLE IF EXISTS campaign_hour_limit CASCADE"),
        ("campaign_ab_test", "DROP TABLE IF EXISTS campaign_ab_test CASCADE"),
        ("campaigns", "DROP TABLE IF EXISTS campaigns CASCADE"),
        ("categories", "DROP TABLE IF EXISTS categories CASCADE"),
        ("products", "DROP TABLE IF EXISTS products CASCADE"),
        ("events", "DROP TABLE IF EXISTS events CASCADE"),
        ("friends", "DROP TABLE IF EXISTS friends CASCADE"),
        ("clients", "DROP TABLE IF EXISTS clients CASCADE"),
        ("users", "DROP TABLE IF EXISTS users CASCADE"),
    ]

    for table_name, query in queries:
        execute_query(cur, query, f"Dropped table: {table_name}")

    print("\n All existing tables dropped")


# =============================================================================
# 2. CREATE TABLES
# =============================================================================

def create_tables(cur):
    #Create all tables
    print("\n" + "=" * 80)
    print(" CREATING TABLES")
    print("=" * 80)

    tables = [
        # users
        ("""
        CREATE TABLE users (
            user_id BIGINT PRIMARY KEY
        )
        """, "Table: users"),

        # clients
        ("""
        CREATE TABLE clients (
            client_id BIGINT PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(user_id),
            user_device_id INTEGER NOT NULL,
            first_purchase_date DATE
        )
        """, "Table: clients"),

        # friends
        ("""
        CREATE TABLE friends (
            user_id BIGINT REFERENCES users(user_id),
            friend_id BIGINT REFERENCES users(user_id),
            PRIMARY KEY (user_id, friend_id)
        )
        """, "Table: friends"),

        # campaigns
        ("""
        CREATE TABLE campaigns (
            id BIGSERIAL PRIMARY KEY,
            campaign_id BIGINT NOT NULL,
            campaign_type VARCHAR(32) NOT NULL,
            channel VARCHAR(32) NOT NULL,
            topic VARCHAR(255),
            started_at TIMESTAMP,
            finished_at TIMESTAMP,
            total_count BIGINT,
            subject_length INTEGER,
            warmup_mode BOOLEAN DEFAULT FALSE,
            subject_with_personalization BOOLEAN DEFAULT FALSE,
            subject_with_deadline BOOLEAN DEFAULT FALSE,
            subject_with_emoji BOOLEAN DEFAULT FALSE,
            subject_with_bonuses BOOLEAN DEFAULT FALSE,
            subject_with_discount BOOLEAN DEFAULT FALSE,
            subject_with_saleout BOOLEAN DEFAULT FALSE
        )
        """, "Table: campaigns"),

        # campaign split tables
        ("""
        CREATE TABLE campaign_ab_test (
            campaign_id BIGINT NOT NULL REFERENCES campaigns(id),
            ab_test BOOLEAN NOT NULL
        )
        """, "Table: campaign_ab_test"),

        ("""
        CREATE TABLE campaign_hour_limit (
            campaign_id BIGINT NOT NULL REFERENCES campaigns(id),
            hour_limit NUMERIC(10, 2) NOT NULL
        )
        """, "Table: campaign_hour_limit"),

        ("""
        CREATE TABLE campaign_test (
            campaign_id BIGINT NOT NULL REFERENCES campaigns(id),
            is_test BOOLEAN NOT NULL
        )
        """, "Table: campaign_test"),

        ("""
        CREATE TABLE campaign_position (
            campaign_id BIGINT NOT NULL REFERENCES campaigns(id),
            position INTEGER NOT NULL   
        )
        """, "Table: campaign_position"),

        # messages
        ("""
        CREATE TABLE messages (
            id BIGINT PRIMARY KEY,
            message_id VARCHAR(64) NOT NULL,
            campaign_id BIGINT NOT NULL REFERENCES campaigns(id),
            user_id BIGINT NOT NULL REFERENCES users(user_id),
            message_type VARCHAR(32) NOT NULL ,
            channel VARCHAR(32) NOT NULL ,
            date DATE NOT NULL,
            sent_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            is_opened BOOLEAN DEFAULT FALSE,
            is_clicked BOOLEAN DEFAULT FALSE,
            is_unsubscribed BOOLEAN DEFAULT FALSE,
            is_hard_bounced BOOLEAN DEFAULT FALSE,
            is_soft_bounced BOOLEAN DEFAULT FALSE,
            is_complained BOOLEAN DEFAULT FALSE,
            is_blocked BOOLEAN DEFAULT FALSE,
            is_purchased BOOLEAN DEFAULT FALSE
        )
        """, "Table: messages"),

        # messages campaign split tables

        #this table will be empty, created just for structure of the data
        ("""
            CREATE TABLE messages_category (
                message_id BIGINT NOT NULL REFERENCES messages(id),
                category VARCHAR(128) NOT NULL
            )
            """, "Table: messages_recipient"),

        ("""
        CREATE TABLE messages_recipient (
            message_id BIGINT NOT NULL REFERENCES messages(id),
            client_id BIGINT NOT NULL REFERENCES clients(client_id),
            email_provider_id BIGINT
        )
        """, "Table: messages_recipient"),

        ("""
        CREATE TABLE messages_device_info (
            message_id BIGINT NOT NULL REFERENCES messages(id),
            stream VARCHAR(32) NOT NULL ,
            platform VARCHAR(32)
        )
        """, "Table: messages_device_info"),

        ("""
        CREATE TABLE message_opens (
            message_id BIGINT NOT NULL REFERENCES messages(id),
            opened_first_time_at TIMESTAMP NOT NULL ,
            opened_last_time_at TIMESTAMP NOT NULL 
        )
        """, "Table: message_opens"),

        ("""
        CREATE TABLE message_clicks (
            message_id BIGINT NOT NULL REFERENCES messages(id),
            clicked_first_time_at TIMESTAMP NOT NULL ,
            clicked_last_time_at TIMESTAMP NOT NULL 
        )
        """, "Table: message_clicks"),

        ("""
        CREATE TABLE message_negatives (
            message_id BIGINT NOT NULL REFERENCES messages(id),
            unsubscribed_at TIMESTAMP,
            hard_bounced_at TIMESTAMP,
            soft_bounced_at TIMESTAMP,
            complained_at TIMESTAMP,
            blocked_at TIMESTAMP
        )
        """, "Table: message_negatives"),

        ("""
        CREATE TABLE message_purchases (
            message_id BIGINT NOT NULL REFERENCES messages(id),
            purchased_at TIMESTAMP NOT NULL
        )
        """, "Table: message_purchases"),

        # email providers
        ("""
        CREATE TABLE email_providers (
            id BIGSERIAL PRIMARY KEY,
            email_provider VARCHAR(255) UNIQUE NOT NULL
        )
        """, "Table: email_providers"),

        # products
        ("""
        CREATE TABLE products (
            product_id BIGINT PRIMARY KEY,
            brand VARCHAR(128)
        )
        """, "Table: products"),

        # categories
        ("""
        CREATE TABLE categories (
            category_id BIGINT PRIMARY KEY,
            category_code TEXT
        )
        """, "Table: categories"),

        # events
        ("""
            CREATE TABLE events (
                id BIGSERIAL PRIMARY KEY,
                event_time TIMESTAMP NOT NULL,
                event_type VARCHAR(32) NOT NULL,
                product_id BIGINT NOT NULL REFERENCES products(product_id),
                category_id BIGINT NOT NULL REFERENCES categories(category_id),
                price NUMERIC(10, 2) NOT NULL,
                user_id BIGINT NOT NULL REFERENCES users(user_id),
                user_session UUID NOT NULL
            )
            """, "Table: events"),
    ]

    for query, description in tables:
        execute_query(cur, query, description)

    print("\n All tables created")


# =============================================================================
# 3. CREATE INDEXES
# =============================================================================

def create_indexes(cur):
    #Create all indexes for query optimization
    print("\n" + "=" * 80)
    print(" CREATING INDEXES")
    print("=" * 80)

    indexes = [
        # Users
        ("CREATE INDEX idx_users_user_id ON users(user_id)", "Index: idx_users_user_id"),

        # Clients
        ("CREATE INDEX idx_clients_user_id ON clients(user_id)", "Index: idx_clients_user_id"),
        ("CREATE INDEX idx_clients_client_id ON clients(client_id)", "Index: idx_clients_client_id"),

        # Friends
        ("CREATE INDEX idx_friends_user_id ON friends(user_id)", "Index: idx_friends_user_id"),
        ("CREATE INDEX idx_friends_friend_id ON friends(friend_id)", "Index: idx_friends_friend_id"),

        # Campaigns
        ("CREATE INDEX idx_campaigns_id ON campaigns(id)", "Index: idx_campaigns_id"),
        ("CREATE INDEX idx_campaigns_campaign_id ON campaigns(campaign_id)", "Index: idx_campaigns_campaign_id"),
        ("CREATE INDEX idx_campaigns_type ON campaigns(campaign_type)", "Index: idx_campaigns_type"),
        ("CREATE INDEX idx_campaigns_channel ON campaigns(channel)", "Index: idx_campaigns_channel"),

        # Messages
        ("CREATE INDEX idx_messages_id ON messages(id)", "Index: idx_messages_id"),
        ("CREATE INDEX idx_messages_campaign_id ON messages(campaign_id)", "Index: idx_messages_campaign_id"),
        ("CREATE INDEX idx_messages_user_id ON messages(user_id)", "Index: idx_messages_user_id"),
        ("CREATE INDEX idx_messages_channel ON messages(channel)", "Index: idx_messages_channel"),
        ("CREATE INDEX idx_messages_is_purchased ON messages(is_purchased) WHERE is_purchased = TRUE",
         "Index: idx_messages_is_purchased (partial)"),
        ("CREATE INDEX idx_messages_is_opened ON messages(is_opened) WHERE is_opened = TRUE",
         "Index: idx_messages_is_opened (partial)"),

        # Message Splits
        ("CREATE INDEX idx_messages_recipient_message_id ON messages_recipient(message_id)",
         "Index: idx_messages_recipient_message_id"),
        ("CREATE INDEX idx_messages_recipient_client_id ON messages_recipient(client_id)",
         "Index: idx_messages_recipient_client_id"),

        # Events
        ("CREATE INDEX idx_events_id ON events(id)", "Index: idx_events_id"),
        ("CREATE INDEX idx_events_user_id ON events(user_id)", "Index: idx_events_user_id"),
        ("CREATE INDEX idx_events_product_id ON events(product_id)", "Index: idx_events_product_id"),
        ("CREATE INDEX idx_events_category_id ON events(category_id)", "Index: idx_events_category_id"),
        ("CREATE INDEX idx_events_type ON events(event_type)", "Index: idx_events_type"),

        # Products
        ("CREATE INDEX idx_products_product_id ON products(product_id)", "Index: idx_products_product_id"),
        ("CREATE INDEX idx_products_brand ON products(brand)", "Index: idx_products_brand"),

        # Categories, FULL-TEXT SEARCH for Task 5
        ("CREATE INDEX idx_categories_id ON categories(category_id)", "Index: idx_categories_id"),
        ("CREATE INDEX idx_categories_fts ON categories USING GIN(to_tsvector('english', category_code))",
         "Index: idx_categories_fts (GIN - Full-Text Search)"),
    ]

    for query, description in indexes:
        execute_query(cur, query, description)

    print("\n All indexes created (28 total)")


# =============================================================================
# 4. VERIFY SCHEMA
# =============================================================================

def verify_schema(cur):
    #Verify all tables and indexes were created
    print("\n" + "=" * 80)
    print(" VERIFYING SCHEMA")
    print("=" * 80)

    # Check tables
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """)
    tables = cur.fetchall()
    print(f"\n  Tables created: {len(tables)}")
    for table in tables:
        print(f"    - {table[0]}")

    # Check indexes
    cur.execute("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE schemaname = 'public' 
        ORDER BY indexname
    """)
    indexes = cur.fetchall()
    print(f"\n  Indexes created: {len(indexes)}")

    print("\n Schema verification complete")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print(" POSTGRESQL SCHEMA CREATION")
    print(f" Target Database: {TARGET_DB}")
    print("=" * 80)

    try:
        # Step 1: Create database (connects to 'postgres')
        create_database()

        # Step 2: Connect to new database
        conn = get_connection(TARGET_DB)
        cur = conn.cursor()

        # Step 3: Drop, Create, Index, Verify
        drop_existing_tables(cur)
        create_tables(cur)
        create_indexes(cur)
        verify_schema(cur)

        conn.commit()

        print("\n" + "=" * 80)
        print(" POSTGRESQL SCHEMA CREATED SUCCESSFULLY!")
        print("=" * 80)

    except Exception as e:
        print(f"\n Error: {e}")
        raise

    finally:
        try:
            cur.close()
            conn.close()
            print("\n Connection closed")
        except:
            pass


if __name__ == "__main__":
    main()