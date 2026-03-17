
"""
This script loads cleaned CSV data into the psql
In this script i will use batches for loading data, it will increase the speed
Run this AFTER create_schema_psql.py

Required files in output/cleaned/:
- clients_cleaned.csv
- friends_cleaned.csv
- campaigns_cleaned.csv
- messages_cleaned.csv
- events_cleaned.csv
"""

import psycopg2
import psycopg2.extras
import pandas as pd
import os


#config
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..', 'output', 'cleaned'))

# PostgreSQL connection settings
# Change password to your own
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'bigdata',
    'user': 'postgres',
    'password': ''  #i will make this empty, please use your own password, i don't want to show mine
}


# =============================================================================
# DATABASE CONNECTION
# =============================================================================

def get_connection():
    #Create psql connection
    conn = psycopg2.connect(**DB_CONFIG)
    print(f" Connected to PostgreSQL ({DB_CONFIG['database']})")
    return conn


def execute_batch(cur, query, params_list, description=""):
    #Execute batch insert with progress
    try:
        psycopg2.extras.execute_batch(cur, query, params_list, page_size=10000)
        if description:
            print(f" {description}: {len(params_list):,} rows")
        return True
    except Exception as e:
        print(f" Error: {e}")
        return False


# =============================================================================
# 1. LOAD USERS and CLIENTS
# =============================================================================
def load_users_and_clients(cur, conn):
    """
    Load users and clients from BOTH sources:

    Merge both sources to ensure NO clients are lost.
    """
    print("\n" + "=" * 80)
    print(" LOADING USERS & CLIENTS")
    print("=" * 80)

    CLIENT_ID_PREFIX = '151591562'
    prefix_len = len(CLIENT_ID_PREFIX)


    messages_df = pd.read_csv(os.path.join(DATA_DIR, 'messages_cleaned.csv'), low_memory=False)
    all_user_ids = set(messages_df['user_id'].dropna().unique())
    print(f"  Unique users in messages: {len(all_user_ids):,}")

    all_clients = {}  # {client_id: {user_id, user_device_id, first_purchase_date}}

    print("  Parsing clients from messages")
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

    print(f" Clients parsed from messages: {len(all_clients):,}")


    clients_df = pd.read_csv(os.path.join(DATA_DIR, 'clients_cleaned.csv'))
    print(f"  Clients from clients_cleaned.csv: {len(clients_df):,}")

    added_count = 0
    updated_count = 0

    for _, row in clients_df.iterrows():
        client_id = int(row['client_id'])
        user_id = int(row['user_id'])
        user_device_id = int(row['user_device_id'])
        first_purchase_date = row['first_purchase_date'] if pd.notna(
            row['first_purchase_date']) else None

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

        # Also ensure user_id exists in all_user_ids
        all_user_ids.add(user_id)

    print(f"  New clients from clients_cleaned.csv (not in messages): {added_count:,}")
    print(f"  Updated clients (in both sources): {updated_count:,}")

    user_params = [(int(user_id),) for user_id in all_user_ids]

    execute_batch(cur,
                  "INSERT INTO users (user_id) VALUES (%s) ON CONFLICT DO NOTHING",
                  user_params,
                  "Users")

    conn.commit()
    print(f" Users committed ({len(all_user_ids):,} rows)")


    client_params = [
        (
            client['client_id'],
            client['user_id'],
            client['user_device_id'],
            client['first_purchase_date']
        )
        for client in all_clients.values()
    ]

    execute_batch(cur,
                  """INSERT INTO clients (client_id, user_id, user_device_id, first_purchase_date) 
                     VALUES (%s, %s, %s, %s) ON CONFLICT (client_id) DO UPDATE 
                     SET first_purchase_date = EXCLUDED.first_purchase_date""",
                  client_params,
                  "Clients")

    conn.commit()

    # Count statistics
    purchaser_count = sum(1 for c in all_clients.values() if c['first_purchase_date'] is not None)

    print(f"\n  Total: {len(all_user_ids):,} users, {len(all_clients):,} clients")
    print(f"  Clients with purchases: {purchaser_count:,}")
    print(f"  Clients without purchases: {len(all_clients) - purchaser_count:,}")

# =============================================================================
# 2. LOAD FRIENDS
# =============================================================================

def load_friends(cur, conn):
    #Load friends from friends_cleaned.csv
    print("\n" + "=" * 80)
    print(" LOADING FRIENDS")
    print("=" * 80)

    df = pd.read_csv(os.path.join(DATA_DIR, 'friends_cleaned.csv'))

    # get all valid user_ids from users table
    cur.execute("SELECT user_id FROM users")
    valid_user_ids = set(row[0] for row in cur.fetchall())
    print(f"  Valid users in database: {len(valid_user_ids):,}")

    valid_params = []
    invalid_count = 0

    for _, row in df.iterrows():
        user_id = int(row['user_id'])
        friend_id = int(row['friend_id'])

        # BOTH must exist in users table
        if user_id in valid_user_ids and friend_id in valid_user_ids:
            valid_params.append((user_id, friend_id))
        else:
            invalid_count += 1

    print(f"  Valid friendships: {len(valid_params):,}")
    print(f"  Filtered out (invalid user_id): {invalid_count:,}")

    if invalid_count > 0:
        print(f" Warning: {invalid_count:,} friendships reference non-existent users")

    if valid_params:
        execute_batch(cur,
                      "INSERT INTO friends (user_id, friend_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                      valid_params,
                      "Friends")

        conn.commit()
        print(f"\n  Total: {len(valid_params):,} friendships loaded")
    else:
        print(f"\n  No valid friendships to insert!")


# =============================================================================
# 3. LOAD CAMPAIGNS
# =============================================================================

def load_campaigns(cur, conn):
    """
    Load campaigns and split tables from campaigns_cleaned.csv

    Returns:
    - campaign_id_map: {original_id: surrogate_id} for messages FK
    """
    print("\n" + "=" * 80)
    print(" LOADING CAMPAIGNS")
    print("=" * 80)

    df = pd.read_csv(os.path.join(DATA_DIR, 'campaigns_cleaned.csv'))
    print(f"  Total campaigns: {len(df):,}")


    df['surrogate_id'] = range(1, len(df) + 1)

    campaign_params = []
    for _, row in df.iterrows():
        campaign_params.append((
            row['surrogate_id'],
            int(row['id']),
            row['campaign_type'],
            row['channel'],
            row['topic'] if pd.notna(row['topic']) else None,
            row['started_at'] if pd.notna(row['started_at']) else None,
            row['finished_at'] if pd.notna(row['finished_at']) else None,
            int(row['total_count']) if pd.notna(row['total_count']) else None,
            int(row['subject_length']) if pd.notna(row['subject_length']) else None,
            bool(row['warmup_mode']),
            bool(row['subject_with_personalization']),
            bool(row['subject_with_deadline']),
            bool(row['subject_with_emoji']),
            bool(row['subject_with_bonuses']),
            bool(row['subject_with_discount']),
            bool(row['subject_with_saleout'])
        ))

    execute_batch(cur,
                  """INSERT INTO campaigns 
                     (id, campaign_id, campaign_type, channel, topic, started_at, finished_at, 
                      total_count, subject_length, warmup_mode, subject_with_personalization,
                      subject_with_deadline, subject_with_emoji, subject_with_bonuses,
                      subject_with_discount, subject_with_saleout)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                  campaign_params,
                  "Campaigns")


    ab_test_params = []
    hour_limit_params = []
    is_test_params = []
    position_params = []

    for _, row in df.iterrows():
        surrogate_id = row['surrogate_id']

        if pd.notna(row['ab_test']):
            ab_test_params.append((surrogate_id, bool(row['ab_test'])))
        if pd.notna(row['hour_limit']):
            hour_limit_params.append((surrogate_id, float(row['hour_limit'])))
        if pd.notna(row['is_test']):
            is_test_params.append((surrogate_id, bool(row['is_test'])))
        if pd.notna(row['position']):
            position_params.append((surrogate_id, int(row['position'])))

    if ab_test_params:
        execute_batch(cur, "INSERT INTO campaign_ab_test (campaign_id, ab_test) VALUES (%s, %s)", ab_test_params)
    if hour_limit_params:
        execute_batch(cur, "INSERT INTO campaign_hour_limit (campaign_id, hour_limit) VALUES (%s, %s)",
                      hour_limit_params)
    if is_test_params:
        execute_batch(cur, "INSERT INTO campaign_test (campaign_id, is_test) VALUES (%s, %s)", is_test_params)
    if position_params:
        execute_batch(cur, "INSERT INTO campaign_position (campaign_id, position) VALUES (%s, %s)", position_params)

    conn.commit()



    campaign_id_map = dict(zip(df['id'], df['surrogate_id']))

    print(f"\n  Total: {len(campaign_params):,} campaigns")
    print(f"  Split: {len(ab_test_params):,} ab_test, {len(hour_limit_params):,} hour_limit, "
          f"{len(is_test_params):,} is_test, {len(position_params):,} position")
    print(f"  campaign_id_map created: {len(campaign_id_map):,} entries")

    return campaign_id_map

# =============================================================================
# 4. LOAD EMAIL PROVIDERS
# =============================================================================

def load_email_providers(cur, conn):
    #Extract and load unique email providers from messages
    print("\n" + "=" * 80)
    print(" LOADING EMAIL PROVIDERS")
    print("=" * 80)

    df = pd.read_csv(os.path.join(DATA_DIR, 'messages_cleaned.csv'), low_memory=False)

    # Get unique providers
    providers = df['email_provider'].dropna().unique()

    params = [(str(provider)) for provider in providers]

    execute_batch(cur,
                  "INSERT INTO email_providers (email_provider) VALUES (%s) ON CONFLICT DO NOTHING",
                  [(p,) for p in params],
                  "Email Providers")

    conn.commit()
    print(f"\n  Total: {len(providers):,} unique email providers")


# =============================================================================
# 5. LOAD MESSAGES, LARGEST TABLE - 3M ROWS, USING BATCHES
# =============================================================================
def load_messages(cur, conn, campaign_id_map):
    """
    Load messages and all split tables from messages_cleaned.csv
    Important:
    - Map original campaign_id to surrogate_id for FK constraint
    - Filter to only include valid user_ids (exist in users table)
    """
    print("\n" + "=" * 80)
    print(" LOADING MESSAGES")
    print("=" * 80)

    df = pd.read_csv(os.path.join(DATA_DIR, 'messages_cleaned.csv'), low_memory=False)
    print(f"  Total messages: {len(df):,}")

    cur.execute("SELECT user_id FROM users")
    valid_user_ids = set(row[0] for row in cur.fetchall())
    print(f"  Valid users in database: {len(valid_user_ids):,}")

    cur.execute("SELECT id, email_provider FROM email_providers")
    email_provider_map = {row[1]: row[0] for row in cur.fetchall()}

    batch_size = 200000
    total_batches = (len(df) + batch_size - 1) // batch_size

    total_inserted = 0
    total_filtered = 0

    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min((batch_num + 1) * batch_size, len(df))
        batch_df = df.iloc[start_idx:end_idx]

        # Prepare batch data
        message_params = []
        recipient_params = []
        device_info_params = []
        opens_params = []
        clicks_params = []
        negatives_params = []
        purchases_params = []

        for _, row in batch_df.iterrows():
            user_id = int(row['user_id'])
            original_campaign_id = int(row['campaign_id'])

            # Filter: user_id must exist
            if user_id not in valid_user_ids:
                total_filtered += 1
                continue

            # Map: original_campaign_id → surrogate_id
            surrogate_campaign_id = campaign_id_map.get(original_campaign_id)
            if surrogate_campaign_id is None:
                total_filtered += 1
                print(f" Warning: campaign_id {original_campaign_id} not found in campaigns!")
                continue

            message_id = int(row['id'])

            # Main messages table
            message_params.append((
                message_id,
                row['message_id'],
                surrogate_campaign_id,
                user_id,
                row['message_type'],
                row['channel'],
                row['date'] if pd.notna(row['date']) else None,
                row['sent_at'] if pd.notna(row['sent_at']) else None,
                row['created_at'] if pd.notna(row['created_at']) else None,
                row['updated_at'] if pd.notna(row['updated_at']) else None,
                bool(row['is_opened']),
                bool(row['is_clicked']),
                bool(row['is_unsubscribed']),
                bool(row['is_hard_bounced']),
                bool(row['is_soft_bounced']),
                bool(row['is_complained']),
                bool(row['is_blocked']),
                bool(row['is_purchased'])
            ))

            # messages_recipient
            if pd.notna(row['client_id']):
                email_provider_id = email_provider_map.get(row['email_provider'], None)
                recipient_params.append((message_id, int(row['client_id']), email_provider_id))

            # messages_device_info
            if pd.notna(row['platform']) or pd.notna(row['stream']):
                device_info_params.append((message_id, row['stream'] if pd.notna(row['stream']) else None,
                                           row['platform'] if pd.notna(row['platform']) else None))

            # message_opens
            if bool(row['is_opened']):
                opens_params.append((message_id, row['opened_first_time_at'], row['opened_last_time_at'] ))

            # message_clicks
            if bool(row['is_clicked']):
                clicks_params.append((message_id, row['clicked_first_time_at'], row['clicked_last_time_at']))

            # message_negatives
            if any([bool(row['is_unsubscribed']), bool(row['is_hard_bounced']), bool(row['is_soft_bounced']),
                    bool(row['is_complained']), bool(row['is_blocked'])]):
                negatives_params.append((message_id, row['unsubscribed_at'] if pd.notna(
                    row['unsubscribed_at']) else None, row['hard_bounced_at'] if pd.notna(
                    row['hard_bounced_at']) else None, row['soft_bounced_at'] if pd.notna(
                    row['soft_bounced_at']) else None, row['complained_at'] if pd.notna(
                    row['complained_at']) else None,
                                         row['blocked_at'] if pd.notna(row['blocked_at']) else None))

            # message_purchases
            if bool(row['is_purchased']):
                purchases_params.append(
                    (message_id, row['purchased_at']))

        # Insert THIS BATCH
        if message_params:
            execute_batch(cur,
                          """INSERT INTO messages 
                             (id, message_id, campaign_id, user_id, message_type, channel, date, sent_at,
                              created_at, updated_at, is_opened, is_clicked, is_unsubscribed,
                              is_hard_bounced, is_soft_bounced, is_complained, is_blocked, is_purchased)
                             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                          message_params,
                          f"Messages batch {batch_num + 1}/{total_batches}")

            if recipient_params:
                execute_batch(cur,
                              "INSERT INTO messages_recipient (message_id, client_id, email_provider_id) VALUES (%s, %s, %s)",
                              recipient_params)
            if device_info_params:
                execute_batch(cur,
                              "INSERT INTO messages_device_info (message_id, stream, platform) VALUES (%s, %s, %s)",
                              device_info_params)
            if opens_params:
                execute_batch(cur,
                              "INSERT INTO message_opens (message_id, opened_first_time_at, opened_last_time_at) VALUES (%s, %s, %s)",
                              opens_params)
            if clicks_params:
                execute_batch(cur,
                              "INSERT INTO message_clicks (message_id, clicked_first_time_at, clicked_last_time_at) VALUES (%s, %s, %s)",
                              clicks_params)
            if negatives_params:
                execute_batch(cur,
                              "INSERT INTO message_negatives (message_id, unsubscribed_at, hard_bounced_at, soft_bounced_at, complained_at, blocked_at) VALUES (%s, %s, %s, %s, %s, %s)",
                              negatives_params)
            if purchases_params:
                execute_batch(cur, "INSERT INTO message_purchases (message_id, purchased_at) VALUES (%s, %s)",
                              purchases_params)

            conn.commit()
            total_inserted += len(message_params)



        print(f" Batch {batch_num + 1}/{total_batches}: {len(batch_df):,} rows")

    print(f"\n  Total: {total_inserted:,} messages loaded")
    print(f"  Filtered out (invalid user_id or campaign_id): {total_filtered:,}")

    return total_inserted


# =============================================================================
# 6. LOAD PRODUCTS & CATEGORIES
# =============================================================================

def load_products_and_categories(cur, conn):
    #Extract and load unique products and categories from events
    print("\n" + "=" * 80)
    print(" LOADING PRODUCTS & CATEGORIES")
    print("=" * 80)

    df = pd.read_csv(os.path.join(DATA_DIR, 'events_cleaned.csv'))

    # Products
    products_df = df[['product_id', 'brand']].drop_duplicates()
    product_params = [
        (int(row['product_id']), row['brand'] if pd.notna(row['brand']) else None)
        for _, row in products_df.iterrows()
    ]

    execute_batch(cur,
                  "INSERT INTO products (product_id, brand) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                  product_params,
                  "Products")

    # Categories
    categories_df = df[['category_id', 'category_code']].drop_duplicates()
    category_params = [
        (int(row['category_id']) if pd.notna(row['category_id']) else None,
         row['category_code'] if pd.notna(row['category_code']) else None)
        for _, row in categories_df.iterrows()
    ]

    execute_batch(cur,
                  "INSERT INTO categories (category_id, category_code) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                  category_params,
                  "Categories")

    conn.commit()
    print(f"\n  Total: {len(products_df):,} products, {len(categories_df):,} categories")


# =============================================================================
# 7. LOAD EVENTS
# =============================================================================

def load_events(cur, conn):
    #Load events from events_cleaned.csv

    print("\n" + "=" * 80)
    print(" LOADING EVENTS ")
    print("=" * 80)

    df = pd.read_csv(os.path.join(DATA_DIR, 'events_cleaned.csv'))
    print(f"  Total events: {len(df):,}")


    batch_size = 100000
    total_batches = (len(df) + batch_size - 1) // batch_size

    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min((batch_num + 1) * batch_size, len(df))
        batch_df = df.iloc[start_idx:end_idx]

        # Prepare batch data
        params = []
        for _, row in batch_df.iterrows():
            params.append((
                row['event_time'],
                row['event_type'],
                int(row['product_id']),
                int(row['category_id']),
                float(row['price']),
                int(row['user_id']),
                row['user_session']
            ))


        execute_batch(cur,
                      """INSERT INTO events 
                         (event_time, event_type, product_id, category_id, price, user_id, user_session)
                         VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                      params,
                      f"Events batch {batch_num + 1}/{total_batches}")

        # Commit after each batch
        conn.commit()

        print(f" Batch {batch_num + 1}/{total_batches}: {len(batch_df):,} rows")

    print(f"\n  Total: {len(df):,} events loaded in {total_batches} batches")


# =============================================================================
# 8. VERIFY DATA
# =============================================================================

def verify_data(cur):
    #Verify all data was loaded correctly
    print("\n" + "=" * 80)
    print(" VERIFYING DATA")
    print("=" * 80)

    tables = [
        'users', 'clients', 'friends', 'campaigns', 'campaign_ab_test',
        'campaign_hour_limit', 'campaign_test', 'campaign_position',
        'email_providers', 'messages', 'messages_recipient', 'messages_device_info',
        'message_opens', 'message_clicks', 'message_negatives', 'message_purchases',
        'products', 'categories', 'events'
    ]

    print("\n  Row counts:")
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"    - {table:<30} {count:>12,} rows")

    print("\n Data verification complete")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print(" POSTGRESQL DATA LOADING")
    print(f" Data Directory: {DATA_DIR}")
    print("=" * 80)

    # Connect
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Load data in correct order (respecting FK constraints)
        load_users_and_clients(cur, conn)
        load_friends(cur, conn)
        campaign_id_map = load_campaigns(cur, conn)
        load_email_providers(cur, conn)
        load_messages(cur, conn, campaign_id_map)
        load_products_and_categories(cur, conn)
        load_events(cur, conn)

        # Verify
        verify_data(cur)

        print("\n" + "=" * 80)
        print(" POSTGRESQL DATA LOADING COMPLETED SUCCESSFULLY!")
        print("=" * 80)


    except Exception as e:
        print(f"\n Error: {e}")
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()
        print("\n Connection closed")


if __name__ == "__main__":
    main()