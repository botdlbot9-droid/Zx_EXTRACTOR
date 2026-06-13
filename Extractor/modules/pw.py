import asyncio
import json
import time
import re
import unicodedata
import requests

from typing import List

import aiohttp
import pytz
from datetime import datetime

from pyrogram import filters
from Extractor import app
from Extractor.core.utils import forward_to_log
from config import PREMIUM_LOGS, join
# ================= TIME =================
india_timezone = pytz.timezone("Asia/Kolkata")
time_new = datetime.now(india_timezone).strftime("%d-%m-%Y %I:%M %p")


# ================= FETCH =================
async def fetch_content(session, url, headers) -> dict:
    async with session.get(url, headers=headers) as response:
        return await response.json()


# ================= CLEAN =================
def clean_text(text):
    if not text:
        return ""
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return text.replace(":", "_").replace("/", "_").replace("|", "_").replace("\\", "_")


# ================= FORMAT =================
def format_content_line(name, url, content_type="", parent_id=None, child_id=None):
    name = clean_text(name)
    prefix = f"[{content_type}] " if content_type else ""

    if parent_id and child_id:
        return f"{prefix}{name}:{url}&parentId={parent_id}&childId={child_id}"
    return f"{prefix}{name}:{url}"


# ================= MPD =================
def extract_mpd_info(url, content_id=None, batch_id=None):
    if "cloudfront.net" in url:
        return url, batch_id, content_id

    base_url = url.split("parentId=")[0].rstrip("&") if "parentId=" in url else url
    parent_match = re.search(r"parentId=([^&]+)", url)
    child_match = re.search(r"childId=([^&]+)", url)

    parent_id = parent_match.group(1) if parent_match else batch_id
    child_id = child_match.group(1) if child_match else content_id

    return base_url, parent_id, child_id


# ================= CORE FUNCTION =================
async def process_subject_content(session, target_id, subject_id, headers, all_links: List[str], total_links: List[int], mode):

    tasks = []

    for page in range(1, 12):
        url = f"https://api.penpencil.co/v2/batches/{target_id}/subject/{subject_id}/contents?page={page}&contentType=exercises-notes-videos"
        tasks.append(fetch_content(session, url, headers))

    responses = await asyncio.gather(*tasks)

    today_date = datetime.now(india_timezone).strftime("%Y-%m-%d")

    for content_response in responses:
        if not content_response or not content_response.get("data"):
            continue

        for item in content_response.get("data", []):
            try:

                # ================= TODAY FILTER =================
                item_date = (item.get("createdAt") or item.get("date", ""))[:10]

                if mode == "2" and item_date != today_date:
                    continue

                video_details = item.get("videoDetails") or {}
                content_id = video_details.get("findKey")

                topic = clean_text(item.get("topic", ""))
                url = item.get("url", "")
                content_type = (item.get("lectureType") or "video").lower()

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


# ================= MAIN BOT HANDLER =================
@app.on_message(filters.command(["pw"]))
async def pw_login(app, message):
    try:
        query_msg = await app.ask(message.chat.id, "Enter mobile or token:")
        user_input = query_msg.text.strip()

        if user_input.isdigit():
            await message.reply_text("Use token only in this version.")
            return

        token = user_input

        headers = {
            "client-id": "5eb393ee95fab7468a79d189",
            "client-type": "WEB",
            "Authorization": f"Bearer {token}",
        }

        batch_response = requests.get(
            "https://api.penpencil.co/v3/batches/my-batches?mode=1&amount=paid&page=1",
            headers=headers
        ).json()

        batches = batch_response.get("data", [])
        if not batches:
            await message.reply_text("No batches found")
            return

        batch_map = {}
        batch_text = "Your Batches:\n\n"

        for b in batches:
            batch_map[b["_id"]] = b["name"]
            batch_text += f"{b['_id']} -> {b['name']}\n"

        target_id_msg = await app.ask(message.chat.id, "Enter Course ID:")
        target_id = target_id_msg.text.strip()

        mode_msg = await app.ask(message.chat.id, "1 Full Batch / 2 Today")
        mode = mode_msg.text.strip()

        if target_id not in batch_map:
            await message.reply_text("Invalid Course ID")
            return

        batch_name = batch_map[target_id]

        course = requests.get(
            f"https://api.penpencil.co/v3/batches/{target_id}/details",
            headers=headers
        ).json()

        subjects = course.get("data", {}).get("subjects", [])

        all_links = []
        total_links = [0]

        async with aiohttp.ClientSession() as session:
            tasks = []

            for sub in subjects:
                si = sub["_id"]
                task = process_subject_content(session, target_id, si, headers, all_links, total_links, mode)
                tasks.append(task)

            await asyncio.gather(*tasks)

        filename = f"{batch_name}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            for line in all_links:
                f.write(line + "\n")

        await message.reply_document(filename)

    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")
