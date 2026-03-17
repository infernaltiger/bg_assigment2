
"""
Find active users for recommendation testing for q2 and q3

This query is only to find user with most events, so the q2 and q3 will be more interesting

i wrote the query here and don't pull it by the file - it was easier.
The same query in .sql format have the same name and is placed is the same folder
"""

import psycopg2
import pandas as pd


# Configuration of psql. I assume db bigbata is already created and have data in it
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'bigdata',
    'user': 'postgres',
    'password': ''   #i will make this empty, please use your own password, i don't want to show mine
}

query = """
SELECT 
    e.user_id,
    COUNT(*) AS total_events,
    COUNT(CASE WHEN e.event_type = 'purchase' THEN 1 END) AS purchases,
    COUNT(CASE WHEN e.event_type = 'view' THEN 1 END) AS views,
    COUNT(CASE WHEN e.event_type = 'cart' THEN 1 END) AS cart_additions,
    COUNT(DISTINCT e.product_id) AS unique_products
FROM events e
GROUP BY e.user_id
HAVING COUNT(*) >= 10
ORDER BY purchases DESC, total_events DESC
LIMIT 20;
"""

conn = psycopg2.connect(**DB_CONFIG)
df = pd.read_sql_query(query, conn)
conn.close()

print("=" * 80)
print(" Top 20 Most Active Users")
print("=" * 80)
print(df.to_string(index=False))
print()
print(f"Recommended user_id for q2.sql: {df.iloc[0]['user_id']}")