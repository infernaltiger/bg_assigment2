
"""
Neo4j Data Loading Script


Schema based on Hackolade model.
"""

from neo4j import GraphDatabase
import pandas as pd
import os

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..', 'output', 'cleaned'))

# Neo4j connection
NEO4J_URI = 'bolt://localhost:7687'
NEO4J_USER = 'neo4j'
NEO4J_PASSWORD = ''  # CHANGE THIS to your password!
DATABASE = 'neo4j'

# Batch size for large inserts
BATCH_SIZE = 10000


# =============================================================================
# DATABASE CONNECTION
# =============================================================================
# Here i use class-style coding, i know it's different form my previous code -
# that's because i found the same style in internet and copied it to implement everything faster

class Neo4jLoader:
    def __init__(self, uri, user, password, database):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database
        print(f" Connected to Neo4j ({DATABASE})")

    def close(self):
        self.driver.close()
        print(" Connection closed")

    def execute_query(self, query, params=None):
        #Execute a query and return results
        with self.driver.session(database=self.database) as session:
            return session.run(query, params)

    def execute_write(self, query, params=None):
        #Execute a write query
        with self.driver.session(database=self.database) as session:
            session.execute_write(lambda tx: tx.run(query, params))

    def execute_write_batch(self, query, records):
        total = len(records)

        with self.driver.session(database=self.database) as session:
            for i in range(0, total, BATCH_SIZE):
                batch = records[i:i + BATCH_SIZE]

                # Each batch = separate transaction (memory freed after each)
                session.execute_write(lambda tx, b=batch: tx.run(query, records=b))

                print(f"  Processed: {min(i + BATCH_SIZE, total):,} / {total:,}")


# =============================================================================
# 1. CREATE CONSTRAINTS and INDEXES
# =============================================================================

def create_constraints(loader):
    #Create unique constraints and indexes
    print("\n" + "=" * 80)
    print(" CREATING CONSTRAINTS & INDEXES")
    print("=" * 80)

    constraints = [
        # Node constraints
        ("CREATE CONSTRAINT IF NOT EXISTS FOR (user:User) REQUIRE user.user_id IS NOT NULL", "User.user_id NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR (product:Product) REQUIRE product.product_id IS NOT NULL",
         "Product.product_id NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR (product:Product) REQUIRE product.product_id IS UNIQUE",
         "Product.product_id UNIQUE"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR (campaign:Campaign) REQUIRE campaign.id IS NOT NULL",
         "Campaign.id NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR (campaign:Campaign) REQUIRE campaign.campaign_id IS NOT NULL",
         "Campaign.campaign_id NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR (campaign:Campaign) REQUIRE campaign.campaign_type IS NOT NULL",
         "Campaign.campaign_type NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR (campaign:Campaign) REQUIRE campaign.channel IS NOT NULL",
         "Campaign.channel NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR (campaign:Campaign) REQUIRE campaign.id IS UNIQUE", "Campaign.id UNIQUE"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR (category:Category) REQUIRE category.category_id IS NOT NULL",
         "Category.category_id NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR (category:Category) REQUIRE category.category_id IS UNIQUE",
         "Category.category_id UNIQUE"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR (client:Client) REQUIRE client.client_id IS NOT NULL",
         "Client.client_id NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR (client:Client) REQUIRE client.user_device_id IS NOT NULL",
         "Client.user_device_id NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR (user:User) REQUIRE user.user_id IS UNIQUE",
         "User.user_id UNIQUE"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR (client:Client) REQUIRE client.client_id IS UNIQUE",
         "Client.client_id UNIQUE"),

        # Relationship constraints
        ("CREATE CONSTRAINT IF NOT EXISTS FOR ()-[p:PURCHASED]-() REQUIRE p.event_time IS NOT NULL",
         "PURCHASED.event_time NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR ()-[p:PURCHASED]-() REQUIRE p.price IS NOT NULL",
         "PURCHASED.price NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR ()-[p:PURCHASED]-() REQUIRE p.user_session IS NOT NULL",
         "PURCHASED.user_session NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR ()-[p:PURCHASED]-() REQUIRE p.category_id IS NOT NULL",
         "PURCHASED.category_id NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR ()-[v:VIEWED]-() REQUIRE v.event_time IS NOT NULL",
         "VIEWED.event_time NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR ()-[v:VIEWED]-() REQUIRE v.price IS NOT NULL", "VIEWED.price NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR ()-[v:VIEWED]-() REQUIRE v.user_session IS NOT NULL",
         "VIEWED.user_session NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR ()-[v:VIEWED]-() REQUIRE v.category_id IS NOT NULL",
         "VIEWED.category_id NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR ()-[c:CART]-() REQUIRE c.event_time IS NOT NULL",
         "CART.event_time NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR ()-[c:CART]-() REQUIRE c.price IS NOT NULL", "CART.price NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR ()-[c:CART]-() REQUIRE c.user_session IS NOT NULL",
         "CART.user_session NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR ()-[c:CART]-() REQUIRE c.category_id IS NOT NULL",
         "CART.category_id NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR ()-[r:RECIEVED_MESSAGE_ABOUT_CAMPAIGN]-() REQUIRE r.id IS NOT NULL",
         "RECIEVED_MESSAGE...id NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR ()-[r:RECIEVED_MESSAGE_ABOUT_CAMPAIGN]-() REQUIRE r.message_id IS NOT NULL",
         "RECIEVED_MESSAGE...message_id NOT NULL"),
        (
        "CREATE CONSTRAINT IF NOT EXISTS FOR ()-[r:RECIEVED_MESSAGE_ABOUT_CAMPAIGN]-() REQUIRE r.message_type IS NOT NULL",
        "RECIEVED_MESSAGE...message_type NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR ()-[r:RECIEVED_MESSAGE_ABOUT_CAMPAIGN]-() REQUIRE r.channel IS NOT NULL",
         "RECIEVED_MESSAGE...channel NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR ()-[r:RECIEVED_MESSAGE_ABOUT_CAMPAIGN]-() REQUIRE r.client_id IS NOT NULL",
         "RECIEVED_MESSAGE...client_id NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR ()-[r:RECIEVED_MESSAGE_ABOUT_CAMPAIGN]-() REQUIRE r.date IS NOT NULL",
         "RECIEVED_MESSAGE...date NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR ()-[r:RECIEVED_MESSAGE_ABOUT_CAMPAIGN]-() REQUIRE r.sent_at IS NOT NULL",
         "RECIEVED_MESSAGE...sent_at NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR ()-[r:RECIEVED_MESSAGE_ABOUT_CAMPAIGN]-() REQUIRE r.created_at IS NOT NULL",
         "RECIEVED_MESSAGE...created_at NOT NULL"),
        ("CREATE CONSTRAINT IF NOT EXISTS FOR ()-[r:RECIEVED_MESSAGE_ABOUT_CAMPAIGN]-() REQUIRE r.updated_at IS NOT NULL",
         "RECIEVED_MESSAGE...updated_at NOT NULL"),

        # Indexes
        ("CREATE INDEX idx_user IF NOT EXISTS FOR (user:User) ON (user.user_id)", "idx_user"),
        ("CREATE INDEX idx_product IF NOT EXISTS FOR (product:Product) ON (product.product_id)", "idx_product"),
        ("CREATE INDEX idx_cmp_id IF NOT EXISTS FOR (campaign:Campaign) ON (campaign.id)", "idx_cmp_id"),
        ("CREATE INDEX idx_cmp_type IF NOT EXISTS FOR (campaign:Campaign) ON (campaign.campaign_type)", "idx_cmp_type"),
        ("CREATE INDEX idx_cat_id IF NOT EXISTS FOR (category:Category) ON (category.category_id)", "idx_cat_id"),
        ("CREATE INDEX idx_cat_code IF NOT EXISTS FOR (category:Category) ON (category.category_code)", "idx_cat_code"),
        ("CREATE INDEX idx_client_id IF NOT EXISTS FOR (client:Client) ON (client.client_id)", "idx_client_id"),
    ]

    for query, name in constraints:
        try:
            loader.execute_write(query)
            print(f"  Done {name}")
        except Exception as e:
            print(f"  Error {name}: {e}")


# =============================================================================
# 2. LOAD CATEGORIES
# =============================================================================

def load_categories(loader):
    #Load Category nodes
    print("\n" + "=" * 80)
    print(" LOADING CATEGORIES")
    print("=" * 80)

    df = pd.read_csv(os.path.join(DATA_DIR, 'events_cleaned.csv'))
    categories = df[['category_id', 'category_code']].drop_duplicates()

    records = []
    for _, row in categories.iterrows():
        if pd.notna(row['category_id']):
            records.append({
                'category_id': int(row['category_id']),
                'category_code': row['category_code'] if pd.notna(row['category_code']) else None
            })
    #here i use megre because of category_id - unique, but in real data there are instances where category_id have and don't have code
    query = """
    UNWIND $records AS record
    MERGE (category:Category {
        category_id: record.category_id})
    SET category.category_code = record.category_code
    """

    loader.execute_write_batch(query, records)
    print(f" Categories: {len(records):,} nodes")


# =============================================================================
# 3. LOAD PRODUCTS
# =============================================================================

def load_products(loader):
    #Load Product nodes
    print("\n" + "=" * 80)
    print(" LOADING PRODUCTS")
    print("=" * 80)

    df = pd.read_csv(os.path.join(DATA_DIR, 'events_cleaned.csv'))
    products = df[['product_id', 'brand']].drop_duplicates()

    records = []
    for _, row in products.iterrows():
        if pd.notna(row['product_id']):
            records.append({
                'product_id': int(row['product_id']),
                'brand': row['brand'] if pd.notna(row['brand']) else None
            })

    query = """
    UNWIND $records AS record
    MERGE (product:Product {
        product_id: record.product_id
    })
    SET product.brand = record.brand
    """

    loader.execute_write_batch(query, records)
    print(f" Products: {len(records):,} nodes")


# =============================================================================
# 4. LOAD USERS (from messages + clients_cleaned)
# =============================================================================

def load_users(loader):
    """
    Load User nodes - EXACT same logic as MongoDB load_users()

    - Load ALL user_ids from messages (not just purchasers)
    - Also include users from clients_cleaned.csv
    - Merge both sources to ensure NO users are lost
    """
    print("\n" + "=" * 80)
    print(" LOADING USERS")
    print("=" * 80)

    # Step 1: Get ALL user_ids from messages
    messages_df = pd.read_csv(os.path.join(DATA_DIR, 'messages_cleaned.csv'), low_memory=False)
    all_user_ids = set(messages_df['user_id'].dropna().unique())
    print(f"  Unique users in messages: {len(all_user_ids):,}")

    # Step 2: Get ALL user_ids from clients_cleaned.csv
    clients_df = pd.read_csv(os.path.join(DATA_DIR, 'clients_cleaned.csv'))
    print(f"  Clients from clients_cleaned.csv: {len(clients_df):,}")

    # Add users from clients to the set
    for _, row in clients_df.iterrows():
        all_user_ids.add(int(row['user_id']))

    print(f"  Total unique users (messages + clients): {len(all_user_ids):,}")

    # Step 3: Create user records
    records = [{'user_id': int(uid)} for uid in all_user_ids]

    query = """
    UNWIND $records AS record
    CREATE (user:User {
        user_id: record.user_id
    })
    """

    loader.execute_write_batch(query, records)
    print(f" Users: {len(records):,} nodes")


# =============================================================================
# 5. LOAD CLIENTS + CLIENT_RELATED_USER
# =============================================================================

def load_clients(loader):
    """
    Load Client nodes and CLIENT_RELATED_USER relationships

    EXACT same logic as in previous loading scripts:
    - Parse clients from messages (extract user_device_id from client_id formula)
    - Merge with clients_cleaned.csv (update purchase dates)
    - Create Client nodes + relationships
    """
    print("\n" + "=" * 80)
    print(" LOADING CLIENTS")
    print("=" * 80)

    CLIENT_ID_PREFIX = '151591562'
    prefix_len = len(CLIENT_ID_PREFIX)

    # Step 1: Parse clients from messages (extract user_device_id)
    messages_df = pd.read_csv(os.path.join(DATA_DIR, 'messages_cleaned.csv'), low_memory=False)

    all_clients = {}  # {client_id: {user_id, user_device_id, first_purchase_date}}

    print("  Parsing clients from messages...")
    for _, row in messages_df.iterrows():
        client_id = int(row['client_id'])
        user_id = int(row['user_id'])

        if client_id in all_clients:
            continue

        client_id_str = str(client_id)
        user_id_str = str(user_id)

        if client_id_str.startswith(CLIENT_ID_PREFIX):
            remainder = client_id_str[prefix_len:]
            device_id_str = remainder.replace(user_id_str, '', 1)

            if device_id_str.isdigit():
                all_clients[client_id] = {
                    'client_id': client_id,
                    'user_id': user_id,
                    'user_device_id': int(device_id_str),
                    'first_purchase_date': None
                }

    print(f"  Clients parsed from messages: {len(all_clients):,}")

    # Step 2: Merge with clients_cleaned.csv
    clients_df = pd.read_csv(os.path.join(DATA_DIR, 'clients_cleaned.csv'))
    print(f"  Clients from clients_cleaned.csv: {len(clients_df):,}")

    added_count = 0
    updated_count = 0

    for _, row in clients_df.iterrows():
        client_id = int(row['client_id'])
        user_id = int(row['user_id'])
        user_device_id = int(row['user_device_id'])
        first_purchase_date = row['first_purchase_date'] if pd.notna(row['first_purchase_date']) else None

        if client_id in all_clients:
            # Client exists from messages - UPDATE with purchase date
            all_clients[client_id]['first_purchase_date'] = str(first_purchase_date) if first_purchase_date else None
            updated_count += 1
        else:
            # Client NOT in messages - ADD new
            all_clients[client_id] = {
                'client_id': client_id,
                'user_id': user_id,
                'user_device_id': user_device_id,
                'first_purchase_date': str(first_purchase_date) if first_purchase_date else None
            }
            added_count += 1

    print(f"  New clients from clients_cleaned.csv (not in messages): {added_count:,}")
    print(f"  Updated clients (in both sources): {updated_count:,}")

    # Step 3: Create records for Neo4j
    records = []
    for client in all_clients.values():
        records.append({
            'client_id': client['client_id'],
            'user_id': client['user_id'],
            'user_device_id': client['user_device_id'],
            'first_purchase_date': client['first_purchase_date']
        })

    query = """
    UNWIND $records AS record
    CREATE (client:Client {
        client_id: record.client_id,
        user_device_id: record.user_device_id,
        first_purchase_date: record.first_purchase_date
    })
    WITH client, record
    MATCH (user:User {user_id: record.user_id})
    CREATE (client)-[:CLIENT_RELATED_USER]->(user)
    """

    loader.execute_write_batch(query, records)
    print(f" Clients: {len(records):,} nodes + relationships")

    # Statistics (like MongoDB)
    purchasers = sum(1 for c in records if c['first_purchase_date'] is not None)
    print(f"\n  Total: {len(records):,} clients")
    print(f"  Clients with purchases: {purchasers:,}")
    print(f"  Clients without purchases: {len(records) - purchasers:,}")


# =============================================================================
# 5.5 LOAD FRIENDS_WITH (EXACT like MongoDB embedded friends[])
# =============================================================================

def load_friends(loader):
    """
    Load FRIENDS_WITH relationships between users

    EXACT same logic as MongoDB friends[] array
    """
    print("\n" + "=" * 80)
    print(" LOADING FRIENDS")
    print("=" * 80)

    df = pd.read_csv(os.path.join(DATA_DIR, 'friends_cleaned.csv'))
    print(f"  Friends from friends_cleaned.csv: {len(df):,}")

    records = []
    for _, row in df.iterrows():
        records.append({
            'user_id': int(row['user_id']),
            'friend_id': int(row['friend_id'])
        })

    query = """
    UNWIND $records AS record
    MATCH (user1:User {user_id: record.user_id})
    MATCH (user2:User {user_id: record.friend_id})
    CREATE (user1)-[:FRIENDS_WITH]->(user2)
    """

    loader.execute_write_batch(query, records)
    print(f" Friends: {len(records):,} relationships")
# =============================================================================
# 6. LOAD CAMPAIGNS
# =============================================================================

def load_campaigns(loader):
    #Load Campaign nodes
    print("\n" + "=" * 80)
    print(" LOADING CAMPAIGNS")
    print("=" * 80)

    df = pd.read_csv(os.path.join(DATA_DIR, 'campaigns_cleaned.csv'))
    df['surrogate_id'] = range(1, len(df) + 1)
    records = []
    for _, row in df.iterrows():
        # subject_flags as array of 6 booleans
        subject_flags = [
            bool(row['subject_with_personalization']) if pd.notna(row['subject_with_personalization']) else False,
            bool(row['subject_with_deadline']) if pd.notna(row['subject_with_deadline']) else False,
            bool(row['subject_with_emoji']) if pd.notna(row['subject_with_emoji']) else False,
            bool(row['subject_with_bonuses']) if pd.notna(row['subject_with_bonuses']) else False,
            bool(row['subject_with_discount']) if pd.notna(row['subject_with_discount']) else False,
            bool(row['subject_with_saleout']) if pd.notna(row['subject_with_saleout']) else False
        ]

        records.append({
            'id': int(row['surrogate_id']),
            'campaign_id': int(row['id']),
            'campaign_type': row['campaign_type'],
            'channel': row['channel'],
            'topic': row['topic'] if pd.notna(row['topic']) else None,
            'started_at': row['started_at'] if pd.notna(row['started_at']) else None,
            'finished_at': row['finished_at'] if pd.notna(row['finished_at']) else None,
            'total_count': int(row['total_count']) if pd.notna(row['total_count']) else None,
            'subject_length': int(row['subject_length']) if pd.notna(row['subject_length']) else None,
            'warmup_mode': bool(row['warmup_mode']) if pd.notna(row['warmup_mode']) else None,
            'hour_limit': float(row['hour_limit']) if pd.notna(row['hour_limit']) else None,
            'ab_test': bool(row['ab_test']) if pd.notna(row['ab_test']) else None,
            'is_test': bool(row['is_test']) if pd.notna(row['is_test']) else None,
            'position': int(row['position']) if pd.notna(row['position']) else None,
            'subject_flags': subject_flags
        })

    query = """
    UNWIND $records AS record
    CREATE (campaign:Campaign {
        id: record.id,
        campaign_id: record.campaign_id,
        campaign_type: record.campaign_type,
        channel: record.channel,
        topic: record.topic,
        started_at: record.started_at,
        finished_at: record.finished_at,
        total_count: record.total_count,
        subject_length: record.subject_length,
        warmup_mode: record.warmup_mode,
        hour_limit: record.hour_limit,
        ab_test: record.ab_test,
        is_test: record.is_test,
        position: record.position,  
        subject_flags: record.subject_flags
    })
    """

    loader.execute_write_batch(query, records)
    print(f" Campaigns: {len(records):,} nodes")


# =============================================================================
# 7. LOAD EVENTS (PURCHASED, VIEWED, CART relationships)
# =============================================================================

def load_events(loader):
    #Load PURCHASED, VIEWED, CART relationships between User and Product
    print("\n" + "=" * 80)
    print(" LOADING EVENTS (This may take some time)")
    print("=" * 80)

    df = pd.read_csv(os.path.join(DATA_DIR, 'events_cleaned.csv'))
    print(f"  Total events: {len(df):,}")

    events_by_type = df.groupby('event_type')

    for event_type, group in events_by_type:
        print(f"\n  Processing {event_type} events: {len(group):,}")

        records = []
        for _, row in group.iterrows():
            if pd.notna(row['user_id']) and pd.notna(row['product_id']):
                records.append({
                    'user_id': int(row['user_id']),
                    'product_id': int(row['product_id']),
                    'category_id': int(row['category_id']),
                    'category_code': row['category_code'] if pd.notna(row['category_code']) else None,
                    'event_time': row['event_time'],
                    'price': float(row['price']),
                    'user_session': row['user_session']
                })

        # Map event_type to relationship type
        rel_type_map = {
            'purchase': 'PURCHASED',
            'view': 'VIEWED',
            'cart': 'CART'
        }
        rel_type = rel_type_map.get(event_type, 'INTERACTED')

        query = f"""
        UNWIND $records AS record
        MATCH (user:User {{user_id: record.user_id}})
        MATCH (product:Product {{product_id: record.product_id}})
        CREATE (user)-[:{rel_type} {{
            event_time: record.event_time,
            price: record.price,
            user_session: record.user_session,
            category_id: record.category_id,
            category_code: record.category_code
        }}]->(product)
        """

        loader.execute_write_batch(query, records)
        print(f" {event_type}: {len(records):,} relationships")

    print(f"\n Total Events: {len(df):,} relationships")


# =============================================================================
# 8. LOAD RECIEVED_MESSAGE_ABOUT_CAMPAIGN (Message as relationship!)
# =============================================================================

def load_messages(loader):
    #Load RECIEVED_MESSAGE_ABOUT_CAMPAIGN relationships (User to Campaign)
    print("\n" + "=" * 80)
    print(" LOADING MESSAGES (This may take some time)")
    print("=" * 80)

    df = pd.read_csv(os.path.join(DATA_DIR, 'messages_cleaned.csv'), low_memory=False)
    print(f"  Total messages: {len(df):,}")

    records = []
    for _, row in df.iterrows():
        records.append({
            'id': int(row['id']),
            'message_id': row['message_id'],
            'campaign_id': int(row['campaign_id']),
            'user_id': int(row['user_id']),
            'client_id': int(row['client_id']),
            'message_type': row['message_type'],
            'channel': row['channel'],
            'date': row['date'],
            'sent_at': row['sent_at'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
            'platform': row['platform'] if pd.notna(row['platform']) else None,
            'stream': row['stream'] if pd.notna(row['stream']) else None,
            'email_provider': row['email_provider'] if pd.notna(row['email_provider']) else None,
            'is_opened': bool(row['is_opened']),
            'opened_first_time_at': row['opened_first_time_at'] if pd.notna(row['opened_first_time_at']) else None,
            'opened_last_time_at': row['opened_last_time_at'] if pd.notna(row['opened_last_time_at']) else None,
            'is_clicked': bool(row['is_clicked']),
            'clicked_first_time_at': row['clicked_first_time_at'] if pd.notna(row['clicked_first_time_at']) else None,
            'clicked_last_time_at': row['clicked_last_time_at'] if pd.notna(row['clicked_last_time_at']) else None,
            'is_unsubscribed': bool(row['is_unsubscribed']),
            'unsubscribed_at': row['unsubscribed_at'] if pd.notna(row['unsubscribed_at']) else None,
            'is_hard_bounced': bool(row['is_hard_bounced']),
            'hard_bounced_at': row['hard_bounced_at'] if pd.notna(row['hard_bounced_at']) else None,
            'is_soft_bounced': bool(row['is_soft_bounced']),
            'soft_bounced_at': row['soft_bounced_at'] if pd.notna(row['soft_bounced_at']) else None,
            'is_complained': bool(row['is_complained']),
            'complained_at': row['complained_at'] if pd.notna(row['complained_at']) else None,
            'is_blocked': bool(row['is_blocked']),
            'blocked_at': row['blocked_at'] if pd.notna(row['blocked_at']) else None,
            'is_purchased': bool(row['is_purchased']),
            'purchased_at': row['purchased_at'] if pd.notna(row['purchased_at']) else None
        })

    query = """
    UNWIND $records AS record
    MATCH (user:User {user_id: record.user_id})
    MATCH (campaign:Campaign {id: record.campaign_id})
    CREATE (user)-[:RECIEVED_MESSAGE_ABOUT_CAMPAIGN {
        id: record.id,
        message_id: record.message_id,
        message_type: record.message_type,
        channel: record.channel,
        client_id: record.client_id,
        date: record.date,
        sent_at: record.sent_at,
        created_at: record.created_at,
        updated_at: record.updated_at,
        platform: record.platform,
        stream: record.stream,
        email_provider: record.email_provider,
        is_opened: record.is_opened,
        opened_first_time_at: record.opened_first_time_at,
        opened_last_time_at: record.opened_last_time_at,
        is_clicked: record.is_clicked,
        clicked_first_time_at: record.clicked_first_time_at,
        clicked_last_time_at: record.clicked_last_time_at,
        is_unsubscribed: record.is_unsubscribed,
        unsubscribed_at: record.unsubscribed_at,
        is_hard_bounced: record.is_hard_bounced,
        hard_bounced_at: record.hard_bounced_at,
        is_soft_bounced: record.is_soft_bounced,
        soft_bounced_at: record.soft_bounced_at,
        is_complained: record.is_complained,
        complained_at: record.complained_at,
        is_blocked: record.is_blocked,
        blocked_at: record.blocked_at,
        is_purchased: record.is_purchased,
        purchased_at: record.purchased_at
    }]->(campaign)
    """

    loader.execute_write_batch(query, records)
    print(f" Messages: {len(records):,} relationships")


# =============================================================================
# 9. CREATE PRODUCT_BELONG_TO_CATEGORY
# =============================================================================

def create_product_category_relationships(loader):
    #Create PRODUCT_BELONG_TO_CATEGORY relationships
    print("\n" + "=" * 80)
    print(" CREATING PRODUCT-CATEGORY RELATIONSHIPS")
    print("=" * 80)

    df = pd.read_csv(os.path.join(DATA_DIR, 'events_cleaned.csv'))
    product_categories = df[['product_id', 'category_id']].drop_duplicates()

    records = []
    for _, row in product_categories.iterrows():
        if pd.notna(row['product_id']) and pd.notna(row['category_id']):
            records.append({
                'product_id': int(row['product_id']),
                'category_id': int(row['category_id'])
            })

    query = """
    UNWIND $records AS record
    MATCH (product:Product {product_id: record.product_id})
    MATCH (category:Category {category_id: record.category_id})
    CREATE (product)-[:PRODUCT_BELONG_TO_CATEGORY]->(category)
    """

    loader.execute_write_batch(query, records)
    print(f"  Product-Category: {len(records):,} relationships")


# =============================================================================
# MAIN
# =============================================================================
def main():
    print("=" * 80)
    print(" NEO4J DATA LOADING")
    print(f" Data Directory: {DATA_DIR}")
    print("=" * 80)

    loader = Neo4jLoader(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, DATABASE)

    try:
        # Step 1: Schema
        create_constraints(loader)

        # Step 2: Core nodes (independent)
        load_categories(loader)
        load_products(loader)
        load_users(loader)  # messages + clients_cleaned
        load_campaigns(loader)

        # Step 3: Clients (with merge logic like MongoDB)
        load_clients(loader)  # messages + clients_cleaned merged

        # Step 4: Social relationships
        load_friends(loader)  #  FRIENDS_WITH

        # Step 5: Event relationships
        load_events(loader)

        # Step 6: Message relationships
        load_messages(loader)

        # Step 7: Product-Category relationships
        create_product_category_relationships(loader)

        print("\n" + "=" * 80)
        print(" NEO4J DATA LOADING COMPLETED SUCCESSFULLY!")
        print("=" * 80)

        # Statistics
        print("\n Database Statistics:")
        stats_query = """
        MATCH (n)
        RETURN labels(n)[0] AS label, count(*) AS count
        UNION ALL
        MATCH ()-[r]->()
        RETURN type(r) AS label, count(*) AS count
        ORDER BY count DESC
        """
        result = loader.execute_query(stats_query)
        for record in result:
            print(f"   - {record['label']}: {record['count']:,}")

    except Exception as e:
        print(f"\n Error: {e}")
        raise

    finally:
        loader.close()


if __name__ == "__main__":
    main()