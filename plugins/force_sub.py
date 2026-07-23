from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from helper.helper_func import is_bot_admin

#===============================================================#

async def fsub(client, query):
    # Create a formatted list of channels with names and IDs
    if client.fsub_dict:
        channel_list = []
        for channel_id, channel_data in client.fsub_dict.items():
            channel_name = channel_data[0] if channel_data and len(channel_data) > 0 else "Unknown"
            request_status = "Request: ✅" if channel_data[2] else "Request: ❌"
            timer_status = f"Timer: {channel_data[3]}m" if channel_data[3] > 0 else "Timer: ∞"
            channel_list.append(f"• `{channel_name}` (`{channel_id}`) - {request_status}, {timer_status}")
        
        channels_display = "\n".join(channel_list)
    else:
        channels_display = "_No force subscription channels configured_"
    
    msg = f"""<blockquote>**Force Subscription Settings:**</blockquote>
**Configured Channels:**
{channels_display}

__Use the appropriate button below to add or remove a force subscription channel based on your needs!__
"""
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('ᴀᴅᴅ ᴄʜᴀɴɴᴇʟ', 'add_fsub'), InlineKeyboardButton('ʀᴇᴍᴏᴠᴇ ᴄʜᴀɴɴᴇʟ', 'rm_fsub')],
        [InlineKeyboardButton('◂ ʙᴀᴄᴋ', 'settings')]]
    )
    await query.message.edit_text(msg, reply_markup=reply_markup)
    return

#===============================================================#

@Client.on_callback_query(filters.regex('^add_fsub$'))
async def add_fsub(client: Client, query: CallbackQuery):
    await query.answer()
    ask_channel_info = await client.ask(query.from_user.id, "Send channel id(negative integer value), request boolean(yes/no/true/false), timers(integer without decimal)(to enable it keep it greator than 0 otherwise the invite link will not have any timer to invalidate it) seperated by a space in the next 60 seconds!\n<blockquote expandable>Eg: `-10089479289 yes 5`\n\n__It means `-10089479289` is the force sub channel id, `yes` means to enable request it means the link will be request link and only after user sends request to the channel bot will work for that user even if you do not accept his request or user is not a member, `5` means timer in minutes aftetr 5 minutes the invite link will be expired.__</blockquote>", filters=filters.text, timeout=60)
    try:
        channel_info = ask_channel_info.text.split()
        channel_id, request, timer = channel_info
        channel_id = int(channel_id)
        if channel_id in client.fsub_dict.keys():
            return await ask_channel_info.reply("**This channel id already exists in force sub list, remove it to change it's configuration!!**")
        val, res = await is_bot_admin(client, channel_id)
        if not val:
            return await ask_channel_info.reply(f"**Error:** `{res}`")
        if request.lower() in ('true', 'on', 'yes'):
            request = True
        elif request.lower() in ('false', 'off', 'no'):
            request = False
        else:
            raise Exception("Invalid request value or type.")
        if timer.isdigit():
            timer = int(timer)
        else:
            raise Exception("Timer is not a valid integer.")
        chat = await client.get_chat(channel_id)
        name = chat.title
        if timer > 0:
            client.fsub_dict[channel_id] = [name, None, request, timer]
        else:
            chat_link = await client.create_chat_invite_link(channel_id, creates_join_request=request)
            link = chat_link.invite_link
            client.fsub_dict[channel_id] = [name, link, request, timer]
        
        # Update req_channels list if request is enabled
        if request and channel_id not in client.req_channels:
            client.req_channels.append(channel_id)
            await client.mongodb.set_channels(client.req_channels)
        
        # Save to database for persistence across bot restarts
        await client.mongodb.add_fsub_channel(channel_id, client.fsub_dict[channel_id])
        
        await fsub(client, query)
        return await ask_channel_info.reply(f"__Channel with name: `{name.strip()}` is added as a force sub channel!!__")
    except Exception as e:
        return await ask_channel_info.reply(f"**Error:** `{e}`")
    
#===============================================================#

@Client.on_callback_query(filters.regex('^rm_fsub$'))
async def rm_fsub(client: Client, query: CallbackQuery):
    await query.answer()
    ask_channel_info = await client.ask(query.from_user.id, "Send channel id(negative integer value) in the next 60 seconds!", filters=filters.text, timeout=60)
    try:
        channel_id = int(ask_channel_info.text)
        if channel_id not in client.fsub_dict.keys():
            return await ask_channel_info.reply("**This channel id is not in force sub list!**")
        
        # Check if it was a request channel and remove from req_channels
        if channel_id in client.req_channels:
            client.req_channels.remove(channel_id)
            await client.mongodb.set_channels(client.req_channels)
        
        client.fsub_dict.pop(channel_id)
        
        # Remove from database for persistence across bot restarts
        await client.mongodb.remove_fsub_channel(channel_id)
        
        await fsub(client, query)
        return await ask_channel_info.reply(f"__Channel with id: `{channel_id}` has been removed as a force sub channel!!__")
    except Exception as e:
        return await ask_channel_info.reply(f"**Error:** `{e}`")

#===============================================================#
# Bot Verification Commands
#===============================================================#

VALID_MODES = {
    "channel_only": "ᴄʜᴀɴɴᴇʟ ᴏɴʟʏ",
    "bot_only":     "ʙᴏᴛ ᴏɴʟʏ",
    "channel_bot":  "ᴄʜᴀɴɴᴇʟ + ʙᴏᴛ",
}

@Client.on_message(filters.command('addbot') & filters.private)
async def addbot_cmd(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return await message.reply("**✗ ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴜsᴇ ᴛʜɪs!**")
    ask = await client.ask(
        message.from_user.id,
        "Send the **bot username** (without @) to add to the bot verification list.\n"
        "<blockquote>Eg: `MyBot`</blockquote>",
        filters=filters.text, timeout=60
    )
    try:
        bot_username = ask.text.strip().lstrip('@')
        if not bot_username:
            return await ask.reply("**✗ ɪɴᴠᴀʟɪᴅ ᴜsᴇʀɴᴀᴍᴇ.**")
        if bot_username in client.bot_verify_dict:
            return await ask.reply(f"**✗ `@{bot_username}` ɪs ᴀʟʀᴇᴀᴅʏ ɪɴ ᴛʜᴇ ʟɪsᴛ!**")
        try:
            chat = await client.get_chat(bot_username)
            bot_name = chat.first_name or chat.title or bot_username
        except Exception:
            bot_name = bot_username
        client.bot_verify_dict[bot_username] = bot_name
        await client.mongodb.add_bot_verify(bot_username, bot_name)
        await ask.reply(f"**✓ `@{bot_username}` (`{bot_name}`) ᴀᴅᴅᴇᴅ ᴛᴏ ʙᴏᴛ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ʟɪsᴛ!**")
    except Exception as e:
        await ask.reply(f"**✗ ᴇʀʀᴏʀ:** `{e}`")

#===============================================================#

@Client.on_message(filters.command('delbot') & filters.private)
async def delbot_cmd(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return await message.reply("**✗ ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴜsᴇ ᴛʜɪs!**")
    if not client.bot_verify_dict:
        return await message.reply("**✗ ɴᴏ ʙᴏᴛs ɪɴ ᴛʜᴇ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ʟɪsᴛ.**")
    ask = await client.ask(
        message.from_user.id,
        "Send the **bot username** (without @) to remove.\n"
        "<blockquote>Eg: `MyBot`</blockquote>",
        filters=filters.text, timeout=60
    )
    try:
        bot_username = ask.text.strip().lstrip('@')
        if bot_username not in client.bot_verify_dict:
            return await ask.reply(f"**✗ `@{bot_username}` ɪs ɴᴏᴛ ɪɴ ᴛʜᴇ ʟɪsᴛ!**")
        client.bot_verify_dict.pop(bot_username)
        await client.mongodb.remove_bot_verify(bot_username)
        await ask.reply(f"**✓ `@{bot_username}` ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ ʙᴏᴛ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ʟɪsᴛ!**")
    except Exception as e:
        await ask.reply(f"**✗ ᴇʀʀᴏʀ:** `{e}`")

#===============================================================#

@Client.on_message(filters.command('listbots') & filters.private)
async def listbots_cmd(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return await message.reply("**✗ ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴜsᴇ ᴛʜɪs!**")
    mode = getattr(client, 'botverify_mode', 'channel_only')
    mode_label = VALID_MODES.get(mode, mode)
    if not client.bot_verify_dict:
        bot_list = "_ɴᴏ ʙᴏᴛs ᴄᴏɴғɪɢᴜʀᴇᴅ_"
    else:
        bot_list = "\n".join(
            f"• `{name}` (@{uname})"
            for uname, name in client.bot_verify_dict.items()
        )
    await message.reply(
        f"<blockquote>**ʙᴏᴛ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ʟɪsᴛ**</blockquote>\n"
        f"**ᴍᴏᴅᴇ:** `{mode_label}`\n\n"
        f"{bot_list}"
    )

#===============================================================#

@Client.on_message(filters.command('botverify_mode') & filters.private)
async def botverify_mode_cmd(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return await message.reply("**✗ ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴜsᴇ ᴛʜɪs!**")
    current = getattr(client, 'botverify_mode', 'channel_only')
    modes_text = "\n".join(f"• `{k}` — {v}" for k, v in VALID_MODES.items())
    ask = await client.ask(
        message.from_user.id,
        f"**ᴄᴜʀʀᴇɴᴛ ᴍᴏᴅᴇ:** `{current}`\n\n"
        f"**ᴀᴠᴀɪʟᴀʙʟᴇ ᴍᴏᴅᴇs:**\n{modes_text}\n\n"
        "Send the mode key to switch to it.",
        filters=filters.text, timeout=60
    )
    try:
        new_mode = ask.text.strip().lower()
        if new_mode not in VALID_MODES:
            return await ask.reply(
                f"**✗ ɪɴᴠᴀʟɪᴅ ᴍᴏᴅᴇ.** ᴄʜᴏᴏsᴇ: `{'` | `'.join(VALID_MODES)}`"
            )
        client.botverify_mode = new_mode
        await client.mongodb.set_botverify_mode(new_mode)
        await ask.reply(f"**✓ ᴍᴏᴅᴇ sᴇᴛ ᴛᴏ `{new_mode}` ({VALID_MODES[new_mode]})**")
    except Exception as e:
        await ask.reply(f"**✗ ᴇʀʀᴏʀ:** `{e}`")

#===============================================================#

@Client.on_callback_query(filters.regex('^bverify$'))
async def bot_verify_callback(client: Client, query: CallbackQuery):
    """Mark all required bots as verified for the user (trust-based)."""
    user_id = query.from_user.id
    bot_verify_dict = getattr(client, 'bot_verify_dict', {})
    if not bot_verify_dict:
        return await query.answer("ɴᴏ ʙᴏᴛs ᴛᴏ ᴠᴇʀɪғʏ.", show_alert=True)
    for bot_username in bot_verify_dict:
        await client.mongodb.set_user_bot_verified(user_id, bot_username)
    await query.answer(
        "✅ ᴠᴇʀɪғɪᴇᴅ! ɴᴏᴡ ᴄʟɪᴄᴋ '🔄 Try Again' ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ғɪʟᴇs.",
        show_alert=True
    )
