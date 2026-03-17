
"""
This script performs  data cleaning that applies to all files, so we can use then later when loading data.
Output: Cleaned CSV files with same structure as original
"""

import pandas as pd
import os

#config and path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..','data'))
OUTPUT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..', 'output', 'cleaned'))

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Client ID prefix that was given
CLIENT_ID_PREFIX = '151591562'

# Boolean columns for each file
MESSAGE_BOOL_COLS = [
    'is_opened', 'is_clicked', 'is_unsubscribed', 'is_hard_bounced',
    'is_soft_bounced', 'is_complained', 'is_blocked', 'is_purchased'
]




#helper functions
def convert_boolean(df, columns):
    #Convert t/f strings to boolean True/False. NaN values are converted to False.
    for col in columns:
        if col in df.columns:
            df[col] = df[col].map({'t': True, 'f': False})
    return df


def save_csv(df, filename):
    #Save dataframe to CSV with progress info
    filepath = os.path.join(OUTPUT_DIR, filename)
    df.to_csv(filepath, index=False)
    file_size_mb = os.path.getsize(filepath) / 1024 ** 2
    print(f" Saved {filename}: {len(df):,} rows, {file_size_mb:.2f} MB")
    return filepath


def print_section(title):
    #Print section header
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


# =============================================================================
# 1. CAMPAIGNS CLEANING
# =============================================================================

def clean_campaigns():
    """
    Cleaning for campaigns.csv
    Steps:
    - Parse timestamps
    - Remove columns with 100% NULL
    - Drop rows with NULL
    """
    print_section("1. CAMPAIGNS CLEANING")

    df = pd.read_csv(os.path.join(DATA_DIR, 'campaigns.csv'))
    print(f"  Original: {len(df):,} rows × {len(df.columns)} columns")
    original_rows = len(df)

    # Parse timestamps
    date_cols = ['started_at', 'finished_at']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Check for 100% NULL columns (should be none based on EDA, just a safe check)
    null_pct = (df.isnull().sum() / len(df)) * 100
    full_null_cols = null_pct[null_pct == 100].index.tolist()
    if full_null_cols:
        df = df.drop(columns=full_null_cols)
        print(f"  - Removed {len(full_null_cols)} columns with 100% NULL: {full_null_cols}")


    # Save cleaned file
    save_csv(df, 'campaigns_cleaned.csv')
    print()
    print(f"\n  Summary: {len(df):,} rows cleaned")
    return df


# =============================================================================
# 2. MESSAGES CLEANING
# =============================================================================

def clean_messages():
    """
    Cleaning for messages.csv
    Steps:
    - Convert boolean columns
    - Parse timestamps
    - Remove 100% NULL columns (category)

    """
    print_section("2. MESSAGES CLEANING")

    df = pd.read_csv(os.path.join(DATA_DIR, 'messages.csv'), low_memory=False)
    print(f"  Original: {len(df):,} rows × {len(df.columns)} columns")
    original_rows = len(df)

    # Remove 100% NULL column (category based on EDA)
    if 'category' in df.columns:
        null_pct = (df['category'].isnull().sum() / len(df)) * 100
        if null_pct == 100:
            df = df.drop(columns=['category'])
            print(f"  - Removed 'category' column (100% NULL)")

    # Convert boolean columns
    df = convert_boolean(df, MESSAGE_BOOL_COLS)

    # Parse timestamps
    date_cols = ['sent_at', 'opened_first_time_at', 'opened_last_time_at',
                 'clicked_first_time_at', 'clicked_last_time_at',
                 'unsubscribed_at', 'hard_bounced_at', 'soft_bounced_at',
                 'complained_at', 'blocked_at', 'purchased_at']

    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')


    # Save cleaned file
    save_csv(df, 'messages_cleaned.csv')

    print(f"\n  Summary: {len(df):,} rows cleaned")
    return df


# =============================================================================
# 3. EVENTS CLEANING
# =============================================================================

def clean_events():
    """
    Cleaning for events.csv
    Steps:
    - Parse timestamps
    - Remove columns with 100% NULL (if any)
    """
    print_section("3. EVENTS CLEANING")

    df = pd.read_csv(os.path.join(DATA_DIR, 'events.csv'))
    print(f"  Original: {len(df):,} rows × {len(df.columns)} columns")

    # Parse timestamps
    df['event_time'] = pd.to_datetime(df['event_time'], errors='coerce')

    # Check for 100% NULL columns
    null_pct = (df.isnull().sum() / len(df)) * 100
    full_null_cols = null_pct[null_pct == 100].index.tolist()
    if full_null_cols:
        df = df.drop(columns=full_null_cols)
        print(f"  - Removed {len(full_null_cols)} columns with 100% NULL")

    # Save cleaned file
    save_csv(df, 'events_cleaned.csv')

    print(f"\n  Summary: {len(df):,} rows cleaned")
    return df


# =============================================================================
# 4. FRIENDS CLEANING
# =============================================================================

def clean_friends():
    """
    Cleaning for friends.csv

    Steps:
    - Remove duplicate rows
    - Remove self-friendship (friend1 == friend2)
    - Ensure integer types
    - Rename columns to match schema (user_id, friend_id)
    """
    print_section("4. FRIENDS CLEANING")

    df = pd.read_csv(os.path.join(DATA_DIR, 'friends.csv'))
    print(f"  Original: {len(df):,} rows")

    # Remove exact duplicates
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        df = df.drop_duplicates()
        print(f"  - Removed {duplicates:,} duplicate row(s)")

    # Ensure friend1 != friend2 (no self-friendship)
    self_friend = df[df['friend1'] == df['friend2']]
    if len(self_friend) > 0:
        df = df[df['friend1'] != df['friend2']]
        print(f"  - Removed {len(self_friend):,} self-friendship row(s)")

    # Ensure integer types for consistency
    df['friend1'] = df['friend1'].astype('int64')
    df['friend2'] = df['friend2'].astype('int64')

    # Rename columns
    df = df.rename(columns={'friend1': 'user_id', 'friend2': 'friend_id'})

    save_csv(df, 'friends_cleaned.csv')

    print(f"\n  Summary: {len(df):,} unique friendships")
    return df


# =============================================================================
# 5. CLIENTS CLEANING
# =============================================================================

def clean_clients():
    """
    Cleaning for client_first_purchase_date.csv

    Steps:
    - Validate client_id formula
    - Parse dates
    - Ensure correct types
    """
    print_section("5. CLIENTS CLEANING")

    df = pd.read_csv(os.path.join(DATA_DIR, 'client_first_purchase_date.csv'))
    print(f"  Original: {len(df):,} rows")

    # Validate client_id formula using str comparison to avoid int64 overflow - i had that problem
    # client_id = '151591562' + user_id + user_device_id
    expected_client_id_str = (CLIENT_ID_PREFIX +
                              df['user_id'].astype(str) +
                              df['user_device_id'].astype(str))

    actual_client_id_str = df['client_id'].astype(str)

    invalid = df[actual_client_id_str != expected_client_id_str]
    if len(invalid) > 0:
        print(f" Warning: {len(invalid):,} rows have invalid client_id formula")
        print(f" Sample invalid rows:")
        print(invalid.head())
    else:
        print(f" All client_id values match formula")

    # Parse date
    df['first_purchase_date'] = pd.to_datetime(df['first_purchase_date'], errors='coerce')

    # Ensure correct types
    df['client_id'] = df['client_id'].astype('int64')
    df['user_id'] = df['user_id'].astype('int64')
    df['user_device_id'] = df['user_device_id'].astype('int64')

    save_csv(df, 'clients_cleaned.csv')

    print(f"\n  Summary: {len(df):,} clients validated")
    return df


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print(" UNIVERSAL DATA CLEANING AND PREPARATION")
    print(f" Input:  {DATA_DIR}")
    print(f" Output: {OUTPUT_DIR}")
    print("=" * 80)

    # Process all files
    clean_campaigns()
    clean_messages()
    clean_events()
    clean_friends()
    clean_clients()

    # Final summary
    print_section("CLEANING SUMMARY")

    output_files = os.listdir(OUTPUT_DIR)
    total_rows = 0
    total_size_mb = 0

    for filename in sorted(output_files):
        if filename.endswith('.csv'):
            filepath = os.path.join(OUTPUT_DIR, filename)
            df = pd.read_csv(filepath)
            file_size_mb = os.path.getsize(filepath) / 1024 ** 2
            total_rows += len(df)
            total_size_mb += file_size_mb
            print(f"  {filename:<35} | {len(df):>12,} rows | {file_size_mb:>8.2f} MB")

    print("-" * 80)
    print(f"  {'TOTAL':<35} | {total_rows:>12,} rows | {total_size_mb:>8.2f} MB")
    print("=" * 80)
    print("Data cleaning completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()