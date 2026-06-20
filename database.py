import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "bot.db")


class Database:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                username TEXT,
                pubg_id TEXT,
                phone TEXT,
                referrer_id INTEGER,
                is_banned INTEGER DEFAULT 0,
                joined_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Eski users jadvalga yangi ustunlar qo'shish (mavjud DB uchun)
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0")
        except Exception:
            pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(referrer_id, referred_id)
            )
        """)

        # referrals jadvalga is_active ustuni qo'shish
        try:
            cursor.execute("ALTER TABLE referrals ADD COLUMN is_active INTEGER DEFAULT 1")
        except Exception:
            pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_username TEXT UNIQUE,
                channel_name TEXT,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # channels jadvalga channel_name ustuni qo'shish
        try:
            cursor.execute("ALTER TABLE channels ADD COLUMN channel_name TEXT")
        except Exception:
            pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gifts (
                place INTEGER PRIMARY KEY,
                gift_name TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('gift_top_limit', '10')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('stat_top_limit', '20')")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS winners (
                place INTEGER,
                user_id INTEGER,
                full_name TEXT,
                username TEXT,
                pubg_id TEXT,
                ref_count INTEGER,
                gift_name TEXT,
                marked_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()

    # ========== USERS ==========

    def add_user(self, user_id, full_name, username, pubg_id, referrer_id=None):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO users (user_id, full_name, username, pubg_id, referrer_id, joined_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, full_name, username, pubg_id, referrer_id, datetime.now().isoformat()))
        self.conn.commit()

    def update_phone(self, user_id, phone):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET phone = ? WHERE user_id = ?", (phone, user_id))
        self.conn.commit()

    def get_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return cursor.fetchone()

    def get_user_by_username(self, username):
        username = username.lstrip("@")
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username,))
        return cursor.fetchone()

    def get_user_by_pubg_id(self, pubg_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE pubg_id = ?", (pubg_id,))
        return cursor.fetchone()

    def get_user_by_phone(self, phone):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE phone = ?", (phone,))
        return cursor.fetchone()

    def ban_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))
        self.conn.commit()

    def unban_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,))
        self.conn.commit()

    def is_banned(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return bool(result and result[0])

    def get_total_users(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        return cursor.fetchone()[0]

    def get_all_user_ids(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE is_banned = 0")
        return [row[0] for row in cursor.fetchall()]

    def get_all_users_with_phones(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id, full_name, username, pubg_id, phone FROM users ORDER BY joined_at DESC")
        return cursor.fetchall()

    def get_top_users(self, limit=20):
        """Faqat 24 soatdan o'tgan, faol referali bor odamlarni qaytaradi"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT u.user_id, u.full_name, u.username, u.pubg_id,
                   COUNT(r.id) as ref_count
            FROM users u
            INNER JOIN referrals r ON r.referrer_id = u.user_id AND r.is_active = 1
                AND datetime(r.created_at) <= datetime('now', '-1 day')
            GROUP BY u.user_id
            HAVING ref_count > 0
            ORDER BY ref_count DESC
            LIMIT ?
        """, (limit,))
        return cursor.fetchall()

    def get_stat_top_limit(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = 'stat_top_limit'")
        result = cursor.fetchone()
        return int(result[0]) if result else 20

    def set_stat_top_limit(self, limit):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('stat_top_limit', ?)", (str(limit),))
        self.conn.commit()

    def get_user_rank(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT rank FROM (
                SELECT user_id, ROW_NUMBER() OVER (ORDER BY COUNT(r.id) DESC) as rank
                FROM users u
                LEFT JOIN referrals r ON r.referrer_id = u.user_id AND r.is_active = 1
                    AND datetime(r.created_at) <= datetime('now', '-1 day')
                GROUP BY u.user_id
            ) WHERE user_id = ?
        """, (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 0

    # ========== REFERRALS ==========

    def add_referral(self, referrer_id, referred_id):
        cursor = self.conn.cursor()
        try:
            # Avval mavjudligini tekshir
            cursor.execute("SELECT id, is_active FROM referrals WHERE referrer_id = ? AND referred_id = ?",
                           (referrer_id, referred_id))
            existing = cursor.fetchone()
            if existing:
                # Mavjud bo'lsa, active qilish
                cursor.execute("UPDATE referrals SET is_active = 1 WHERE referrer_id = ? AND referred_id = ?",
                               (referrer_id, referred_id))
            else:
                cursor.execute("""
                    INSERT INTO referrals (referrer_id, referred_id, is_active)
                    VALUES (?, ?, 1)
                """, (referrer_id, referred_id))
            cursor.execute("""
                UPDATE users SET referrer_id = ? WHERE user_id = ? AND referrer_id IS NULL
            """, (referrer_id, referred_id))
            self.conn.commit()
        except Exception as e:
            print(f"add_referral xato: {e}")

    def deactivate_referral(self, referrer_id, referred_id):
        """Referalni o'chirmay, nofaol qiladi (qayta obuna bo'lsa qaytarish uchun)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE referrals SET is_active = 0 WHERE referrer_id = ? AND referred_id = ?
        """, (referrer_id, referred_id))
        self.conn.commit()

    def remove_referral(self, referrer_id, referred_id):
        self.deactivate_referral(referrer_id, referred_id)

    def get_referral_count(self, user_id):
        """Faqat 24 soatdan o'tgan, faol referallarni sanaydi"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM referrals
            WHERE referrer_id = ? AND is_active = 1
            AND datetime(created_at) <= datetime('now', '-1 day')
        """, (user_id,))
        return cursor.fetchone()[0]

    def get_pending_referral_count(self, user_id):
        """24 soat kutish bosqichida turgan referallar soni"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM referrals
            WHERE referrer_id = ? AND is_active = 1
            AND datetime(created_at) > datetime('now', '-1 day')
        """, (user_id,))
        return cursor.fetchone()[0]

    def get_referral_history(self, user_id, limit=50):
        """Kim, qachon taklif qilingani"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT u.full_name, r.created_at, r.is_active,
                   (datetime(r.created_at) <= datetime('now', '-1 day')) as confirmed
            FROM referrals r
            JOIN users u ON u.user_id = r.referred_id
            WHERE r.referrer_id = ?
            ORDER BY r.created_at DESC
            LIMIT ?
        """, (user_id, limit))
        return cursor.fetchall()

    def get_referrer_of(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT referrer_id FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None

    def get_total_referrals(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM referrals WHERE is_active = 1")
        return cursor.fetchone()[0]

    # ========== CHANNELS ==========

    def add_channel(self, channel_username, channel_name):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO channels (channel_username, channel_name) VALUES (?, ?)
        """, (channel_username, channel_name))
        self.conn.commit()

    def remove_channel(self, channel_username):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM channels WHERE channel_username = ?", (channel_username,))
        self.conn.commit()

    def get_channels(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT channel_username FROM channels")
        return [row[0] for row in cursor.fetchall()]

    def get_channels_with_names(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT channel_username, channel_name FROM channels")
        return cursor.fetchall()

    # ========== GIFTS ==========

    def set_gift(self, place, gift_name):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO gifts (place, gift_name, updated_at)
            VALUES (?, ?, ?)
        """, (place, gift_name, datetime.now().isoformat()))
        self.conn.commit()

    def remove_gift(self, place):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM gifts WHERE place = ?", (place,))
        self.conn.commit()

    def get_gifts(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT place, gift_name FROM gifts ORDER BY place ASC")
        return cursor.fetchall()

    def get_gift_top_limit(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = 'gift_top_limit'")
        result = cursor.fetchone()
        return int(result[0]) if result else 10

    def set_gift_top_limit(self, limit):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('gift_top_limit', ?)", (str(limit),))
        self.conn.commit()

    def set_contest_end_date(self, date_text):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('contest_end_date', ?)", (date_text,))
        self.conn.commit()

    def get_contest_end_date(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = 'contest_end_date'")
        result = cursor.fetchone()
        return result[0] if result else None

    def reset_contest(self):
        """Konkursni tugatadi: barcha referallar o'chiriladi, users.referrer_id NULL qilinadi"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM referrals")
        cursor.execute("UPDATE users SET referrer_id = NULL")
        cursor.execute("DELETE FROM gifts")
        cursor.execute("DELETE FROM settings WHERE key = 'contest_end_date'")
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('gift_top_limit', '10')")
        self.conn.commit()

    # ========== WINNERS ==========

    def mark_winners(self):
        """Joriy Top N ni g'oliblar sifatida saqlaydi (sovgalar bilan)"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM winners")
        gifts = dict(self.get_gifts())
        top_limit = self.get_gift_top_limit()
        top_users = self.get_top_users(top_limit)
        for i, (uid, name, uname, pubg_id, ref_count) in enumerate(top_users, 1):
            gift_name = gifts.get(i, "—")
            cursor.execute("""
                INSERT INTO winners (place, user_id, full_name, username, pubg_id, ref_count, gift_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (i, uid, name, uname, pubg_id, ref_count, gift_name))
        self.conn.commit()
        return len(top_users)

    def get_winners(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT place, full_name, username, pubg_id, ref_count, gift_name FROM winners ORDER BY place ASC")
        return cursor.fetchall()
