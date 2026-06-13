from Extractor import app

async def forward_to_log(message, tag="LOG"):
    try:
        await app.send_message(
            chat_id=-100xxxxxxxxxx,  # apna log channel id
            text=f"📥 {tag}\n\n{message.text if hasattr(message, 'text') else str(message)}"
        )
    except Exception as e:
        print("Log forward error:", e)
