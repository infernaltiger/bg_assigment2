-- scripts/find_active_user.sql
-- Find users with most activity (purchases + views + cart)

SELECT
    e.user_id,
    COUNT(*) AS total_events,
    COUNT(CASE WHEN e.event_type = 'purchase' THEN 1 END) AS purchases,
    COUNT(CASE WHEN e.event_type = 'view' THEN 1 END) AS views,
    COUNT(CASE WHEN e.event_type = 'cart' THEN 1 END) AS cart_additions,
    COUNT(DISTINCT e.product_id) AS unique_products
FROM events e
GROUP BY e.user_id
HAVING COUNT(*) >= 10  -- At least 10 events
ORDER BY purchases DESC, total_events DESC
LIMIT 20;