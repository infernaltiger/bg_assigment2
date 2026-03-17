// scripts/mongo_queries/q3.js
// Task 5: Full-Text Search on Products
// Find products by keywords from category_code
//
// IMPORTANT: This query uses Q2 results (top 20 recommended products)
// as the basis for category extraction, per assignment requirement:
// "Based on the top products you obtained above"
//
// OPTIMIZATION: Q2 product_ids and categories are hardcoded for performance.
// These values are from MongoDB q2.js results (denormalized schema, that's why the have a slight difference).

db = db.getSiblingDB('bigdata');


const TARGET_USER_ID = 560126337;

// Q2 Results - Product IDs (hardcoded from q2.js output)
const Q2_PRODUCT_IDS = [
    1004749, 1005232, 26401412, 2900926, 2600218,
    1005265, 3601060, 1005008, 1004905, 1004751,
    2900864, 1004708, 1004749, 1004751, 26300087,
    1005173, 3600253, 1801906, 3801134, 1005203
];

// Q2 Categories (extracted from MongoDB q2.js results - denormalized)
// Note: MongoDB has more complete category data than PostgreSQL
const Q2_CATEGORIES = [
    'electronics.smartphone',
    'construction.tools.light',
    'auto.accessories.compressor', // MongoDB has this (psql dont - because i tried to normilize data for psql or due to my mistake in loading code)
    'furniture.bedroom.blanket',
    'appliances.kitchen.washer',
    'appliances.kitchen.coffee_grinder',
    'appliances.personal.massager',
    'appliances.iron'
];

// =============================================================================
// QUERY PIPELINE
// =============================================================================

const pipeline = [
    // Stage 1: Create keywords array from Q2 categories
    {
        $addFields: {
            q2_categories: Q2_CATEGORIES,
            q2_product_ids: Q2_PRODUCT_IDS
        }
    },
    {
        $unwind: "$q2_categories"
    },
    {
        $addFields: {
            category_parts: { $split: ["$q2_categories", "."] }
        }
    },
    {
        $unwind: "$category_parts"
    },
    {
        $group: {
            _id: null,
            keywords: { $addToSet: "$category_parts" },
            q2_product_ids: { $first: "$q2_product_ids" }
        }
    },

    // Stage 2: Lookup products matching keywords
    {
        $lookup: {
            from: "events",
            let: {
                keywords: "$keywords",
                q2_ids: "$q2_product_ids"
            },
            pipeline: [
                {
                    $match: {
                        $expr: {
                            $and: [
                                { $ne: ["$category_code", null] },
                                { $ne: ["$category_code", ""] }
                            ]
                        }
                    }
                },
                {
                    $addFields: {
                        category_parts: { $split: ["$category_code", "."] }
                    }
                },
                {
                    $unwind: "$category_parts"
                },
                {
                    $match: {
                        $expr: {
                            $in: ["$category_parts", "$$keywords"]
                        }
                    }
                },
                {
                    $group: {
                        _id: {
                            product_id: "$product_id",
                            brand: "$brand",
                            category_code: "$category_code"
                        },
                        matched_keywords: { $addToSet: "$category_parts" }
                    }
                },
                {
                    $match: {
                        $expr: {
                            $not: { $in: ["$_id.product_id", "$$q2_ids"] }
                        }
                    }
                }
            ],
            as: "product_matches"
        }
    },
    { $unwind: "$product_matches" },

    // Stage 3: Calculate relevance score
    {
        $project: {
            _id: 0,
            product_id: "$product_matches._id.product_id",
            brand: "$product_matches._id.brand",
            category_code: "$product_matches._id.category_code",
            matched_keywords: "$product_matches.matched_keywords",
            relevance_score: { $size: "$product_matches.matched_keywords" }
        }
    },

    // Stage 4: Add match quality
    {
        $addFields: {
            match_quality: {
                $switch: {
                    branches: [
                        { case: { $gte: ["$relevance_score", 3] }, then: "High Match" },
                        { case: { $gte: ["$relevance_score", 2] }, then: "Medium Match" }
                    ],
                    default: "Low Match"
                }
            }
        }
    },

    // Stage 5: Sort and limit
    {
        $sort: { relevance_score: -1, product_id: 1 }
    },
    {
        $limit: 20
    },

    // Stage 6: Final projection
    {
        $project: {
            product_id: 1,
            brand: 1,
            category_code: 1,
            relevance_score: 1,
            matched_keywords: 1,
            match_quality: 1
        }
    }
];

// =============================================================================
// EXECUTE AND PRINT RESULTS
// =============================================================================

print("\n" + "=".repeat(80));
print(" Task 5: Full-Text Search on Products");
print("=".repeat(80) + "\n");

print("Database: " + db.getName());
print("Target User ID: " + TARGET_USER_ID);
print("Q2 Products excluded: " + Q2_PRODUCT_IDS.length);
print("Q2 Categories used: " + Q2_CATEGORIES.length);
print("Q2 Categories: " + Q2_CATEGORIES.join(", ") + "\n");

const results = db.events.aggregate(pipeline, { allowDiskUse: true }).toArray();

print("Top 20 Products by Keyword Match (excluding Q2 products):\n");

if (results.length === 0) {
    print("⚠ WARNING: No matching products found!");
} else {
    printjson(results);
}

print("\n" + "=".repeat(80));
print(" Summary Statistics");
print("=".repeat(80));
print("Total products found: " + results.length);

if (results.length > 0) {
    const avgScore = results.reduce((sum, r) => sum + r.relevance_score, 0) / results.length;
    const highCount = results.filter(r => r.match_quality === "High Match").length;
    const medCount = results.filter(r => r.match_quality === "Medium Match").length;
    const lowCount = results.filter(r => r.match_quality === "Low Match").length;

    print("Average relevance score: " + avgScore.toFixed(2));
    print("High Match: " + highCount);
    print("Medium Match: " + medCount);
    print("Low Match: " + lowCount);
}

print("\n" + "=".repeat(80));
print(" Query completed successfully!");
print("=".repeat(80) + "\n");