// scripts/neo4j_queries/q3.cypher
// Task 5: Full-Text Search on Products
// Based on Q2 results (top 20 recommended products)
// Parameter: $user_id (for consistency, though not used in hardcoded version)

// STEP 1: Q2 Results (hardcoded product_ids and category_codes)
WITH [
    {product_id: 1004749, category_code: 'electronics.smartphone'},
    {product_id: 1005232, category_code: 'construction.tools.light'},
    {product_id: 26401412, category_code: 'auto.accessories.compressor'},
    {product_id: 2900926, category_code: 'furniture.bedroom.blanket'},
    {product_id: 2600218, category_code: ''},
    {product_id: 1005265, category_code: 'construction.tools.light'},
    {product_id: 3601060, category_code: 'appliances.kitchen.washer'},
    {product_id: 1005008, category_code: 'construction.tools.light'},
    {product_id: 1004905, category_code: 'construction.tools.light'},
    {product_id: 1004751, category_code: 'construction.tools.light'},
    {product_id: 2900864, category_code: 'furniture.bedroom.blanket'},
    {product_id: 1004708, category_code: 'construction.tools.light'},
    {product_id: 1004749, category_code: 'construction.tools.light'},
    {product_id: 1004751, category_code: 'electronics.smartphone'},
    {product_id: 26300087, category_code: 'appliances.kitchen.coffee_grinder'},
    {product_id: 1005173, category_code: 'electronics.smartphone'},
    {product_id: 3600253, category_code: 'appliances.kitchen.washer'},
    {product_id: 1801906, category_code: 'appliances.personal.massager'},
    {product_id: 3801134, category_code: 'appliances.iron'},
    {product_id: 1005203, category_code: 'construction.tools.light'}
] AS q2_products

// STEP 2: Extract Q2 product_ids (to exclude from results)
WITH
    q2_products,
    [p IN q2_products | p.product_id] AS q2_product_ids,
    [p IN q2_products WHERE p.category_code IS NOT NULL AND p.category_code <> '' | p.category_code] AS q2_categories

// STEP 3: Extract keywords from category_codes (split by '.')
WITH
    q2_products,
    q2_product_ids,
    REDUCE(keywords = [], cat IN q2_categories | keywords + SPLIT(cat, '.')) AS keywords_nested

// Flatten keywords list
WITH
    q2_product_ids,
    REDUCE(unique_keywords = [], k IN keywords_nested |
        CASE WHEN k IN unique_keywords THEN unique_keywords ELSE unique_keywords + k END
    ) AS all_keywords

// STEP 4: Find products matching keywords (excluding Q2 products)
MATCH (product:Product)
WHERE NOT product.product_id IN q2_product_ids
MATCH (product)-[:PRODUCT_BELONG_TO_CATEGORY]->(category:Category)
WHERE category.category_code IS NOT NULL

// Split category_code and count matching keywords
WITH
    product,
    category,
    SPLIT(category.category_code, '.') AS category_parts,
    all_keywords,
    q2_product_ids

// Count how many keywords match
WITH
    product,
    category,
    [k IN category_parts WHERE k IN all_keywords] AS matched_keywords,
    q2_product_ids

WHERE SIZE(matched_keywords) > 0

// STEP 5: Return results with match quality
WITH
    product.product_id AS product_id,
    product.brand AS brand,
    category.category_code AS category_code,
    SIZE(matched_keywords) AS relevance_score,
    matched_keywords,
    q2_product_ids

RETURN
    product_id,
    brand,
    category_code,
    relevance_score,
    matched_keywords,
    CASE
        WHEN relevance_score >= 3 THEN 'High Match'
        WHEN relevance_score >= 2 THEN 'Medium Match'
        ELSE 'Low Match'
    END AS match_quality
ORDER BY relevance_score DESC, product_id ASC
LIMIT 20;