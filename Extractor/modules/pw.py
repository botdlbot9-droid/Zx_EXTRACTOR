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
