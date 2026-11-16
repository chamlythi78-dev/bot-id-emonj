"""
Bot lấy Telegram Premium Custom Emoji ID kèm emoji thường tương ứng.
- Gửi/forward tin nhắn có emoji Premium cho bot.
- Bot trả về tối đa 500 ID duy nhất trong một lượt quét.
- Không hard-code token: đặt biến môi trường BOT_TOKEN.
Cài đặt: pip install -U python-telegram-bot
Chạy:
  Windows PowerShell: $env:BOT_TOKEN="TOKEN"; python get_emoji_ids.py
  Linux/macOS: BOT_TOKEN="TOKEN" python get_emoji_ids.py
"""

import os
from html import escape

from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

MAX_IDS_PER_SCAN = 500


def get_entity_text(text: str, offset: int, length: int) -> str:
    """Telegram entity offsets/lengths dùng đơn vị UTF-16, không phải ký tự Python."""
    raw = text.encode("utf-16-le")
    start = offset * 2
    end = (offset + length) * 2
    return raw[start:end].decode("utf-16-le", errors="replace")


async def scan_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if not msg:
        return

    source_text = msg.text or msg.caption or ""
    entities = list(msg.entities or []) + list(msg.caption_entities or [])

    found = []
    seen = set()

    for entity in entities:
        if entity.type != "custom_emoji" or not entity.custom_emoji_id:
            continue

        emoji_id = str(entity.custom_emoji_id)
        if emoji_id in seen:
            continue

        seen.add(emoji_id)
        fallback_emoji = get_entity_text(
            source_text, entity.offset, entity.length
        ).strip()

        # Giữ emoji thường ở đầu dòng, ID nằm trong thẻ code để dễ sao chép.
        found.append((fallback_emoji or "❔", emoji_id))

        if len(found) >= MAX_IDS_PER_SCAN:
            break

    if not found:
        await msg.reply_text(
            "Không tìm thấy emoji Premium trong tin nhắn này.\n"
            "Bạn hãy gửi hoặc chuyển tiếp tin nhắn có emoji Premium cho bot nhé."
        )
        return

    header = f"Đã lấy {len(found)} ID emoji Premium:\n\n"
    lines = [
        f"{escape(emoji)}  <code>{escape(emoji_id)}</code>"
        for emoji, emoji_id in found
    ]

    # Chia nhỏ để không vượt giới hạn độ dài tin nhắn Telegram.
    chunks = []
    current = header

    for line in lines:
        addition = line + "\n"
        if len(current) + len(addition) > 3500 and current != header:
            chunks.append(current)
            current = ""
        current += addition

    if current:
        chunks.append(current)

    for index, chunk in enumerate(chunks, start=1):
        suffix = f"\nPhần {index}/{len(chunks)}" if len(chunks) > 1 else ""
        await msg.reply_text(chunk + suffix, parse_mode="HTML")


def main() -> None:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit(
            "Thiếu BOT_TOKEN. Hãy đặt biến môi trường BOT_TOKEN bằng token bot từ BotFather."
        )

    app = Application.builder().token(token).build()
    app.add_handler(
        MessageHandler(filters.TEXT | filters.CAPTION, scan_message)
    )
    print("Bot đang chạy. Gửi hoặc forward tin nhắn có emoji Premium cho bot.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
