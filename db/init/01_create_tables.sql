CREATE TABLE IF NOT EXISTS products (
    id BIGSERIAL PRIMARY KEY,

    source_url TEXT NOT NULL UNIQUE,
    title VARCHAR(500),
    source VARCHAR(100) DEFAULT 'rozetka',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS reviews (
    id BIGSERIAL PRIMARY KEY,

    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,

    external_id VARCHAR(255),
    author VARCHAR(255),
    rating NUMERIC(2, 1),

    raw_text TEXT NOT NULL,
    cleaned_text TEXT,
    language VARCHAR(20),

    content_hash CHAR(64),
    review_date TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_review_product_external_id UNIQUE (product_id, external_id),
    CONSTRAINT uq_review_product_content_hash UNIQUE (product_id, content_hash)
);


CREATE TABLE IF NOT EXISTS review_analyses (
    id BIGSERIAL PRIMARY KEY,

    review_id BIGINT NOT NULL UNIQUE REFERENCES reviews(id) ON DELETE CASCADE,

    helpfulness_score INTEGER,
    specificity_score INTEGER,
    usage_experience_score INTEGER,
    pros_cons_balance_score INTEGER,
    decision_support_score INTEGER,

    fake_probability NUMERIC(5, 4),
    category VARCHAR(100),

    raw_llm_response JSONB,

    analyzed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);