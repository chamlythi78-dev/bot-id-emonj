"""
Bot lấy Telegram Premium Custom Emoji ID.
- Gửi/forward tin nhắn có emoji Premium cho bot.
- Bot trả về tối đa 500 ID duy nhất trong một lượt quét.
- Không hard-code token: đặt biến môi trường BOT_TOKEN.
Cài đặt: pip install -U python-telegram-bot
Chạy:
  Windows PowerShell: $env:BOT_TOKEN="TOKEN_MOI"; python get_emoji_ids.py
  Linux/macOS: BOT_TOKEN="TOKEN_MOI" python get_emoji_ids.py
"""

import os
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

MAX_IDS_PER_SCAN = 500


async def scan_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if not msg:
        return

    entities = list(msg.entities or []) + list(msg.caption_entities or [])
    found = []
    seen = set()

    for entity in entities:
        if entity.type == "custom_emoji" and entity.custom_emoji_id:
            emoji_id = str(entity.custom_emoji_id)
            if emoji_id not in seen:
                seen.add(emoji_id)
                found.append(emoji_id)
            if len(found) >= MAX_IDS_PER_SCAN:
                break

    if not found:
        await msg.reply_text(
            "Không tìm thấy emoji Premium trong tin nhắn này.\n"
            "Bạn hãy gửi hoặc chuyển tiếp tin nhắn có emoji Premium cho bot nhé."
        )
        return

    # Telegram giới hạn độ dài tin nhắn; chia kết quả thành các phần nhỏ.
    header = f"Đã lấy {len(found)} ID emoji Premium:\n\n"
    lines = [f"`{emoji_id}`" for emoji_id in found]
    chunks = []
    current = header

    for line in lines:
        if len(current) + len(line) + 1 > 3500:
            chunks.append(current)
            current = ""
        current += line + "\n"

    if current:
        chunks.append(current)

    for index, chunk in enumerate(chunks, start=1):
        suffix = f"\nPhần {index}/{len(chunks)}" if len(chunks) > 1 else ""
        await msg.reply_text(chunk + suffix, parse_mode="Markdown")

    if len(entities) > len(found):
        # Thông báo nhẹ: các entity khác (chữ/link/mention) không phải custom emoji.
        pass


def main() -> None:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit(
            "Thiếu BOT_TOKEN. Hãy đặt biến môi trường BOT_TOKEN bằng token mới từ BotFather."
        )

    app = Application.builder().token(token).build()
    app.add_handler(
        MessageHandler(
            filters.TEXT | filters.CAPTION,
            scan_message,
        )
    )
    print("Bot đang chạy. Gửi hoặc forward tin nhắn có emoji Premium cho bot.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
