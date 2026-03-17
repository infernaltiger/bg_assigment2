
"""
This script performs sma EDA of given data.
Output: printed properties of data in console
"""


import pandas as pd
import os

# Config, data path
SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

# # Part for cheking cleaned data
# #
# DATA_PATH = os.path.join(SCRIPT_PATH, '..','..', 'output\cleaned')
# DATA_PATH = os.path.normpath(DATA_PATH)
#
# CSV_FILES = [
#     "campaigns_cleaned.csv",
#     "client_cleaned.csv",
#     "events_cleaned.csv",
#     "friends_cleaned.csv",
#     "messages_cleaned.csv"
# ]

DATA_PATH = os.path.join(SCRIPT_PATH, '..', '..', 'data')
DATA_PATH = os.path.normpath(DATA_PATH)

CSV_FILES = [
    "campaigns.csv",
    "client_first_purchase_date.csv",
    "events.csv",
    "friends.csv",
    "messages.csv"
]

# Thresholds for reporting
HIGH_NULL_THRESHOLD = 5.0  # Percent
LOW_CARDINALITY_THRESHOLD = 20  # Unique values


def explore_csv(file_path, file_name):

    #Exploration of a single CSV file

    print("\n" + "=" * 80)
    print(f"FILE: {file_name}")
    print("=" * 80)

    try:
        # Read data
        df = pd.read_csv(file_path)

        # Basic Info
        print(f"\n[SHAPE] {df.shape[0]:,} rows x {df.shape[1]} columns")
        print(f"[MEMORY] {df.memory_usage(deep=True).sum() / 1024 ** 2:.2f} MB")

        # Duplicates Check
        dupes = df.duplicated().sum()
        if dupes > 0:
            print(f"[WARNING] Found {dupes:,} duplicate rows ({dupes / len(df) * 100:.2f}%)")
        else:
            print(f"[INFO] No duplicate rows found")

        # Columns and Null Analysis
        print("\n[COLUMNS and NULLS]")
        print("-" * 80)
        print(f"{'Column':<40} | {'Type':<15} | {'Null Count':<12} | {'Null %':<8} | {'Status'}")
        print("-" * 80)

        high_null_cols = []

        for col, dtype in df.dtypes.items():
            null_count = df[col].isnull().sum()
            null_pct = (null_count / len(df)) * 100 if len(df) > 0 else 0

            # Determine status based on null percentage
            if null_pct == 0:
                status = "OK"
            elif null_pct < HIGH_NULL_THRESHOLD:
                status = "LOW"
            else:
                status = "HIGH"
                high_null_cols.append(col)

            print(f"{col:<40} | {str(dtype):<15} | {null_count:<12,} | {null_pct:<8.2f} | {status}")

        if high_null_cols:
            print(f"\n[!] Columns with high null rate (>{HIGH_NULL_THRESHOLD}%): {', '.join(high_null_cols)}")

        # Sample Data
        print("\n[FIRST 5 ROWS]")
        print("-" * 80)
        print(df.head().to_string())

        # Numeric Statistics
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            print("\n[NUMERIC STATISTICS]")
            print("-" * 80)
            print(df[numeric_cols].describe(include='all').loc[['count', 'mean', 'min', 'max']].to_string())

        # Categorical Analysis
        object_cols = df.select_dtypes(include=['object']).columns
        if len(object_cols) > 0:
            print("\n[CATEGORICAL UNIQUES]")
            print("-" * 80)
            for col in object_cols:
                unique_count = df[col].nunique()
                if unique_count <= LOW_CARDINALITY_THRESHOLD:
                    vals = df[col].dropna().unique()
                    print(f"{col:<35} | {unique_count:<6} values | {vals}")
                else:
                    print(f"{col:<35} | {unique_count:<6} values (High cardinality)")

        # Domain Specific Analysis
        print("\n[DOMAIN ANALYSIS]")
        print("-" * 80)

        # Check for potential IDs (
        id_cols = [c for c in df.columns if 'id' in c.lower()]
        for col in id_cols:
            unique_count = df[col].nunique()
            null_count = df[col].isnull().sum()
            # Check if column can be a primary key
            if unique_count == len(df) - null_count and null_count == 0:
                print(f"  [PK CANDIDATE] {col}: Unique values match row count")
            else:
                print(f"  [FK CANDIDATE] {col}: {unique_count:,} unique values")

        # Specific checks based on assignment requirements
        if 'event_type' in df.columns:
            print(f"\n  Event Types:\n{df['event_type'].value_counts().to_string()}")

        if 'campaign_type' in df.columns:
            print(f"\n  Campaign Types:\n{df['campaign_type'].value_counts().to_string()}")

        if 'channel' in df.columns:
            print(f"\n  Channels:\n{df['channel'].value_counts().to_string()}")

        if 'topic' in df.columns:
            print(f"\n  Topics:\n{df['topic'].value_counts().to_string()}")

        # Date Columns
        date_cols = df.select_dtypes(include=['object']).columns
        for col in date_cols:
            if any(x in col.lower() for x in ['date', 'time', 'at']):
                # Try parse without modifying original df permanently if possible,
                # but for exploration copy is fine or just try/except
                try:
                    # Sample check to avoid heavy processing on huge cols
                    sample = df[col].dropna().head(1000)
                    if len(sample) > 0:
                        pd.to_datetime(sample, errors='raise')
                        full_col = pd.to_datetime(df[col], errors='coerce')
                        print(f"\n  [DATE] {col}: {full_col.min()} to {full_col.max()}")
                except:
                    pass

        return df

    except Exception as e:
        print(f"[ERROR] reading {file_name}: {str(e)}")
        return None


def main():
    print("=" * 80)
    print(" DATA EXPLORATION SCRIPT")
    print(f" PATH: {DATA_PATH}")
    print("=" * 80)

    dataframes = {}

    for file_name in CSV_FILES:
        file_path = os.path.join(DATA_PATH, file_name)
        if os.path.exists(file_path):
            df = explore_csv(file_path, file_name)
            if df is not None:
                dataframes[file_name] = df
        else:
            print(f"\n[ERROR] FILE NOT FOUND: {file_path}")

    # Summary Table
    print("\n" + "=" * 80)
    print(" SUMMARY")
    print("=" * 80)
    print(f"{'File':<40} | {'Rows':>12} | {'Size (MB)':>10}")
    print("-" * 80)

    total_rows = 0
    total_size_mb = 0

    for file_name, df in dataframes.items():
        file_path = os.path.join(DATA_PATH, file_name)
        file_size_mb = os.path.getsize(file_path) / 1024 ** 2
        total_rows += len(df)
        total_size_mb += file_size_mb
        print(f"{file_name:<40} | {len(df):>12,} | {file_size_mb:>10.2f}")

    print("-" * 80)
    print(f"{'TOTAL':<40} | {total_rows:>12,} | {total_size_mb:>10.2f}")
    print("=" * 80)




if __name__ == "__main__":
    main()