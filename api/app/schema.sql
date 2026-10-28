CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS cardmembers (
    id        text PRIMARY KEY,
    full_name text NOT NULL,
    email     text NOT NULL
);

CREATE TABLE IF NOT EXISTS cards (
    id            text PRIMARY KEY,
    cardmember_id text NOT NULL REFERENCES cardmembers (id),
    last4         text NOT NULL,
    product_tier  text NOT NULL,
    issued_by     text NOT NULL CHECK (issued_by IN ('network', 'partner_bank')),
    market        text NOT NULL,
    kind          text NOT NULL CHECK (kind IN ('credit', 'prepaid')),
    segment       text NOT NULL
);

CREATE TABLE IF NOT EXISTS agents (
    id            text PRIMARY KEY,
    name          text NOT NULL,
    developer     text NOT NULL,
    registered    boolean NOT NULL,
    registered_at timestamptz,
    suspended_at  timestamptz
);

CREATE TABLE IF NOT EXISTS enablements (
    card_id    text REFERENCES cards (id),
    agent_id   text REFERENCES agents (id),
    enabled_at timestamptz NOT NULL,
    PRIMARY KEY (card_id, agent_id)
);

CREATE TABLE IF NOT EXISTS merchants (
    id                    text PRIMARY KEY,
    name                  text NOT NULL,
    kind                  text NOT NULL CHECK (kind IN ('direct', 'facilitator')),
    aliases               text[] NOT NULL DEFAULT '{}',
    mcc                   text NOT NULL,
    sku_prefix            text NOT NULL,
    returnable            boolean NOT NULL,
    return_window_days    int NOT NULL,
    restocking_fee_pct    int NOT NULL,
    return_shipping_cents int NOT NULL,
    return_note           text NOT NULL
);

CREATE TABLE IF NOT EXISTS intents (
    id               text PRIMARY KEY,
    card_id          text NOT NULL REFERENCES cards (id),
    agent_id         text NOT NULL REFERENCES agents (id),
    instruction      text NOT NULL,
    max_amount_cents int,
    authenticated_at timestamptz NOT NULL,
    auth_method      text NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    id           text PRIMARY KEY,
    card_id      text NOT NULL REFERENCES cards (id),
    descriptor   text NOT NULL,
    amount_cents int NOT NULL CHECK (amount_cents > 0),
    currency     text NOT NULL,
    posted_at    timestamptz NOT NULL,
    agent_id     text REFERENCES agents (id),
    intent_id    text REFERENCES intents (id),
    merchant_id  text NOT NULL REFERENCES merchants (id),
    mcc          text NOT NULL
);
CREATE INDEX IF NOT EXISTS transactions_card_posted ON transactions (card_id, posted_at);

CREATE TABLE IF NOT EXISTS cart_lines (
    transaction_id   text REFERENCES transactions (id),
    line_no          int,
    sku              text NOT NULL,
    title            text NOT NULL,
    attributes       jsonb NOT NULL DEFAULT '{}',
    qty              int NOT NULL CHECK (qty > 0),
    unit_price_cents int NOT NULL,
    merchant_note    text,
    PRIMARY KEY (transaction_id, line_no)
);

CREATE TABLE IF NOT EXISTS returns (
    transaction_id             text PRIMARY KEY REFERENCES transactions (id),
    status                     text NOT NULL CHECK (status IN ('initiated', 'received', 'refunded')),
    initiated_at               timestamptz NOT NULL,
    refunded_cents             int NOT NULL DEFAULT 0,
    return_shipping_paid_cents int NOT NULL DEFAULT 0
);
