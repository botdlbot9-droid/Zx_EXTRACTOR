import os

# ----------- REQUIRED VARIABLES (Inko Render/Heroku par set karna hi padega) -----------
API_ID = int(os.environ.get("API_ID", 0))          # Your API ID from my.telegram.org
API_HASH = os.environ.get("API_HASH", "")          # Your API Hash
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")        # Your Bot Token from @BotFather
# -------------------------------------------------------------------------------------

# ----------- OPTIONAL VARIABLES (Defaults diye hain, chaahe toh change karo) ----------
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")
BOT_TEXT = "Sumit_Zx"
OWNER_ID = int(os.environ.get("OWNER_ID", 6884772962))
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", -1003086072844))
CHANNEL_ID2 = int(os.environ.get("CHANNEL_ID2", -1003728827978))
MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://itsgoluAPI:jrMHSipToKUEnmcp@cpprivateapi.ghhp3oz.mongodb.net/?appName=CpprivateApi")
PREMIUM_LOGS = int(os.environ.get("PREMIUM_LOGS", 0))
join = '✳️ JOIN BACKUP'
UNSPLASH_ACCESS_KEY = 'RabDRmuXXBobanmwwbvpP5LwoG4J8ox34y5Sstz-9jk'
UNSPLASH_QUERY = 'animal baby'
ADMIN_BOT_USERNAME = ""  # without @
THUMB_URL = os.environ.get("THUMB_URL", "https://files.catbox.moe/vg3vae.jpg")
