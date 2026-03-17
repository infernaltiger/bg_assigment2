-- scripts/psql_queries/q1.sql
-- Task 3: Campaign Effectiveness Analysis (Social Network)
-- Find campaigns that attracted customers to purchase products via social network

-- Approach:
-- 1. Find users who received messages from campaigns
-- 2. Check if they purchased after receiving message
-- 3. Rank campaigns by total purchase conversion rate


WITH campaign_stats AS (
    -- Group messages by campaign and calculate conversion
    SELECT
        c.campaign_id AS original_campaign_id,
        c.campaign_type,
        c.channel,
        COUNT(DISTINCT m.user_id) AS message_recipients,
        COUNT(DISTINCT CASE WHEN m.is_purchased = TRUE THEN m.user_id END) AS purchases,
        ROUND(100.0 * COUNT(DISTINCT CASE WHEN m.is_purchased = TRUE THEN m.user_id END) /
              NULLIF(COUNT(DISTINCT m.user_id), 0), 2) AS conversion_rate
    FROM messages m
    JOIN campaigns c ON m.campaign_id = c.id
    GROUP BY c.campaign_id, c.campaign_type, c.channel
)
SELECT
    original_campaign_id,
    campaign_type,
    channel,
    message_recipients,
    purchases,
    conversion_rate
FROM campaign_stats
WHERE message_recipients > 0
ORDER BY purchases DESC
LIMIT 20;