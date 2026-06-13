from Extractor import app

async def forward_to_log(message, tag="LOG"):
    try:
        chat_id = -1001234567890  # 👈 REAL Telegram channel ID yaha daal

        await app.send_message(
            chat_id=chat_id,
            text=f"📥 {tag}\n\n{message.text if hasattr(message, 'text') else str(message)}"
        )
    except Exception as e:
        print("Log error:", e)
