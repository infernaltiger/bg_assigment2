// scripts/neo4j_queries/q1.cypher
// Task 3: Campaign Effectiveness Analysis
// Find campaigns that attracted customers to purchase products

// Approach:
// 1. Find users who received messages from campaigns
// 2. Check if they purchased after receiving message
// 3. Rank campaigns by total purchase conversion rate

MATCH (user:User)-[r:RECIEVED_MESSAGE_ABOUT_CAMPAIGN]->(campaign:Campaign)
WITH
    campaign.campaign_id AS campaign_id,
    campaign.campaign_type AS campaign_type,
    campaign.channel AS channel,
    COUNT(DISTINCT user.user_id) AS message_recipients,
    COUNT(DISTINCT CASE WHEN r.is_purchased = true THEN user.user_id END) AS purchases
WHERE message_recipients > 0
RETURN
    campaign_id,
    campaign_type,
    channel,
    message_recipients,
    purchases,
    ROUND(100.0 * purchases / message_recipients, 2) AS conversion_rate
ORDER BY purchases DESC
LIMIT 20;