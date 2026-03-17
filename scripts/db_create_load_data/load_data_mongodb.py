"""
MongoDB Data Loading Script
Option B: Python driver (pymongo) for database creation and data loading.

Schema based on Hackolade model with embedded documents and arrays.
"""

from pymongo import MongoClient, ASCENDING, TEXT
import pandas as pd
import os
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..', 'output', 'cleaned'))

# MongoDB connection, default ip
MONGO_URI = 'mongodb://localhost:27017/'
DB_NAME = 'bigdata'


# =============================================================================
# DATABASE CONNECTION
# =============================================================================

def get_connection():
    #Create MongoDB connection
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    print(f" Connected to MongoDB ({DB_NAME})")
    return db


# =============================================================================
# 1. LOAD USERS
# =============================================================================

def load_users(db):
    """
    Load users with embedded clients array and friends array

    Important:
    - Load ALL user_ids from messages (not just purchasers)
    - Load clients from clients_cleaned.csv (purchasers with dates)
    - Parse user_device_id from client_id formula: 151591562 + user_id + device_id

    Schema:
    {
        _id: ObjectId (auto),
        user_id: int64 (PK, unique),
        clients: [{
            client_id: int64,
            user_device_id: int32,
            first_purchase_date: date
        }],
        friends: [friend_id, ...]
    }
    """
    print("\n" + "=" * 80)
    print(" LOADING USERS ")
    print("=" * 80)

    CLIENT_ID_PREFIX = '151591562'
    prefix_len = len(CLIENT_ID_PREFIX)

    messages_df = pd.read_csv(os.path.join(DATA_DIR, 'messages_cleaned.csv'), low_memory=False)
    all_user_ids = set(messages_df['user_id'].dropna().unique())
    print(f"  Unique users in messages: {len(all_user_ids):,}")

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

    clients_df = pd.read_csv(os.path.join(DATA_DIR, 'clients_cleaned.csv'))
    print(f"  Clients from clients_cleaned.csv: {len(clients_df):,}")

    added_count = 0
    updated_count = 0

    for _, row in clients_df.iterrows():
        client_id = int(row['client_id'])
        user_id = int(row['user_id'])
        user_device_id = int(row['user_device_id'])
        first_purchase_date = str(row['first_purchase_date']) if pd.notna(row['first_purchase_date']) else None

        if client_id in all_clients:
            # Client exists from messages - UPDATE with purchase date
            all_clients[client_id]['first_purchase_date'] = first_purchase_date
            updated_count += 1
        else:
            # Client NOT in messages - ADD new (purchaser who didn't receive messages)
            all_clients[client_id] = {
                'client_id': client_id,
                'user_id': user_id,
                'user_device_id': user_device_id,
                'first_purchase_date': first_purchase_date
            }
            added_count += 1

        # Ensure user_id exists in all_user_ids
        all_user_ids.add(user_id)

    print(f"  New clients from clients_cleaned.csv (not in messages): {added_count:,}")
    print(f"  Updated clients (in both sources): {updated_count:,}")

    friends_df = pd.read_csv(os.path.join(DATA_DIR, 'friends_cleaned.csv'))
    print(f"  Friends from friends_cleaned.csv: {len(friends_df):,}")


    friends_by_user = friends_df.groupby('user_id')['friend_id'].apply(
        lambda x: [int(f) for f in x.tolist()]
    ).to_dict()

    clients_by_user = {}
    for client in all_clients.values():
        user_id = client['user_id']
        if user_id not in clients_by_user:
            clients_by_user[user_id] = []
        clients_by_user[user_id].append({
            'client_id': client['client_id'],
            'user_device_id': client['user_device_id'],
            'first_purchase_date': client['first_purchase_date']
        })


    db.users.drop()

    users = []
    for user_id in all_user_ids:
        doc = {
            'user_id': int(user_id),
            'clients': clients_by_user.get(user_id, []),
            'friends': friends_by_user.get(user_id, [])
        }
        users.append(doc)

    db.users.insert_many(users)
    print(f"  Users: {len(users):,} documents")

    db.users.create_index([('user_id', ASCENDING)], unique=True)
    db.users.create_index([('friends', ASCENDING)])
    db.users.create_index([('clients.client_id', ASCENDING)])

    total_clients = sum(len(u['clients']) for u in users)
    total_friends = sum(len(u['friends']) for u in users)
    purchasers = sum(1 for u in users if any(c['first_purchase_date'] for c in u['clients']))

    print(f"\n  Total: {len(users):,} users, {total_clients:,} clients")
    print(f"  Clients with purchases: {purchasers:,}")
    print(f"  Clients without purchases: {total_clients - purchasers:,}")
    print(f"  Embedded friends: {total_friends:,}")


# =============================================================================
# 2. LOAD PRODUCTS
# =============================================================================

def load_products(db):
    """
    Load products with embedded categories array

    Schema:
    {
        _id: ObjectId (auto),
        product_id: int64 (PK),
        brand: str,
        categories: [{category_id, category_code}]
    }
    """
    print("\n" + "=" * 80)
    print(" LOADING PRODUCTS")
    print("=" * 80)

    df = pd.read_csv(os.path.join(DATA_DIR, 'events_cleaned.csv'))
    print(f"  Total events: {len(df):,}")

    db.products.drop()

    # Get unique products with their categories
    products_dict = {}

    for _, row in df.iterrows():
        product_id = int(row['product_id'])

        if product_id is None:
            continue

        if product_id not in products_dict:
            products_dict[product_id] = {
                'product_id': product_id,
                'brand': row['brand'] if pd.notna(row['brand']) else None,
                'categories': []
            }

        # Add category if not already present
        category_id = int(row['category_id'])
        category_code = row['category_code'] if pd.notna(row['category_code']) else None

        # Check if this category already exists for this product
        category_exists = any(
            c['category_id'] == category_id and c['category_code'] == category_code
            for c in products_dict[product_id]['categories']
        )

        if not category_exists:
            products_dict[product_id]['categories'].append({
                'category_id': category_id,
                'category_code': category_code
            })

    # Convert to list
    products_list = list(products_dict.values())

    db.products.insert_many(products_list)
    print(f" Products: {len(products_list):,} documents")

    # Count total categories embedded
    total_categories = sum(len(p['categories']) for p in products_list)
    print(f" Embedded categories: {total_categories:,}")

    # Indexes
    db.products.create_index([('product_id', ASCENDING)], unique=True)
    db.products.create_index([('brand', ASCENDING)])
    db.products.create_index([('categories.category_code', TEXT)])

# =============================================================================
# 3. LOAD CAMPAIGNS
# =============================================================================
def load_campaigns(db):
    """
    Schema:
    {
        _id: ObjectId (auto, PK),
        id: int64 (original from CSV, not unique),
        campaign_type: str,
        channel: str,
        topic: str,
        started_at: date,
        finished_at: date,
        total_count: int64,
        subject: {length, personalization, deadline, emoji, bonuses, discount, saleout},
        ab_test: bool,
        warmup_mode: bool,
        hour_limit: num,
        is_test: bool,
        position: num
    }

    Returns:
        campaign_map: {original_id: mongo_id}
    """
    print("\n" + "=" * 80)
    print(" LOADING CAMPAIGNS")
    print("=" * 80)

    df = pd.read_csv(os.path.join(DATA_DIR, 'campaigns_cleaned.csv'))

    db.campaigns.drop()

    campaigns = []
    campaign_map = {}  # {campaign_id: {'_id': mongo_id, 'data': full_doc}}
    for _, row in df.iterrows():
        doc = {
            'id': int(row['id']),  # Original ID (not unique)
            'campaign_type': row['campaign_type'],
            'channel': row['channel'],
            'topic': row['topic'] if pd.notna(row['topic']) else None,
            'started_at': row['started_at'] if pd.notna(row['started_at']) else None,
            'finished_at': row['finished_at'] if pd.notna(row['finished_at']) else None,
            'total_count': int(row['total_count']) if pd.notna(row['total_count']) else None,
            'subject': {
                'length': int(row['subject_length']) if pd.notna(row['subject_length']) else None,
                'personalization': bool(row['subject_with_personalization']),
                'deadline': bool(row['subject_with_deadline']),
                'emoji': bool(row['subject_with_emoji']),
                'bonuses': bool(row['subject_with_bonuses']),
                'discount': bool(row['subject_with_discount']),
                'saleout': bool(row['subject_with_saleout'])
            },
            'ab_test': bool(row['ab_test']) if pd.notna(row['ab_test']) else None,
            'warmup_mode': bool(row['warmup_mode']),
            'hour_limit': float(row['hour_limit']) if pd.notna(row['hour_limit']) else None,
            'is_test': bool(row['is_test']) if pd.notna(row['is_test']) else None,
            'position': int(row['position']) if pd.notna(row['position']) else None
        }
        campaigns.append(doc)

    result = db.campaigns.insert_many(campaigns)
    print(f"  Campaigns: {len(campaigns):,} documents")

    # Create mapping: campaign_id: {mongo_id, full_data_for_embedding}
    for doc, mongo_id in zip(campaigns, result.inserted_ids):
        campaign_map[doc['id']] = {
            '_id': mongo_id,
            'data': {
                'id': doc['id'],
                'campaign_type': doc['campaign_type'],
                'channel': doc['channel'],
                'topic': doc['topic'],
                'started_at': doc['started_at'],
                'finished_at': doc['finished_at'],
                'total_count': doc['total_count'],
                'subject': doc['subject'],
                'ab_test': doc['ab_test'],
                'warmup_mode': doc['warmup_mode'],
                'hour_limit': doc['hour_limit'],
                'is_test': doc['is_test'],
                'position': doc['position']
            }
        }

    print(f"Campaign mapping created: {len(campaign_map):,} entries")

    # Indexes
    db.campaigns.create_index([('_id', ASCENDING)])
    db.campaigns.create_index([('campaign_type', ASCENDING)])
    db.campaigns.create_index([('channel', ASCENDING)])

    return campaign_map

# =============================================================================
# 4. LOAD MESSAGES
# =============================================================================
def load_messages(db, campaign_map):
    """
    Schema:
    {
        _id: ObjectId (auto, PK),
        campaign_id: ObjectId (FK campaigns._id),
        campaign_data: {
            id: int64
            campaign_type: str,
            channel: str,
            topic: str,
            started_at: date,
            finished_at: date,
            total_count: int64,
            subject: {length, personalization, deadline, emoji, bonuses, discount, saleout},
            ab_test: bool,
            warmup_mode: bool,
            hour_limit: num,
            is_test: bool,
            position: num
        },
        message_type: str,
        channel: str,
        user_id: int64, (FK)
        client_id: int64, (FK)
        date: date,
        sent_at: date,
        device_info: {platform, stream, email_provider},
        engagement: {is_opened, is_clicked, ..., purchased_at, ...},
        created_at: date,
        updated_at: date
    }
    """
    print("\n" + "=" * 80)
    print(" LOADING MESSAGES (This may take some time)")
    print("=" * 80)

    df = pd.read_csv(os.path.join(DATA_DIR, 'messages_cleaned.csv'), low_memory=False)
    print(f"  Total messages: {len(df):,}")

    db.messages.drop()

    messages = []
    skipped = 0

    for idx, row in df.iterrows():
        original_campaign_id = int(row['campaign_id'])

        # Get MongoDB _id from mapping
        campaign_info = campaign_map.get(original_campaign_id)

        if campaign_info is None:
            skipped += 1
            continue

        doc = {
            'campaign_id': campaign_info['_id'],
            'campaign_data': campaign_info['data'],
            'message_type': row['message_type'],
            'channel': row['channel'],
            'user_id':int(row['user_id']),
            'client_id': int(row['client_id']),
            'date': row['date'],
            'sent_at': row['sent_at'],
            'device_info': {
                'platform': row['platform'] if pd.notna(row['platform']) else None,
                'stream': row['stream'] if pd.notna(row['stream']) else None,
                'email_provider': row['email_provider'] if pd.notna(row['email_provider']) else None
            },
            'engagement': {
                'is_opened': bool(row['is_opened']),
                'opened_first_time_at': row['opened_first_time_at'] if pd.notna(row['opened_first_time_at']) else None,
                'opened_last_time_at': row['opened_last_time_at'] if pd.notna(row['opened_last_time_at']) else None,
                'is_clicked': bool(row['is_clicked']),
                'clicked_first_time_at': row['clicked_first_time_at'] if pd.notna(
                    row['clicked_first_time_at']) else None,
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
                'purchased_at': row['purchased_at'] if pd.notna(row['purchased_at']) else None,

            },
            'created_at': row['created_at'] if pd.notna(row['created_at']) else None,
            'updated_at': row['updated_at'] if pd.notna(row['updated_at']) else None
        }
        messages.append(doc)

        if (idx + 1) % 100000 == 0:
            print(f"  Processed: {idx + 1:,} / {len(df):,}")

    db.messages.insert_many(messages)
    print(f" Messages: {len(messages):,} documents")
    if skipped > 0:
        print(f" Skipped: {skipped:,} (campaign_id not found)")

    # Indexes
    db.messages.create_index([('_id', ASCENDING)])
    db.messages.create_index([('campaign_id', ASCENDING)])
    db.messages.create_index([('user_id', ASCENDING)])
    db.messages.create_index([('engagement.is_purchased', ASCENDING)])



# =============================================================================
# 5. LOAD EVENTS
# =============================================================================

def load_events(db):
    """
    Load events

    Schema:
    {
        _id: ObjectId,
        event_time: date,
        event_type: str,
        product_id: int64 (FK),
        category_id: int64,
        category_code: str,
        brand: str,
        price: dec128,
        user_id: int64 (FK),
        user_session: str
    }
    """
    print("\n" + "=" * 80)
    print(" LOADING EVENTS (This may take some time)")
    print("=" * 80)

    df = pd.read_csv(os.path.join(DATA_DIR, 'events_cleaned.csv'))
    print(f"  Total events: {len(df):,}")

    # Drop existing
    db.events.drop()

    events = []
    for idx, row in df.iterrows():
        doc = {
            'event_time': row['event_time'],
            'event_type': row['event_type'],
            'product_id': int(row['product_id']),
            'category_id': int(row['category_id']),
            'category_code': row['category_code'] if pd.notna(row['category_code']) else None,
            'brand': row['brand'] if pd.notna(row['brand']) else None,
            'price': float(row['price']),
            'user_id': int(row['user_id']),
            'user_session': row['user_session']
        }
        events.append(doc)

        if (idx + 1) % 100000 == 0:
            print(f"  Processed: {idx + 1:,} / {len(df):,}")

    db.events.insert_many(events)
    print(f" Events: {len(events):,} documents")

    # Create indexes
    db.events.create_index([('user_id', ASCENDING)])
    db.events.create_index([('product_id', ASCENDING)])
    db.events.create_index([('event_type', ASCENDING)])


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print(" MONGODB DATA LOADING")
    print(f" Data Directory: {DATA_DIR}")
    print(f" Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    db = get_connection()

    try:
        load_users(db)
        load_products(db)
        campaigns_mapping = load_campaigns(db)
        load_messages(db, campaigns_mapping)
        load_events(db)

        print("\n" + "=" * 80)
        print(" MONGODB DATA LOADING COMPLETED SUCCESSFULLY!")
        print("=" * 80)

        # Print collection stats
        print("\n Collection Statistics:")
        for collection_name in db.list_collection_names():
            count = db[collection_name].count_documents({})
            print(f"   - {collection_name}: {count:,} documents")

    except Exception as e:
        print(f"\n Error: {e}")
        raise

    finally:
        print("\n Connection closed")


if __name__ == "__main__":
    main()