-- scripts/hybrid_model/create_hybrid_db.sql
-- Hybrid Model: PostgreSQL Schema (Core Reference Data)

-- =============================================================================
-- 1. CREATE DATABASE
-- =============================================================================

-- Run separately: CREATE DATABASE bigdata_hybrid;

-- =============================================================================
-- 2. CORE TABLES (Reference Data)
-- =============================================================================

-- Users (core profile data only)
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Products (reference data)
CREATE TABLE IF NOT EXISTS products (
    product_id BIGINT PRIMARY KEY,
    brand VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categories (reference data)
CREATE TABLE IF NOT EXISTS categories (
    category_id BIGINT PRIMARY KEY,
    category_code VARCHAR(500),
    parent_category_id BIGINT REFERENCES categories(category_id)
);

-- Campaigns (reference data)
CREATE TABLE IF NOT EXISTS campaigns (
    id BIGINT PRIMARY KEY,
    campaign_id BIGINT,
    campaign_type VARCHAR(50),
    channel VARCHAR(50),
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    total_count BIGINT
);

-- =============================================================================
-- 3. INDEXES (For core tables)
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
CREATE INDEX IF NOT EXISTS idx_categories_code ON categories(category_code);
CREATE INDEX IF NOT EXISTS idx_campaigns_type ON campaigns(campaign_type);
CREATE INDEX IF NOT EXISTS idx_campaigns_channel ON campaigns(channel);