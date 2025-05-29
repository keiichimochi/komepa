-- お米商品情報テーブル
CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,                      -- 商品を一意に識別するID (例: "siteA_product123")
    name TEXT NOT NULL,                       -- 商品名
    price INTEGER,                            -- 価格 (円)
    product_url TEXT UNIQUE NOT NULL,         -- 元の商品ページURL
    affiliate_url TEXT,                       -- 生成済みのアフィリエイトリンク
    image_url TEXT,                           -- 商品画像のURL
    site_name TEXT,                           -- 収集元サイト名 (例: "楽天", "Amazon")
    last_scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 最終スクレイピング日時
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 価格でのインデックス
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);

-- 更新日時でのインデックス
CREATE INDEX IF NOT EXISTS idx_products_updated_at ON products(updated_at);

-- サイト名でのインデックス
CREATE INDEX IF NOT EXISTS idx_products_site_name ON products(site_name);