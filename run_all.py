"""
Botni va Web App serverini BIRGALIKDA ishga tushiradi.
Ishlatish: python run_all.py
"""
import asyncio
import threading
from webapp_server import app as flask_app
from bot import main as bot_main


def run_flask():
    flask_app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)


if __name__ == "__main__":
    # Flask serverni alohida threadda ishga tushiramiz
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("✅ Web App server ishga tushdi: http://0.0.0.0:5000")

    # Botni asosiy threadda (asyncio) ishga tushiramiz
    asyncio.run(bot_main())
