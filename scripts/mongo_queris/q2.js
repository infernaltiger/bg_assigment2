// scripts/mongo_queries/q2.js
// Task 4: Personalized Product Recommendations
// Find top products to display on user's home page based on behavior

//I assume that this script is run in shell by ''mongosh --file''
// Thats why i added printing the results
//You also can copy the pipeline directly and run it in mongodb compass

// Approach:
// 1. Analyze user's purchase history (highest weight)
// 2. Analyze user's view/cart history (medium weight)
// 3. Find similar users (via friends or similar behavior)
// 4. Rank products by interaction score

db = db.getSiblingDB('bigdata');


const TARGET_USER_ID = 560126337;  // Change this for different users.  I use the most active user found by sql query 'find_active_user'


const pipeline = [
    // Stage 1: Match user's events
    {
        $match: {
            user_id: TARGET_USER_ID
        }
    },

    // Stage 2: Calculate weighted interaction score per product
    {
        $group: {
            _id: {
                product_id: "$product_id",
                brand: "$brand",
                category_code: "$category_code"
            },
            interaction_score: {
                $sum: {
                    $switch: {
                        branches: [
                            { case: { $eq: ["$event_type", "purchase"] }, then: 3 },
                            { case: { $eq: ["$event_type", "cart"] }, then: 2 },
                            { case: { $eq: ["$event_type", "view"] }, then: 1 }
                        ],
                        default: 0
                    }
                }
            },
            interaction_count: { $sum: 1 },
            avg_price: { $avg: "$price" }
        }
    },

    // Stage 3: Get user's friends
    {
        $lookup: {
            from: "users",
            let: { user_id: TARGET_USER_ID },
            pipeline: [
                {
                    $match: {
                        $expr: { $eq: ["$user_id", "$$user_id"] }
                    }
                },
                {
                    $project: {
                        friends: 1
                    }
                }
            ],
            as: "user_data"
        }
    },
    {
        $unwind: {
            path: "$user_data",
            preserveNullAndEmptyArrays: true
        }
    },

    // Stage 4: Lookup friends' purchase events
    {
        $lookup: {
            from: "events",
            let: {
                friend_ids: "$user_data.friends",
                product_id: "$_id.product_id",
                brand: "$_id.brand",
                category_code: "$_id.category_code"
            },
            pipeline: [
                {
                    $match: {
                        $expr: {
                            $and: [
                                { $in: ["$user_id", "$$friend_ids"] },
                                { $eq: ["$event_type", "purchase"] },
                                { $eq: ["$product_id", "$$product_id"] }
                            ]
                        }
                    }
                },
                {
                    $group: {
                        _id: null,
                        friend_score: { $sum: 2 },
                        friend_count: { $sum: 1 }
                    }
                }
            ],
            as: "friend_stats"
        }
    },
    {
        $unwind: {
            path: "$friend_stats",
            preserveNullAndEmptyArrays: true
        }
    },

    // Stage 5: Calculate total scores
    {
        $project: {
            product_id: "$_id.product_id",
            brand: "$_id.brand",
            category_code: "$_id.category_code",
            user_score: "$interaction_score",
            friend_score: { $ifNull: ["$friend_stats.friend_score", 0] },
            total_score: {
                $add: [
                    "$interaction_score",
                    { $ifNull: ["$friend_stats.friend_score", 0] }
                ]
            },
            total_interactions: {
                $add: [
                    "$interaction_count",
                    { $ifNull: ["$friend_stats.friend_count", 0] }
                ]
            },
            avg_price: { $round: ["$avg_price", 2] }
        }
    },

    // Stage 6: Add recommendation level
    {
        $addFields: {
            recommendation_level: {
                $switch: {
                    branches: [
                        { case: { $gte: ["$total_score", 10] }, then: "High Recommendation" },
                        { case: { $gte: ["$total_score", 5] }, then: "Medium Recommendation" }
                    ],
                    default: "Low Recommendation"
                }
            }
        }
    },

    // Stage 7: Sort and limit
    {
        $sort: { total_score: -1, total_interactions: -1 }
    },
    {
        $limit: 20
    },

    // Stage 8: Final projection
    {
        $project: {
            _id: 0,
            product_id: 1,
            brand: 1,
            category_code: 1,
            total_score: 1,
            total_interactions: 1,
            avg_price: 1,
            recommendation_level: 1
        }
    }
];

print("\n" + "=".repeat(80));
print(" Task 4: Personalized Product Recommendations");
print("=".repeat(80) + "\n");

print("Database: " + db.getName());
print("Target User ID: " + TARGET_USER_ID);
print("Collection: events\n");

const results = db.events.aggregate(pipeline, { allowDiskUse: true }).toArray();

print("Top 20 Recommended Products:\n");

if (results.length === 0) {
    print(" WARNING: No recommendations found!");
    print("Check that:");
    print("  1. User " + TARGET_USER_ID + " has events in the database");
    print("  2. User has friends with purchase events");
} else {
    printjson(results);
}

print("\n" + "=".repeat(80));
print(" Summary Statistics");
print("=".repeat(80));
print("Total recommendations: " + results.length);

if (results.length > 0) {
    const avgScore = results.reduce((sum, r) => sum + r.total_score, 0) / results.length;
    const highCount = results.filter(r => r.recommendation_level === "High Recommendation").length;
    const medCount = results.filter(r => r.recommendation_level === "Medium Recommendation").length;
    const lowCount = results.filter(r => r.recommendation_level === "Low Recommendation").length;

    print("Average total score: " + avgScore.toFixed(2));
    print("High recommendations: " + highCount);
    print("Medium recommendations: " + medCount);
    print("Low recommendations: " + lowCount);
}

print("\n" + "=".repeat(80));
print(" Query completed successfully!");
print("=".repeat(80) + "\n");