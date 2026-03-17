-- scripts/psql_queries/q2.sql
-- Task 4: Personalized Product Recommendations
-- Find top products to display on user's home page based on behavior

-- Approach:
-- 1. Analyze user's purchase history (highest weight)
-- 2. Analyze user's view/cart history (medium weight)
-- 3. Find similar users (via friends or similar behavior)
-- 4. Rank products by interaction score

WITH user_behavior AS (
    -- User's own behavior (weighted scoring)
    SELECT
        e.user_id,
        e.product_id,
        p.brand,
        c.category_code,
        SUM(CASE
            WHEN e.event_type = 'purchase' THEN 3
            WHEN e.event_type = 'cart' THEN 2
            WHEN e.event_type = 'view' THEN 1
            ELSE 0
        END) AS interaction_score,
        COUNT(*) AS interaction_count,
        AVG(e.price) AS avg_price
    FROM events e
    JOIN products p ON e.product_id = p.product_id
    JOIN categories c ON e.category_id = c.category_id
    WHERE e.user_id = 560126337  -- Change user_id for different users, i use this user as an example
    GROUP BY e.user_id, e.product_id, p.brand, c.category_code
),
friend_behavior AS (
    -- Friends' purchases (social recommendation)
    SELECT
        f.user_id AS target_user,
        e.product_id,
        p.brand,
        c.category_code,
        SUM(2) AS interaction_score,
        COUNT(*) AS interaction_count,
        AVG(e.price) AS avg_price
    FROM friends f
    JOIN events e ON f.friend_id = e.user_id
    JOIN products p ON e.product_id = p.product_id
    JOIN categories c ON e.category_id = c.category_id
    WHERE f.user_id = 560126337  -- Change user_id for different users, i use 1 user as an example
    AND e.event_type = 'purchase'
    GROUP BY f.user_id, e.product_id, p.brand, c.category_code
),
combined_scores AS (
    -- Combine user + friend scores
    SELECT
        COALESCE(ub.user_id, fb.target_user) AS user_id,
        COALESCE(ub.product_id, fb.product_id) AS product_id,
        COALESCE(ub.brand, fb.brand) AS brand,
        COALESCE(ub.category_code, fb.category_code) AS category_code,
        COALESCE(ub.interaction_score, 0) + COALESCE(fb.interaction_score, 0) AS total_score,
        COALESCE(ub.interaction_count, 0) + COALESCE(fb.interaction_count, 0) AS total_interactions,
        COALESCE(ub.avg_price, fb.avg_price) AS avg_price
    FROM user_behavior ub
    FULL OUTER JOIN friend_behavior fb ON ub.product_id = fb.product_id
)
SELECT
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
FROM combined_scores
WHERE user_id = 560126337  -- Change user_id for different users, i use 1 user as an example
ORDER BY total_score DESC, total_interactions DESC
LIMIT 20;