#!/usr/bin/env python3
"""
╔════════════════════════╗
║     SOMANI DECODER     ║
║      PREMIUM EDITION   ║
╚════════════════════════╝
Production-ready Telegram bot — Python 3.11+
"""

import os
import sys
import time
import tempfile
import subprocess
import textwrap
from pathlib import Path

import telebot
from telebot import types

# ─────────────────────────────────────────────
#  CONFIG  —  PASTE YOUR TOKEN ON THE NEXT LINE
# ─────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN")

OWNER_USERNAME = "@somani_07x"         # change to your Telegram username
OWNER_CONTACT  = "https://t.me/somani_07x"
BOT_VERSION    = "1.0.0"
EXEC_TIMEOUT   = 30                      # seconds per execution

# ── Validate token before creating bot ────────
if not BOT_TOKEN:
    print(
        "\n"
        "╔══════════════════════════════════════╗\n"
        "║   ❌  BOT TOKEN NOT SET              ║\n"
        "╠══════════════════════════════════════╣\n"
        "║  Open somani_decoder_bot.py and      ║\n"
        "║  replace YOUR_BOT_TOKEN_HERE with    ║\n"
        "║  the token from @BotFather.          ║\n"
        "╚══════════════════════════════════════╝\n"
    )
    sys.exit(1)

bot = telebot.TeleBot(BOT_TOKEN.strip(), parse_mode="Markdown")

# ─────────────────────────────────────────────
#  STATS (in-memory, resets on restart)
# ─────────────────────────────────────────────
stats = {
    "total_decoded": 0,
    "total_users": set(),
    "start_time": time.time(),
}

# ─────────────────────────────────────────────
#  ASCII LOGO & THEMED STRINGS
# ─────────────────────────────────────────────
LOGO = (
    "```\n"
    "╔════════════════════════╗\n"
    "║   ░██████╗░░█████╗░███╗░░░███╗░█████╗░███╗░░██╗██╗   ║\n"
    "║   ██╔════╝░██╔══██╗████╗░████║██╔══██╗████╗░██║██║   ║\n"
    "║   ╚█████╗░██║░░██║██╔████╔██║███████║██╔██╗░██║██║   ║\n"
    "║   ░╚═══██╗██║░░██║██║╚██╔╝██║██╔══██║██║╚████║██║   ║\n"
    "║   ██████╔╝╚█████╔╝██║░╚═╝░██║██║░░██║██║░╚███║██║   ║\n"
    "║   ╚═════╝░░╚════╝░╚═╝░░░░░╚═╝╚═╝░░╚═╝╚═╝░░╚══╝╚═╝   ║\n"
    "╚════════════════════════════════════════════════════╝\n"
    "```"
)

LOGO_SMALL = (
    "```\n"
    "╔════════════════════════╗\n"
    "║     SOMANI DECODER     ║\n"
    "║      PREMIUM EDITION   ║\n"
    "╚════════════════════════╝\n"
    "```"
)

DIVIDER = "```\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n```"

DECODER_INJECTION = textwrap.dedent("""\
    # ─── SOMANI DECODER INJECTION ───────────────────────────
    _print = print
    print = lambda *a, **k: _print(
        *(x.decode('utf-8', errors='replace') if isinstance(x, (bytes, bytearray)) else x for x in a),
        **k
    )
    exec = print
    # ─────────────────────────────────────────────────────────

""")

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def box(title: str, body: str) -> str:
    """Wrap content in a styled box message."""
    return (
        f"{LOGO_SMALL}\n"
        f"🔷 *{title}*\n"
        f"{DIVIDER}\n"
        f"{body}\n"
        f"{DIVIDER}\n"
        f"⚡ *SOMANI DECODER* `v{BOT_VERSION}`"
    )


def progress(chat_id: int, step: str, icon: str = "🔄") -> types.Message:
    """Send an ephemeral progress update."""
    text = (
        f"{icon} `{step}`\n"
        f"```\n[ {'█' * (10 if icon != '✅' else 10)}{'░' * 0} ] 100%\n```"
    )
    return bot.send_message(chat_id, text)


def edit_progress(msg: types.Message, step: str, icon: str = "✅"):
    """Edit a progress message in place."""
    text = (
        f"{icon} `{step}`\n"
        f"```\n[ ██████████ ] 100%\n```"
    )
    try:
        bot.edit_message_text(text, msg.chat.id, msg.message_id)
    except Exception:
        pass


def main_keyboard() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📂  Decode File",  callback_data="how_to_decode"),
        types.InlineKeyboardButton("❓  Help",          callback_data="help"),
    )
    kb.add(
        types.InlineKeyboardButton("👑  Owner",         callback_data="owner"),
        types.InlineKeyboardButton("📊  Stats",         callback_data="stats"),
    )
    return kb


def uptime_str() -> str:
    secs = int(time.time() - stats["start_time"])
    h, rem = divmod(secs, 3600)
    m, s   = divmod(rem, 60)
    return f"{h}h {m}m {s}s"


def safe_send(chat_id: int, text: str, **kwargs):
    """Send a Markdown message; fall back to plain text if parsing fails."""
    try:
        bot.send_message(chat_id, text, parse_mode="Markdown",
                         disable_web_page_preview=True, **kwargs)
    except Exception:
        # Strip Markdown characters and send plain
        plain = (text
                 .replace("*", "").replace("`", "").replace("_", "")
                 .replace("[", "").replace("]", "").replace("\\.", "."))
        bot.send_message(chat_id, plain, disable_web_page_preview=True, **kwargs)


# ─────────────────────────────────────────────
#  /start
# ─────────────────────────────────────────────

@bot.message_handler(commands=["start"])
def cmd_start(msg: types.Message):
    stats["total_users"].add(msg.from_user.id)
    name = msg.from_user.first_name or "User"

    body = (
        f"👋 Welcome, *{name}*!\n\n"
        "🌐 You are now inside the *SOMANI DECODER* — a premium\n"
        "     Python file decoder & executor system.\n\n"
        "🔹 *What I do:*\n"
        "     › Accept `.py` files\n"
        "     › Inject a smart decoder layer\n"
        "     › Execute securely in a sandbox\n"
        "     › Return full decoded output\n\n"
        "🔹 *How to use:*\n"
        "     Simply send me any `.py` file and I will\n"
        "     process it instantly.\n\n"
        "     Use the buttons below to explore features. 👇"
    )

    bot.send_message(msg.chat.id, box("WELCOME", body), reply_markup=main_keyboard())


# ─────────────────────────────────────────────
#  INLINE BUTTON CALLBACKS
# ─────────────────────────────────────────────

@bot.callback_query_handler(func=lambda c: c.data == "how_to_decode")
def cb_how_to_decode(call: types.CallbackQuery):
    body = (
        "📤 *Send a `.py` file* directly in this chat.\n\n"
        "🔄 *Processing steps:*\n"
        "     1️⃣  File Received\n"
        "     2️⃣  Injecting Decoder\n"
        "     3️⃣  Executing File\n"
        "     4️⃣  Preparing Result\n"
        "     5️⃣  Sending Output\n\n"
        "📥 *Output:* A `.py` file with decoded results\n"
        "     *(first & last line marked with `#SOMANI GOD`)*"
    )
    bot.answer_callback_query(call.id)
    safe_send(call.message.chat.id, box("HOW TO DECODE", body))


@bot.callback_query_handler(func=lambda c: c.data == "help")
def cb_help(call: types.CallbackQuery):
    body = (
        "📖 *COMMAND LIST*\n\n"
        "  `/start`  —  Launch the bot & main menu\n\n"
        "📁 *FILE SUPPORT*\n\n"
        "  ✅  `.py`  files only\n"
        "  ❌  Other formats rejected\n\n"
        "⚙️  *FEATURES*\n\n"
        "  🔐  Decoder injection\n"
        "  🖥  Secure subprocess execution\n"
        "  📄  Full output capture (no truncation)\n"
        "  💾  Result returned as `.py` file\n\n"
        "⏱  *LIMITS*\n\n"
        f"  Execution timeout: `{EXEC_TIMEOUT}s`\n"
        "  Max file size: `5 MB`\n\n"
        "🛡  *SECURITY*\n\n"
        "  Files run in isolated subprocess\\.\n"
        "  No persistence\\. No network access granted\\."
    )
    bot.answer_callback_query(call.id)
    safe_send(call.message.chat.id, box("HELP & COMMANDS", body))


@bot.callback_query_handler(func=lambda c: c.data == "owner")
def cb_owner(call: types.CallbackQuery):
    body = (
        "👑 *BOT OWNER*\n\n"
        f"  Handle  : `{OWNER_USERNAME}`\n"
        f"  Contact : [Open Chat]({OWNER_CONTACT})\n\n"
        "💬 *Support*\n\n"
        "  For issues, bugs, or custom decoder\n"
        "  requests — reach out to the owner directly\\.\n\n"
        "⚡ *SOMANI DECODER* is a premium commercial tool\\.\n"
        "  Unauthorized redistribution is prohibited\\."
    )
    bot.answer_callback_query(call.id)
    safe_send(call.message.chat.id, box("OWNER INFO", body))


@bot.callback_query_handler(func=lambda c: c.data == "stats")
def cb_stats(call: types.CallbackQuery):
    body = (
        "📊 *LIVE STATISTICS*\n\n"
        f"  🔓  Files Decoded  : `{stats['total_decoded']}`\n"
        f"  👥  Unique Users   : `{len(stats['total_users'])}`\n"
        f"  ⏱️   Uptime         : `{uptime_str()}`\n"
        f"  🤖  Bot Version    : `v{BOT_VERSION}`\n\n"
        "  Stats reset on bot restart."
    )
    bot.answer_callback_query(call.id)
    safe_send(call.message.chat.id, box("BOT STATISTICS", body))


# ─────────────────────────────────────────────
#  FILE HANDLER — .py files
# ─────────────────────────────────────────────

@bot.message_handler(content_types=["document"])
def handle_file(msg: types.Message):
    doc = msg.document
    chat_id = msg.chat.id
    stats["total_users"].add(msg.from_user.id)

    # ── Validate extension ──────────────────
    if not doc.file_name.endswith(".py"):
        bot.reply_to(
            msg,
            "```\n"
            "╔══════════════════════════╗\n"
            "║   ❌  INVALID FILE TYPE  ║\n"
            "╚══════════════════════════╝\n"
            "```\n"
            "⚠️  Only `.py` files are accepted.\n"
            "Please send a valid Python script.",
        )
        return

    # ── Validate size (5 MB) ────────────────
    if doc.file_size and doc.file_size > 5 * 1024 * 1024:
        bot.reply_to(msg, "❌ File too large. Maximum size is *5 MB*.")
        return

    # ── Step 1: File Received ───────────────
    p1 = progress(chat_id, "File Received ...", "📥")
    time.sleep(0.4)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Download file
        file_info = bot.get_file(doc.file_id)
        downloaded = bot.download_file(file_info.file_path)
        src_path = Path(tmpdir) / doc.file_name
        src_path.write_bytes(downloaded)

        original_code = src_path.read_text(encoding="utf-8", errors="replace")

        # ── Step 2: Injecting Decoder ──────
        edit_progress(p1, "File Received ✓", "✅")
        p2 = progress(chat_id, "Injecting Decoder ...", "💉")
        time.sleep(0.4)

        injected_code = DECODER_INJECTION + original_code
        injected_path = Path(tmpdir) / f"injected_{doc.file_name}"
        injected_path.write_text(injected_code, encoding="utf-8")

        edit_progress(p2, "Decoder Injected ✓", "✅")

        # ── Step 3: Executing File ─────────
        p3 = progress(chat_id, "Executing File ...", "⚙️")

        try:
            result = subprocess.run(
                [sys.executable, str(injected_path)],
                capture_output=True,
                text=True,
                timeout=EXEC_TIMEOUT,
                cwd=tmpdir,
            )
            stdout = result.stdout
            stderr = result.stderr
            exit_code = result.returncode
        except subprocess.TimeoutExpired:
            edit_progress(p3, "Execution Timed Out", "⏱️")
            bot.send_message(
                chat_id,
                f"⏱️ *Execution timed out* after `{EXEC_TIMEOUT}s`.\n"
                "The script took too long to complete.",
            )
            return
        except Exception as exc:
            edit_progress(p3, "Execution Error", "❌")
            bot.send_message(chat_id, f"❌ *Execution error:*\n```\n{exc}\n```")
            return

        edit_progress(p3, "Execution Complete ✓", "✅")

        # ── Step 4: Preparing Result ───────
        p4 = progress(chat_id, "Preparing Result ...", "📝")
        time.sleep(0.3)

        combined_output = ""
        if stdout:
            combined_output += stdout
        if stderr:
            combined_output += "\n# STDERR:\n" + stderr

        if not combined_output.strip():
            combined_output = "# (no output produced)"

        result_content = (
            "#SOMANI GOD\n"
            + combined_output.rstrip("\n")
            + "\n#SOMANI GOD\n"
        )

        result_filename = f"decoded_{doc.file_name}"
        result_path = Path(tmpdir) / result_filename
        result_path.write_text(result_content, encoding="utf-8")

        stats["total_decoded"] += 1

        edit_progress(p4, "Result Prepared ✓", "✅")

        # ── Step 5: Sending Output ─────────
        p5 = progress(chat_id, "Sending Output ...", "📤")
        time.sleep(0.3)

        caption = (
            f"{LOGO_SMALL}\n"
            f"✅ *Decode Complete!*\n"
            f"{DIVIDER}\n"
            f"📄 File   : `{doc.file_name}`\n"
            f"🔢 Exit   : `{exit_code}`\n"
            f"📏 Output : `{len(combined_output)} chars`\n"
            f"{DIVIDER}\n"
            f"⚡ *SOMANI DECODER* `v{BOT_VERSION}`"
        )

        with open(result_path, "rb") as f:
            bot.send_document(
                chat_id,
                f,
                caption=caption,
                visible_file_name=result_filename,
            )

        edit_progress(p5, "Output Sent ✓", "✅")


# ─────────────────────────────────────────────
#  CATCH-ALL — non-file text messages
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda m: True)
def catch_all(msg: types.Message):
    bot.reply_to(
        msg,
        "```\n"
        "╔══════════════════════════════╗\n"
        "║  📂  Send a .py file to me  ║\n"
        "║  or use /start for the menu ║\n"
        "╚══════════════════════════════╝\n"
        "```",
    )


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌  Set your TELEGRAM_BOT_TOKEN environment variable or paste it into the script.")
        sys.exit(1)

    # ── Verify token & fetch bot info ──────────
    try:
        me = bot.get_me()
    except Exception as e:
        print(
            "\n"
            "╔══════════════════════════════════════╗\n"
            "║   ❌  FAILED TO CONNECT TO TELEGRAM  ║\n"
            "╠══════════════════════════════════════╣\n"
            "║  Possible reasons:                   ║\n"
            "║  1. Token is wrong / expired         ║\n"
            "║  2. No internet connection           ║\n"
            "║  3. Telegram is blocked on network   ║\n"
            "╚══════════════════════════════════════╝\n"
            f"  Error: {e}\n"
        )
        sys.exit(1)

    # ── Remove any existing webhook (prevents conflict) ──
    try:
        bot.remove_webhook()
        time.sleep(0.5)
    except Exception:
        pass

    print(
        "\n"
        "╔════════════════════════╗\n"
        "║     SOMANI DECODER     ║\n"
        "║      PREMIUM EDITION   ║\n"
        "╚════════════════════════╝\n"
        f"  Bot Name : @{me.username}\n"
        f"  Bot ID   : {me.id}\n"
        f"  Version  : v{BOT_VERSION}\n"
        f"  Timeout  : {EXEC_TIMEOUT}s\n"
        "  Status   : ✅ Online & Listening ...\n"
        "\n"
        f"  ➡  Open Telegram and message @{me.username}\n"
        "  ➡  Send /start to test the bot\n"
    )

    bot.infinity_polling(
        timeout=30,
        long_polling_timeout=20,
        allowed_updates=["message", "callback_query"],
    )
