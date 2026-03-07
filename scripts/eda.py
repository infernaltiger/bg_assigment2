import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


#path of script, needed to create path to other folders
script_dir = os.path.dirname(os.path.abspath(__file__))

#data path
data_folder = os.path.join(script_dir, '..', 'data')
data_folder = os.path.normpath(data_folder)

files = {
    'events': 'events.csv',
    'campaigns': 'campaigns.csv',
    'messages': 'messages.csv',
    'clients': 'client_first_purchase_date.csv',
    'friends': 'friends.csv'
}

#output path
output_folder = os.path.normpath(os.path.join(script_dir, '..', 'output'))


def analyze_file(name, filepath):
    print("-"*60)
    print("File name:", name)
    print("-" * 60)

    #messages only thing - DtypeWarning because of mixed types
    if name == 'messages':
        df = pd.read_csv(filepath, low_memory=False)
    else:
        df = pd.read_csv(filepath)

    #general info
    print(f"Shape: {df.shape[0]:,} rows, {df.shape[1]} columns")
    print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024 ** 2:.2f} MB")

    #NaN counting
    missing = df.isnull().sum()
    missing_pct = (missing / len(df)) * 100
    missing_df = pd.DataFrame({'Missing Count': missing, 'Missing %': missing_pct})
    missing_df = missing_df[missing_df['Missing Count'] > 0].sort_values(by='Missing Count', ascending=False)

    if not missing_df.empty:
        print("\n Columns with missing values:")
        print(missing_df.to_string())
    else:
        print("\n No missing values")

    # 3. unique values for possible main keys
    print("\n Unique values:")
    key_columns = [col for col in df.columns if
                   'id' in col.lower() or 'user' in col.lower() or 'category' in col.lower()]
    for col in key_columns:
        if col in df.columns:
            unique_count = df[col].nunique()
            print(f"   - {col}: {unique_count:,} ({unique_count / len(df) * 100:.2f}%)")

    #analysys for each file
    if name == 'events':
        print("\n Distribution of event_type:")
        print(df['event_type'].value_counts())
        print("\n Price info:")
        print(df['price'].describe())
        #looking for unreal values outliars
        if (df['price'] <= 0).any():
            print(f"{(df['price'] <= 0).sum()} price is <= 0")

    # i commented this because the it takes too long to execute this part
    # size of messages with low_memory=False is very big
    # elif name == 'messages':
    #     print("\n Messages stats:")
    #     total = len(df)
    #     opened = df['is_opened'].sum()
    #     clicked = df['is_clicked'].sum()
    #     purchased = df['is_purchased'].sum()
    #
    #     print(f"   - Sended total: {total:,}")
    #     print(f"   - Opened: {opened:,} ({opened / total * 100:.2f}%)")
    #     print(f"   - Clicked: {clicked:,} ({clicked / total * 100:.2f}%)")
    #     print(f"   - Bought: {purchased:,} ({purchased / total * 100:.2f}%)")
    #
    #     #client_id logic
    #     if 'client_id' in df.columns and 'user_id' in df.columns:
    #         sample_client = df['client_id'].iloc[0]
    #         sample_user = df['user_id'].iloc[0]
    #         expected_client = int(f"151591562{sample_user}")
    #         match = sample_client == expected_client
    #         print("\n Checking formula for client_id:")
    #         print(f"  user_id: {sample_user}")
    #         print(f"  client_id: {sample_client}")
    #         print(f"  expected client_id: {expected_client}")
    #         print(f"  Correct match" if match else f"  Incorrect match")


    elif name == 'friends':
        print("\n friends Graph:")
        pairs = df.apply(lambda x: tuple(sorted([x['friend1'], x['friend2']])), axis=1)
        unique_pairs = pairs.nunique()
        total_rows = len(df)

        print(f"  Total record: {total_rows:,}")
        print(f"  Unique pairs of friends: {unique_pairs:,}")

        if total_rows == unique_pairs * 2:
            print("  Symmetric graph (A->B, B->A).")
        elif total_rows == unique_pairs:
            print("   No doubling (only A->B, no B->A).")
        else:
            print("  Mixed format or contains single cons.")

        # nodes degree
        all_users = pd.concat([df['friend1'], df['friend2']])
        degree = all_users.value_counts()
        print("\n  Stats of num of friends for user:")
        print(degree.describe())

    elif name == 'campaigns':
        print("\n Campaigns:")
        print(df['campaign_type'].value_counts())
        print("\n Channels:")
        print(df['channel'].value_counts())

    elif name == 'clients':
        print("\n Dates of first purchases interval:")
        print(f"   Min: {df['first_purchase_date'].min()}")
        print(f"   Max: {df['first_purchase_date'].max()}")

    #saving part of a report as csv
    summary_path = os.path.join(output_folder, f"{name}_summary.csv")
    # saving only missing values
    missing_df.to_csv(summary_path)
    print(f"\n Short report saved in: {summary_path}")

    return df

dataframes = {}
for name, filename in files.items():
    filepath = os.path.join(data_folder, filename)
    if os.path.exists(filepath):
        dataframes[name] = analyze_file(name, filepath)
    else:
        print(f" Problem - file not found: {filepath}")

print("\n EDA finished")