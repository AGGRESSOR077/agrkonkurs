"""
Telegram Web App uchun API server.
Bot bilan bir vaqtda ishga tushiriladi (alohida processda yoki thread'da).
"""
import hashlib
import hmac
import json
from urllib.parse import parse_qsl, unquote

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from database import Database

BOT_TOKEN = "8935442087:AAEkbThT6uMQQqW_LkiK6P0PV5q4QuxlV0o"
ADMIN_ID = 7808709581

app = Flask(__name__, static_folder="static")
CORS(app)
db = Database()


# ===================== TELEGRAM INIT DATA VALIDATSIYASI =====================

def validate_init_data(init_data: str) -> dict | None:
    """Telegram Web App initData ni tekshiradi va foydalanuvchi ma'lumotini qaytaradi"""
    try:
        parsed = dict(parse_qsl(init_data))
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            return None

        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if calculated_hash != received_hash:
            return None

        user_json = parsed.get("user")
        if not user_json:
            return None
        return json.loads(unquote(user_json))
    except Exception:
        return None


def get_user_from_request():
    """Request headerdan foydalanuvchini oladi va tekshiradi"""
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    user = validate_init_data(init_data)
    return user


# ===================== STATIC FILES (Web App frontend) =====================

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("static", path)


# ===================== API: FOYDALANUVCHI =====================

@app.route("/api/me", methods=["GET"])
def get_me():
    tg_user = get_user_from_request()
    if not tg_user:
        return jsonify({"error": "unauthorized"}), 401

    user_id = tg_user["id"]
    user = db.get_user(user_id)
    is_admin = user_id == ADMIN_ID

    if not user:
        return jsonify({
            "registered": False,
            "is_admin": is_admin,
            "telegram": {
                "id": user_id,
                "first_name": tg_user.get("first_name", ""),
                "username": tg_user.get("username", "")
            }
        })

    uid, name, uname, pubg_id, phone, ref_id, banned, joined = user
    count = db.get_referral_count(user_id)
    pending = db.get_pending_referral_count(user_id)
    rank = db.get_user_rank(user_id)
    gift_limit = db.get_gift_top_limit()

    return jsonify({
        "registered": True,
        "is_admin": is_admin,
        "is_banned": bool(banned),
        "user": {
            "id": uid,
            "full_name": name,
            "username": uname,
            "pubg_id": pubg_id,
            "phone": phone,
            "joined_at": joined,
        },
        "stats": {
            "referral_count": count,
            "pending_count": pending,
            "rank": rank if count > 0 else None,
            "gift_limit": gift_limit,
            "in_gift_zone": (rank <= gift_limit) if count > 0 else False,
            "needed_for_gift": max(0, rank - gift_limit) if count > 0 and rank > gift_limit else 0,
        }
    })


@app.route("/api/referral-link", methods=["GET"])
def referral_link():
    tg_user = get_user_from_request()
    if not tg_user:
        return jsonify({"error": "unauthorized"}), 401
    bot_username = "AGGRESSOR_KONKURS_BOT"  # @BotFather dan olingan username (@ siz)
    link = f"https://t.me/{bot_username}?start=ref{tg_user['id']}"
    return jsonify({"link": link})


@app.route("/api/history", methods=["GET"])
def referral_history():
    tg_user = get_user_from_request()
    if not tg_user:
        return jsonify({"error": "unauthorized"}), 401
    history = db.get_referral_history(tg_user["id"], 100)
    result = [
        {"name": name, "date": created_at, "active": bool(is_active), "confirmed": bool(confirmed)}
        for name, created_at, is_active, confirmed in history
    ]
    return jsonify({"history": result})


# ===================== API: STATISTIKA / SOVGALAR =====================

@app.route("/api/leaderboard", methods=["GET"])
def leaderboard():
    limit = db.get_stat_top_limit()
    top_users = db.get_top_users(limit)
    result = [
        {"rank": i, "name": name, "username": uname, "pubg_id": pubg_id, "ref_count": ref_count}
        for i, (uid, name, uname, pubg_id, ref_count) in enumerate(top_users, 1)
    ]
    return jsonify({"leaderboard": result, "limit": limit})


@app.route("/api/gifts", methods=["GET"])
def gifts():
    gift_list = db.get_gifts()
    top_limit = db.get_gift_top_limit()
    end_date = db.get_contest_end_date()
    result = [{"place": place, "name": name} for place, name in gift_list]
    return jsonify({"gifts": result, "top_limit": top_limit, "end_date": end_date})


# ===================== API: ADMIN =====================

def check_admin(tg_user):
    return tg_user and tg_user["id"] == ADMIN_ID


@app.route("/api/admin/stats", methods=["GET"])
def admin_stats():
    tg_user = get_user_from_request()
    if not check_admin(tg_user):
        return jsonify({"error": "forbidden"}), 403
    return jsonify({
        "total_users": db.get_total_users(),
        "total_channels": len(db.get_channels()),
        "total_referrals": db.get_total_referrals(),
        "stat_top_limit": db.get_stat_top_limit(),
        "gift_top_limit": db.get_gift_top_limit(),
    })


@app.route("/api/admin/users", methods=["GET"])
def admin_users():
    tg_user = get_user_from_request()
    if not check_admin(tg_user):
        return jsonify({"error": "forbidden"}), 403
    users = db.get_all_users_with_phones()
    result = []
    for uid, name, uname, pubg_id, phone in users:
        result.append({
            "id": uid, "name": name, "username": uname,
            "pubg_id": pubg_id, "phone": phone,
            "ref_count": db.get_referral_count(uid),
            "banned": db.is_banned(uid),
        })
    return jsonify({"users": result})


@app.route("/api/admin/channels", methods=["GET"])
def admin_channels():
    tg_user = get_user_from_request()
    if not check_admin(tg_user):
        return jsonify({"error": "forbidden"}), 403
    channels = db.get_channels_with_names()
    return jsonify({"channels": [{"username": u, "name": n} for u, n in channels]})


@app.route("/api/admin/channels", methods=["POST"])
def admin_add_channel():
    tg_user = get_user_from_request()
    if not check_admin(tg_user):
        return jsonify({"error": "forbidden"}), 403
    data = request.get_json()
    username = data.get("username", "").strip()
    name = data.get("name", "").strip()
    if not username.startswith("@"):
        username = "@" + username
    db.add_channel(username, name)
    return jsonify({"success": True})


@app.route("/api/admin/channels", methods=["DELETE"])
def admin_remove_channel():
    tg_user = get_user_from_request()
    if not check_admin(tg_user):
        return jsonify({"error": "forbidden"}), 403
    data = request.get_json()
    username = data.get("username", "").strip()
    db.remove_channel(username)
    return jsonify({"success": True})


@app.route("/api/admin/ban", methods=["POST"])
def admin_ban():
    tg_user = get_user_from_request()
    if not check_admin(tg_user):
        return jsonify({"error": "forbidden"}), 403
    data = request.get_json()
    username = data.get("username", "").strip().lstrip("@")
    user = db.get_user_by_username(username)
    if not user:
        return jsonify({"error": "not_found"}), 404
    db.ban_user(user[0])
    return jsonify({"success": True})


@app.route("/api/admin/unban", methods=["POST"])
def admin_unban():
    tg_user = get_user_from_request()
    if not check_admin(tg_user):
        return jsonify({"error": "forbidden"}), 403
    data = request.get_json()
    username = data.get("username", "").strip().lstrip("@")
    user = db.get_user_by_username(username)
    if not user:
        return jsonify({"error": "not_found"}), 404
    db.unban_user(user[0])
    return jsonify({"success": True})


@app.route("/api/admin/gifts", methods=["POST"])
def admin_set_gift():
    tg_user = get_user_from_request()
    if not check_admin(tg_user):
        return jsonify({"error": "forbidden"}), 403
    data = request.get_json()
    place = int(data.get("place"))
    name = data.get("name", "").strip()
    db.set_gift(place, name)
    return jsonify({"success": True})


@app.route("/api/admin/gifts", methods=["DELETE"])
def admin_remove_gift():
    tg_user = get_user_from_request()
    if not check_admin(tg_user):
        return jsonify({"error": "forbidden"}), 403
    data = request.get_json()
    place = int(data.get("place"))
    db.remove_gift(place)
    return jsonify({"success": True})


@app.route("/api/admin/settings", methods=["POST"])
def admin_settings():
    tg_user = get_user_from_request()
    if not check_admin(tg_user):
        return jsonify({"error": "forbidden"}), 403
    data = request.get_json()
    if "gift_top_limit" in data:
        db.set_gift_top_limit(int(data["gift_top_limit"]))
    if "stat_top_limit" in data:
        db.set_stat_top_limit(int(data["stat_top_limit"]))
    if "contest_end_date" in data:
        db.set_contest_end_date(data["contest_end_date"])
    return jsonify({"success": True})


@app.route("/api/admin/winners", methods=["GET"])
def admin_get_winners():
    tg_user = get_user_from_request()
    if not check_admin(tg_user):
        return jsonify({"error": "forbidden"}), 403
    winners = db.get_winners()
    result = [
        {"place": p, "name": n, "username": u, "pubg_id": pid, "ref_count": rc, "gift_name": g}
        for p, n, u, pid, rc, g in winners
    ]
    return jsonify({"winners": result})


@app.route("/api/admin/winners", methods=["POST"])
def admin_mark_winners():
    tg_user = get_user_from_request()
    if not check_admin(tg_user):
        return jsonify({"error": "forbidden"}), 403
    count = db.mark_winners()
    return jsonify({"success": True, "count": count})


@app.route("/api/admin/reset-contest", methods=["POST"])
def admin_reset_contest():
    tg_user = get_user_from_request()
    if not check_admin(tg_user):
        return jsonify({"error": "forbidden"}), 403
    db.reset_contest()
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
