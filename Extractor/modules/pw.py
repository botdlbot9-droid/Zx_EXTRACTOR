import asyncio
import aiohttp
import requests
import json
import re
import time
import unicodedata
import pytz

from datetime import datetime
from pyrogram import Client, filters
from Extractor import app
from config import PREMIUM_LOGS, join

# ================= TIME =================
india_timezone = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(india_timezone)
time_new = current_time.strftime("%d-%m-%Y %I:%M %p")


# ================= FETCH CONTENT (FIXED MISSING ERROR) =================
async def fetch_content(session, url, headers):
    try:
        async with session.get(url, headers=headers, timeout=30) as r:
            return await r.json()
    except:
        return None


# ================= CLEAN TEXT =================
def clean_text(text):
    if not text:
        return ""
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    return text


# ================= MPD HANDLER =================
def extract_mpd_info(url, content_id=None, batch_id=None):
    if "cloudfront.net" in url:
        return url, batch_id, content_id

    base_url = url.split('parentId=')[0].rstrip('&') if 'parentId=' in url else url
    parent_id = batch_id
    child_id = content_id

    return base_url, parent_id, child_id


# ================= FORMAT LINE =================
def format_content_line(name, url, content_type="", parent_id=None, child_id=None):
    name = clean_text(name)
    prefix = f"[{content_type}] " if content_type else ""

    if parent_id and child_id:
        return f"{prefix}{name}:{url}&parentId={parent_id}&childId={child_id}"
    return f"{prefix}{name}:{url}"


# ================= CORE PROCESS =================
async def process_subject_content(session, target_id, subject_id, headers, all_links, total_links):

    tasks = []

    for page in range(1, 12):
        url = f"https://api.penpencil.co/v2/batches/{target_id}/subject/{subject_id}/contents?page={page}&contentType=exercises-notes-videos"
        tasks.append(fetch_content(session, url, headers))

    responses = await asyncio.gather(*tasks)

    for content_response in responses:

        if not content_response or not content_response.get("data"):
            continue

        for item in content_response.get("data", []):

            try:
                if not item:
                    continue

                video_details = item.get("videoDetails", {}) or {}
                content_id = video_details.get("findKey")

                topic = clean_text(item.get("topic", ""))
                url = item.get("url", "")
                content_type = (item.get("lectureType") or "video").lower()

                # ================= MAIN =================
                if url:
                    if ".mpd" in url:
                        final_url, parent_id, child_id = extract_mpd_info(
                            url, content_id, target_id
                        )
                        line = format_content_line(
                            topic, final_url, content_type, parent_id, child_id
                        )
                    else:
                        line = format_content_line(topic, url, content_type)

                    all_links.append(line)
                    total_links[0] += 1

                # ================= HOMEWORK =================
                for hw in item.get("homeworkIds", []):
                    hw_id = hw.get("_id")

                    for attachment in hw.get("attachmentIds", []):
                        try:
                            name = clean_text(attachment.get("name", ""))
                            base_url = attachment.get("baseUrl", "")
                            key = attachment.get("key", "")

                            if key:
                                full_url = f"{base_url}{key}"

                                if ".mpd" in full_url:
                                    final_url, parent_id, child_id = extract_mpd_info(
                                        full_url, hw_id, target_id
                                    )
                                    line = format_content_line(
                                        name, final_url, "notes", parent_id, child_id
                                    )
                                else:
                                    line = format_content_line(name, full_url, "notes")

                                all_links.append(line)
                                total_links[0] += 1

                        except:
                            continue

            except:
                continue


# NOTE:
# PW login handler tumhara same rahega, is core file se extraction stable ho jayega.
@app.on_message(filters.command(["pw"]))
async def pw_login(client, message):

    try:
        query_msg = await app.ask(
            message.chat.id,
            "🔐 Enter PW Mobile No. or Login Token:"
        )

        user_input = query_msg.text.strip()

        # ================= TOKEN DIRECT =================
        if user_input.startswith("eyJ"):
            token = user_input

        # ================= MOBILE LOGIN =================
        elif user_input.isdigit():

            mob = user_input

            payload = {
                "username": mob,
                "countryCode": "+91",
                "organizationId": "5eb393ee95fab7468a79d189"
            }

            headers = {
                "client-id": "5eb393ee95fab7468a79d189",
                "client-version": "12.84",
                "Client-Type": "MOBILE",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }

            await message.reply_text("📲 Sending OTP...")

            otp_response = requests.post(
                "https://api.penpencil.co/v1/users/get-otp?smsType=0",
                headers=headers,
                json=payload
            ).json()

            if not otp_response:
                await message.reply_text("❌ OTP send failed")
                return

            otp_msg = await app.ask(message.chat.id, "🔑 Enter OTP:")
            otp = otp_msg.text.strip()

            token_payload = {
                "username": mob,
                "otp": otp,
                "client_id": "system-admin",
                "client_secret": "KjPXuAVfC5xbmgreETNMaL7z",
                "grant_type": "password",
                "organizationId": "5eb393ee95fab7468a79d189",
                "latitude": 0,
                "longitude": 0
            }

            token_response = requests.post(
                "https://api.penpencil.co/v3/oauth/token",
                data=token_payload
            ).json()

            token = token_response.get("data", {}).get("access_token")

            if not token:
                await message.reply_text("❌ Login failed (OTP wrong)")
                return

        else:
            await message.reply_text("❌ Invalid input")
            return

        # ================= HEADERS =================
        headers = {
            "Authorization": f"Bearer {token}",
            "client-id": "5eb393ee95fab7468a79d189",
            "client-type": "WEB",
            "client-version": "3.3.0",
            "Accept": "application/json"
        }

        # ================= FETCH BATCHES =================
        batch_response = requests.get(
            "https://api.penpencil.co/v3/batches/my-batches?mode=1&amount=paid&page=1",
            headers=headers
        ).json()

        batches = batch_response.get("data", [])

        if not batches:
            await message.reply_text("❌ No batches found")
            return

        batch_map = {}
        batch_text = "📚 YOUR BATCHES:\n\n"

        for b in batches:
            bid = b.get("_id")
            name = b.get("name")
            batch_map[bid] = name
            batch_text += f"{bid} ➜ {name}\n"

        await message.reply_text(batch_text)

        target_msg = await app.ask(message.chat.id, "🆔 Enter Batch ID:")
        target_id = target_msg.text.strip()

        if target_id not in batch_map:
            await message.reply_text("❌ Invalid Batch ID")
            return

        batch_name = batch_map[target_id]

        # ================= SUBJECTS =================
        course = requests.get(
            f"https://api.penpencil.co/v3/batches/{target_id}/details",
            headers=headers
        ).json()

        subjects = course.get("data", {}).get("subjects", [])

        if not subjects:
            await message.reply_text("❌ No subjects found")
            return

        all_links = []
        total_links = [0]

        await message.reply_text("🚀 Extraction Started...")

        async with aiohttp.ClientSession() as session:

            tasks = []

            for sub in subjects:
                sid = sub.get("_id")
                tasks.append(
                    process_subject_content(
                        session,
                        target_id,
                        sid,
                        headers,
                        all_links,
                        total_links
                    )
                )

            await asyncio.gather(*tasks)

        # ================= SAVE FILE =================
        filename = f"{batch_name}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            for line in all_links:
                f.write(line + "\n")

        await message.reply_document(filename)

        await app.send_message(
            PREMIUM_LOGS,
            f"✅ Extraction Done\nBatch: {batch_name}\nLinks: {total_links[0]}"
        )

    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")
