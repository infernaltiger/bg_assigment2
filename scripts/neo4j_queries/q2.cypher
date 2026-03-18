// scripts/neo4j_queries/q2.cypher
// Task 4: Personalized Product Recommendations
// Find top products to display on user's home page based on behavior
// Parameter: $user_id (e.g., 560126337)
// Logic is the same as previous queries

// 1. Analyze user's purchase history (highest weight)
// 2. Analyze user's view/cart history (medium weight)
// 3. Find similar users (via friends or similar behavior)
// 4. Rank products by interaction score

MATCH (user:User {user_id: $user_id})
MATCH (user)-[r:PURCHASED|VIEWED|CART]->(product:Product)
WITH
    user.user_id AS user_id,
    product.product_id AS product_id,
    product.brand AS brand,
    r.category_code AS category_code,
    SUM(CASE
        WHEN type(r) = 'PURCHASED' THEN 3
        WHEN type(r) = 'CART' THEN 2
        WHEN type(r) = 'VIEWED' THEN 1
        ELSE 0
    END) AS user_score,
    COUNT(*) AS user_interactions,
    AVG(r.price) AS avg_price

WITH
    user_id,
    product_id,
    brand,
    category_code,
    user_score,
    user_interactions,
    avg_price

OPTIONAL MATCH (u:User {user_id: user_id})-[:FRIENDS_WITH]->(friend:User)
OPTIONAL MATCH (friend)-[fp:PURCHASED]->(fp_product:Product)
WITH
    user_id,
    product_id,
    brand,
    category_code,
    user_score,
    user_interactions,
    avg_price,
    COLLECT(DISTINCT fp_product.product_id) AS friend_purchased_products

WITH
    user_id,
    product_id,
    brand,
    category_code,
    user_score,
    user_interactions,
    avg_price,
    SIZE([p IN friend_purchased_products WHERE p = product_id]) AS friend_purchase_count

WITH
    user_id,
    product_id,
    brand,
    category_code,
    user_score + (2 * friend_purchase_count) AS total_score,
    user_interactions + friend_purchase_count AS total_interactions,
    avg_price

WITH
    user_id,
    product_id,
    brand,
    category_code,
    total_score,
    total_interactions,
    ROUND(avg_price, 2) AS avg_price,
    CASE
        WHEN total_score >= 10 THEN 'High Recommendation'
        WHEN total_score >= 5 THEN 'Medium Recommendation'
        ELSE 'Low Recommendation'
    END AS recommendation_level

RETURN
    product_id,
    brand,
    category_code,
    total_score,
    total_interactions,
    avg_price,
    recommendation_level
ORDER BY total_score DESC, total_interactions DESC
LIMIT 20;