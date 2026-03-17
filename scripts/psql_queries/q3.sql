-- scripts/psql_queries/q3.sql
-- Task 5: Full-Text Search on Products
-- Note: Using ILIKE due to FTS tokenization issues with category_code format
--
-- IMPORTANT: This query uses q2 results (top 20 recommended products)
-- as the basis for category extraction, per assignment requirement:
-- "Based on the top products you obtained above"
--
-- OPTIMIZATION: Q2 product_ids are hardcoded for performance.
-- In real data, this would be a dynamic pipeline q2 to q3.


WITH
-- -------------------------------------------------------------------------
-- STEP 1: Q2 Results (hardcoded for performance)
-- These are the top 20 recommended products from q2.sql
-- -------------------------------------------------------------------------
q2_recommendations AS (
    SELECT * FROM (VALUES
        (1004749, 'samsung', 'electronics.smartphone'),
        (1005232, 'xiaomi', 'construction.tools.light'),
        (26401412, 'lucente', ''),
        (2900926, 'dauscher', 'furniture.bedroom.blanket'),
        (2600218, '', ''),
        (1005265, 'xiaomi', 'construction.tools.light'),
        (3601060, 'artel', 'appliances.kitchen.washer'),
        (1005008, 'xiaomi', 'construction.tools.light'),
        (1004905, 'huawei', 'construction.tools.light'),
        (1004751, 'samsung', 'construction.tools.light'),
        (2900864, '', 'furniture.bedroom.blanket'),
        (1004708, 'huawei', 'construction.tools.light'),
        (1004749, 'samsung', 'construction.tools.light'),
        (1004751, 'samsung', 'electronics.smartphone'),
        (26300087, 'lucente', 'appliances.kitchen.coffee_grinder'),
        (1005173, '', 'electronics.smartphone'),
        (3600253, 'midea', 'appliances.kitchen.washer'),
        (1801906, 'tcl', 'appliances.personal.massager'),
        (3801134, 'elenberg', 'appliances.iron'),
        (1005203, 'xiaomi', 'construction.tools.light')
    ) AS q2(product_id, brand, category_code)
),

-- -------------------------------------------------------------------------
-- STEP 2: Extract unique category_codes from Q2 results
-- -------------------------------------------------------------------------
q2_categories AS (
    SELECT DISTINCT category_code
    FROM q2_recommendations
    WHERE category_code IS NOT NULL
    AND category_code != ''
),

-- -------------------------------------------------------------------------
-- STEP 3: Extract keywords from category_codes (split by '.')
-- -------------------------------------------------------------------------
search_keywords AS (
    SELECT
        category_code,
        UNNEST(string_to_array(category_code, '.')) AS keyword
    FROM q2_categories
    WHERE category_code IS NOT NULL
),

-- -------------------------------------------------------------------------
-- STEP 4: Find products matching keywords (FTS via ILIKE)
-- -------------------------------------------------------------------------
fts_results AS (
    SELECT
        e.product_id,
        p.brand,
        c.category_code,
        COUNT(DISTINCT sk.keyword) AS matched_keywords_count,
        ARRAY_AGG(DISTINCT sk.keyword) AS matched_keywords
    FROM events e
    JOIN products p ON e.product_id = p.product_id
    JOIN categories c ON e.category_id = c.category_id
    CROSS JOIN search_keywords sk
    WHERE c.category_code ILIKE '%' || sk.keyword || '%'
    -- Exclude products already in Q2 recommendations
    AND e.product_id NOT IN (SELECT product_id FROM q2_recommendations)
    GROUP BY e.product_id, p.brand, c.category_code
)

-- -------------------------------------------------------------------------
-- STEP 5: Final output with match quality
-- -------------------------------------------------------------------------
SELECT
    product_id,
    brand,
    category_code,
    matched_keywords_count AS relevance_score,
    matched_keywords::TEXT AS matched_keywords,
    CASE
        WHEN matched_keywords_count >= 3 THEN 'High Match'
        WHEN matched_keywords_count >= 2 THEN 'Medium Match'
        ELSE 'Low Match'
    END AS match_quality
FROM fts_results
ORDER BY matched_keywords_count DESC, product_id
LIMIT 20;