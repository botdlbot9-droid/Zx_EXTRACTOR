async def forward_to_log(message, tag):
    try:
        from Extractor import app
        await app.send_message(
            chat_id=-100xxxxxxxxxx,  # apna log channel id
            text=f"📥 {tag}\n\n{message.text if hasattr(message, 'text') else message}"
        )
    except:
        pass
