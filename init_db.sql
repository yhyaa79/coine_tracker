-- init_db.sql
CREATE DATABASE IF NOT EXISTS comments_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE comments_db;

-- اینجا تمام CREATE TABLE هایی که فرستادی رو بذار
-- من فقط چندتاش رو مثال می‌زنم، بقیه رو هم کپی کن

CREATE TABLE IF NOT EXISTS ai_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    coin_id VARCHAR(50) NOT NULL,
    prediction_type VARCHAR(20) NOT NULL,
    predicted_price DECIMAL(20,8) NOT NULL,
    confidence DECIMAL(5,2) NOT NULL,
    current_price DECIMAL(20,8) NOT NULL,
    prediction_time DATETIME NOT NULL,
    target_time DATETIME NOT NULL,
    model_version VARCHAR(50) DEFAULT 'v1.0',
    additional_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_coin_time (coin_id, prediction_time),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ... بقیه جدول‌ها رو هم همینجا بذار (btc_predictions, coin_descriptions, ...)
-- من همه رو نمی‌نویسم که پیام طولانی نشه، ولی تو همه رو کپی کن