from datetime import datetime
import pytz

# ================= TIMEZONE =================
india_tz = pytz.timezone("Asia/Kolkata")


# ================= TODAY FILTER =================
def is_today(item):
    try:
        raw_date = (
            item.get("createdAt")
            or item.get("date")
            or item.get("uploadedOn")
            or item.get("updatedAt")
            or ""
        )

        if not raw_date:
            return False

        item_date = str(raw_date)[:10]
        today_date = datetime.now(india_tz).strftime("%Y-%m-%d")

        return item_date == today_date

    except:
        return False
