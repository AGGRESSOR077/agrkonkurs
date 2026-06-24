"""
Telegram Web App uchun API server.
Bot bilan bir vaqtda ishga tushiriladi (alohida processda yoki thread'da).
"""
import hashlib
import hmac
import json
from urllib.parse import parse_qsl, unquote

from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from io import BytesIO
from openpyxl import Workbook

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

    # Konkurs holati (hamma uchun qaytariladi)
    contest_status = db.get_contest_status_flag()
    end_date = db.get_contest_end_date()

    # last_seen yangilanadi
    if user:
        db.update_last_seen(user_id)

    if not user:
        return jsonify({
            "registered": False,
            "is_admin": is_admin,
            "telegram": {
                "id": user_id,
                "first_name": tg_user.get("first_name", ""),
                "username": tg_user.get("username", "")
            },
            "contest": {"status": contest_status, "end_date": end_date}
        })

    uid, name, uname, pubg_id, phone, ref_id, banned, joined = user
    count = db.get_referral_count(user_id)
    pending = db.get_pending_referral_count(user_id)
    rank = db.get_user_rank(user_id)
    gift_limit = db.get_gift_top_limit()
    was_subscribed = db.get_subscription_status(user_id)

    return jsonify({
        "registered": True,
        "is_admin": is_admin,
        "is_banned": bool(banned),
        "was_subscribed": was_subscribed,
        "has_pubg_id": pubg_id is not None,
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
        },
        "contest": {"status": contest_status, "end_date": end_date}
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


def is_valid_pubg_id(pubg_id: str) -> bool:
    """Kamida 7 xona, 5 yoki 6 bilan boshlanishi kerak"""
    return (
        isinstance(pubg_id, str)
        and pubg_id.isdigit()
        and len(pubg_id) >= 7
        and pubg_id[0] in ("5", "6")
    )


@app.route("/api/channels", methods=["GET"])
def get_channels():
    """Barcha majburiy kanallar ro'yxati (auth shart emas)"""
    channels = db.get_channels_with_names()
    return jsonify({"channels": [{"username": u, "name": n} for u, n in channels]})


@app.route("/api/me/subscription", methods=["GET"])
def check_subscription():
    """Foydalanuvchi barcha kanallarga obuna bo'lganini tekshiradi"""
    tg_user = get_user_from_request()
    if not tg_user:
        return jsonify({"error": "unauthorized"}), 401

    user_id = tg_user["id"]
    if user_id == ADMIN_ID:
        return jsonify({"all_subscribed": True, "not_subscribed": []})

    channels = db.get_channels_with_names()
    if not channels:
        return jsonify({"all_subscribed": True, "not_subscribed": []})

    import requests as req_lib
    not_subscribed = []
    for username, name in channels:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
            resp = req_lib.get(url, params={"chat_id": username, "user_id": user_id}, timeout=5)
            data = resp.json()
            if data.get("ok"):
                status = data["result"]["status"]
                if status in ["left", "kicked", "banned"]:
                    not_subscribed.append({"username": username, "name": name or username})
            else:
                not_subscribed.append({"username": username, "name": name or username})
        except Exception:
            not_subscribed.append({"username": username, "name": name or username})

    if not not_subscribed:
        db.set_subscription_status(user_id, True)

    return jsonify({
        "all_subscribed": len(not_subscribed) == 0,
        "not_subscribed": not_subscribed
    })
    """Foydalanuvchi Web App ichida ixtiyoriy ravishda PUBG ID qo'shadi/yangilaydi"""
    tg_user = get_user_from_request()
    if not tg_user:
        return jsonify({"error": "unauthorized"}), 401

    user_id = tg_user["id"]
    user = db.get_user(user_id)
    if not user:
        return jsonify({"error": "not_registered"}), 400

    data = request.get_json() or {}
    pubg_id = str(data.get("pubg_id", "")).strip()

    if not is_valid_pubg_id(pubg_id):
        return jsonify({
            "error": "invalid_pubg_id",
            "message": "PUBG ID kamida 7 xonali bo'lib, 5 yoki 6 raqami bilan boshlanishi kerak"
        }), 400

    db.update_pubg_id(user_id, pubg_id)
    return jsonify({"success": True, "pubg_id": pubg_id})


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

    today = db.get_today_stats()
    return jsonify({
        "total_users": db.get_total_users(),
        "total_channels": len(db.get_channels()),
        "total_referrals": db.get_total_referrals(),
        "stat_top_limit": db.get_stat_top_limit(),
        "gift_top_limit": db.get_gift_top_limit(),
        "active_last_24h": db.get_active_last_24h(),
        "joins_today": today["joins_today"],
        "referrals_today": today["referrals_today"],
        "left_today": today["left_today"],
    })


@app.route("/api/admin/users", methods=["GET"])
def admin_users():
    tg_user = get_user_from_request()
    if not check_admin(tg_user):
        return jsonify({"error": "forbidden"}), 403
    users = db.get_all_users_with_phones()  # eng yangi birinchi (joined_at DESC)
    result = []
    for uid, name, uname, pubg_id, phone in users[:3]:
        user_full = db.get_user(uid)
        joined_at = user_full[7] if user_full else None
        result.append({
            "id": uid,
            "telegram_id": uid,
            "name": name, "username": uname,
            "pubg_id": pubg_id, "phone": phone,
            "ref_count": db.get_referral_count(uid),
            "banned": db.is_banned(uid),
            "joined_at": joined_at,
        })
    return jsonify({"users": result, "total_count": len(users)})


@app.route("/api/admin/users/export", methods=["GET"])
def admin_export_users():
    """Hamma foydalanuvchilarni Excel fayl qilib to'g'ridan-to'g'ri yuklab beradi"""
    tg_user = get_user_from_request()
    if not check_admin(tg_user):
        return jsonify({"error": "forbidden"}), 403

    users = db.get_all_users_with_phones()

    wb = Workbook()
    ws = wb.active
    ws.title = "Foydalanuvchilar"
    ws.append(["№", "Telegram ID", "Ism", "Username", "PUBG ID", "Telefon", "Referallar soni", "Reyting"])

    for i, (uid, name, uname, pubg_id, phone) in enumerate(users, 1):
        ref_count = db.get_referral_count(uid)
        rank = db.get_user_rank(uid) if ref_count > 0 else "—"
        ws.append([
            i, uid, name, f"@{uname}" if uname else "—",
            pubg_id if pubg_id else "Kiritilmagan",
            phone if phone else "Yo'q", ref_count, rank
        ])

    for col in ws.columns:
        max_len = max((len(str(c.value)) for c in col if c.value), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 3, 40)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="foydalanuvchilar.xlsx"
    )


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
        db.set_contest_end_date(
            data["contest_end_date"],
            date_iso=data.get("contest_end_iso")
        )
        db.set_24h_warning_sent(False)
        db.set_contest_status_flag("active")
    return jsonify({"success": True})


@app.route("/api/admin/suspicious", methods=["GET"])
def admin_suspicious():
    tg_user = get_user_from_request()
    if not check_admin(tg_user):
        return jsonify({"error": "forbidden"}), 403
    rows = db.get_recent_suspicious_signups()
    result = [{"id": r[0], "name": r[1], "phone": r[2], "joined_at": r[3]} for r in rows]
    return jsonify({"suspicious": result, "is_suspicious": len(result) >= 3})


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
