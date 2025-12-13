import mysql.connector
from mysql.connector import Error

# تنظیمات دیتابیس (همون که در کدت داری)
config = {
    'host': 'localhost',
    'user': 'pythonuser',
    'password': '135101220',
    'database': 'comments_db',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'autocommit': True,
    'raise_on_warnings': True
}

def create_all_tables_if_not_exist():
    """تمام جدول‌های مورد نیاز پروژه را در صورت عدم وجود، ایجاد می‌کند"""
    conn = None
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        print("در حال بررسی و ایجاد جدول‌های مورد نیاز...")

        # 1. جدول comments
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                coin_name VARCHAR(50) NOT NULL,
                username VARCHAR(50) NOT NULL,
                comment TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_coin (coin_name),
                INDEX idx_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        print("✓ جدول comments بررسی/ایجاد شد")

        # 2. جدول coin_descriptions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS coin_descriptions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                coin_id VARCHAR(100) UNIQUE NOT NULL,
                english_description LONGTEXT,
                persian_description LONGTEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        print("✓ جدول coin_descriptions بررسی/ایجاد شد")

        # 3. جدول dollar_price
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dollar_price (
                id INT AUTO_INCREMENT PRIMARY KEY,
                price_rial BIGINT NOT NULL DEFAULT 0,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_updated_at (updated_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        print("✓ جدول dollar_price بررسی/ایجاد شد")

        # درج یک رکورد اولیه اگر جدول خالی بود
        cursor.execute("SELECT COUNT(*) FROM dollar_price")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO dollar_price (price_rial, updated_at) 
                VALUES (0, '2000-01-01 00:00:00')
            """)
            print("  → رکورد اولیه در dollar_price اضافه شد")

        # 4. جدول btc_predictions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS btc_predictions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                current_price DECIMAL(20,8) NOT NULL,
                predicted_price_10min DECIMAL(20,8) NOT NULL,
                change_percent DECIMAL(10,4) NOT NULL,
                direction ENUM('UP', 'DOWN') NOT NULL,
                strength ENUM('STRONG', 'WEAK', 'NEUTRAL') NOT NULL,
                features_used JSON,
                prediction_time DATETIME NOT NULL,
                timestamp_local TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_prediction_time (prediction_time DESC)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        print("✓ جدول btc_predictions بررسی/ایجاد شد")

        # 5. جدول coin_votes (برای نظرسنجی bullish/bearish)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS coin_votes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                coin VARCHAR(50) NOT NULL,
                vote_type ENUM('bullish', 'bearish') NOT NULL,
                user_ip VARCHAR(45),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_coin (coin),
                INDEX idx_vote_type (vote_type)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        print("✓ جدول coin_votes بررسی/ایجاد شد")

        conn.commit()
        print("\nتمام جدول‌ها با موفقیت بررسی و در صورت نیاز ایجاد شدند.")

    except Error as e:
        print(f"خطا در اتصال یا اجرای کوئری MySQL: {e}")
    except Exception as e:
        print(f"خطای غیرمنتظره: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


# اجرای تابع (می‌تونی این بخش رو کامنت کنی اگر فقط به عنوان ماژول استفاده می‌کنی)
if __name__ == "__main__":
    create_all_tables_if_not_exist()




""" 
# حذف تمام جدول های دیتابیس

import mysql.connector
from mysql.connector import Error

config = {
    'host': 'localhost',
    'user': 'pythonuser',
    'password': '135101220',
    'database': 'comments_db',
    'charset': 'utf8mb4',
    'autocommit': True,
    'raise_on_warnings': True
}

try:
    # اتصال به دیتابیس
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()

    # غیرفعال کردن بررسی foreign key برای جلوگیری از خطا
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

    # گرفتن لیست تمام جداول
    cursor.execute("SHOW TABLES;")
    tables = cursor.fetchall()

    # حذف هر جدول
    for table in tables:
        table_name = table[0]
        print(f"در حال حذف جدول: {table_name}")
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")

    # فعال کردن دوباره بررسی foreign key
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    print("تمام جداول با موفقیت حذف شدند.")

except Error as e:
    print(f"خطا در اتصال یا اجرای دستورات: {e}")

finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("اتصال به دیتابیس بسته شد.") 
"""