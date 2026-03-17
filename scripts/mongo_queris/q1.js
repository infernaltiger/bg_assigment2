// scripts/q1.js
// Task 3: Campaign Effectiveness Analysis
// Find campaigns that attracted customers to purchase products

//I assume that this script is run in shell by ''mongosh --file''
// Thats why i added printing the results
//You also can copy the pipeline directly and run it in mongodb compass

// Approach:
// 1. Find users who received messages from campaigns
// 2. Check if they purchased after receiving message
// 3. Rank campaigns by total purchase conversion rate

db = db.getSiblingDB('bigdata');

// Define the pipeline
const pipeline = [
    // Stage 1: Match valid messages
    {
        $match: {
            campaign_id: { $exists: true },
            user_id: { $exists: true },
            "campaign_data.id": { $exists: true }
        }
    },

    // Stage 2: Group by user + campaign (deduplicate messages per user)
    {
        $group: {
            _id: {
                campaign_id: "$campaign_data.id",
                user_id: "$user_id"
            },
            campaign_type: { $first: "$campaign_data.campaign_type" },
            channel: { $first: "$campaign_data.channel" },
            purchased: { $max: "$engagement.is_purchased" }
        }
    },

    // Stage 3: Group by campaign only (count unique users)
    {
        $group: {
            _id: {
                campaign_id: "$_id.campaign_id",
                campaign_type: "$campaign_type",
                channel: "$channel"
            },
            message_recipients: { $sum: 1 },
            purchases: { $sum: { $cond: ["$purchased", 1, 0] } }
        }
    },

    // Stage 4: Calculate stats
    {
        $project: {
        _id: 0,
        original_campaign_id: "$_id.campaign_id",
        campaign_type: "$_id.campaign_type",
        channel: "$_id.channel",
        message_recipients: "$message_recipients",
        purchases: "$purchases",
        conversion_rate: {
            $round: [
                {
                    $multiply: [
                        { $divide: ["$purchases", "$message_recipients"] },
                        100
                    ]
                },
                2
            ]
        }
    }
    },

    // Stage 5: Filter and sort
    {
        $match: { message_recipients: { $gt: 0 } }
    },
    {
        $sort: { purchases: -1 }
    },
    {
        $limit: 20
    }
];

// Execute and store results
const results = db.messages.aggregate(pipeline, { allowDiskUse: true });

// Print header
print("\n" + "=".repeat(80));
print(" Task 3: Campaign Effectiveness Analysis");
print("=".repeat(80) + "\n");

// Print results
print("Top 20 Campaigns by Purchases:\n");
print(JSON.stringify(results.toArray(), null, 2));

// Print summary
print("\n" + "=".repeat(80));
print(" Query completed successfully!");
print("=".repeat(80) + "\n");