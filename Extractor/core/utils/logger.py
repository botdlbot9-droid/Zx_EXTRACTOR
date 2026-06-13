from Extractor import app

async def forward_to_log(message, tag="LOG"):
    try:
        chat_id = -1003728827978  # apna channel id

        await app.send_message(
            chat_id=chat_id,
            text=f"📥 {tag}\n\n{message.text if hasattr(message, 'text') else str(message)}"
        )
    except Exception as e:
        print("Log error:", e)
