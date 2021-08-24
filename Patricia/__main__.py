
import importlib
import time
import re
from sys import argv
from typing import Optional

from innexiaBot import (
    ALLOW_EXCL,
    CERT_PATH,
    DONATION_LINK,
    LOGGER,
    OWNER_ID,
    PORT,
    SUPPORT_CHAT,
    TOKEN,
    URL,
    WEBHOOK,
    SUPPORT_CHAT,
    dispatcher,
    StartTime,
    telethn,
    pbot,
    updater,
)

# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in the config file!
from innexiaBot.modules import ALL_MODULES
from innexiaBot.modules.helper_funcs.chat_status import is_user_admin
from innexiaBot.modules.helper_funcs.misc import paginate_modules
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.error import (
    BadRequest,
    ChatMigrated,
    NetworkError,
    TelegramError,
    TimedOut,
    Unauthorized,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)
from telegram.ext.dispatcher import DispatcherHandlerStop, run_async
from telegram.utils.helpers import escape_markdown


def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time

INNEXIA_IMG = "https://telegra.ph/file/8b6f8f2bb4ff3912634c7.jpg"

PM_START_TEXT = """
`ʜᴇʏ` ɪ ᴀᴍ *ᴩᴀᴛʀɪᴄɪᴀ* ᴀ ᴀɴɪᴍᴇᴅ ɢʀᴏᴜᴩ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ ʙᴏᴛ,
`ɪ ᴩʀᴏᴠɪᴅᴇ ᴏsᴍ ғᴇᴀᴛᴜʀᴇ ᴛʜᴀᴛ ᴀ ɢʀᴏᴜᴩ ᴏᴡɴᴇʀ ᴡɪʟʟ ʟᴏᴏᴋ ғᴏʀ ᴛʜᴇʀᴇ ɢʀᴏᴜᴩs, ᴄʜᴇᴄᴋ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅ ᴅᴇᴀᴛɪʟs ᴜsɪɴɢ `help📚` ʙᴜᴛᴛᴏɴ ᴏʀ ᴊᴜsᴛ sᴇɴᴅ /help !`
"""

buttons = [
    [
        InlineKeyboardButton(
            text="➕ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴩ➕", url="http://t.me/Innexiabot?startgroup=true"),
    ],
    [
        InlineKeyboardButton(text="ᴀʙᴏᴜᴛℹ️", callback_data="innexia_"),
        InlineKeyboardButton(
            text="ʜᴇʟᴩ📚", callback_data="start_help"
        ),
    ],
    [
        InlineKeyboardButton(text="⚙️ᴄᴏɴғɪɢᴜʀᴀᴛɪᴏɴ⚙️", callback_data="config_help" ),
    ],
]


HELP_STRINGS = """
ʜᴇʏ ᴛʜᴇʀᴇ! ᴍʏ ɴᴀᴍᴇ ɪs *ᴩᴀᴛʀɪᴄɪᴀ*.,
ɪ'ᴍ ʜᴇʀᴇ ᴛᴏ ʜᴇʟᴘ ʏᴏᴜ ᴍᴀɴᴀɢᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘs!,
ᴍᴀɪɴ ᴄᴏᴍᴍᴀɴᴅs ᴀᴠᴀɪʟᴀʙʟᴇ :,
- /start: sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ,
- /help: ᴘᴍ's ʏᴏᴜ ᴛʜɪs ᴍᴇssᴀɢᴇ.,
- /settings:,
 • ɪɴ ᴘᴍ: ᴡɪʟʟ sᴇɴᴅ ʏᴏᴜ ʏᴏᴜʀ sᴇᴛᴛɪɴɢs ғᴏʀ ᴀʟʟ sᴜᴘᴘᴏʀᴛᴇᴅ ᴍᴏᴅᴜʟᴇs.,
 • ɪɴ ᴀ ɢʀᴏᴜᴘ: ᴡɪʟʟ ʀᴇᴅɪʀᴇᴄᴛ ʏᴏᴜ ᴛᴏ ᴘᴍ, ᴡɪᴛʜ ᴀʟʟ ᴛʜᴀᴛ ᴄʜᴀᴛ's sᴇᴛᴛɪɴɢs.,
ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴏ ɢᴇᴛ ᴅᴏᴄᴜᴍᴇɴᴛᴀᴛɪᴏɴ ᴀʙᴏᴜᴛ sᴘᴇᴄɪғɪᴄ ᴍᴏᴅᴜʟᴇs!."""



DONATE_STRING = """Heya, glad to hear you want to donate!
 @piroXpower's 💕"""

IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []
CHAT_SETTINGS = {}
USER_SETTINGS = {}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("innexiaBot.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() not in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module


# do not async
def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    dispatcher.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=keyboard,
    )


@run_async
def test(update: Update, context: CallbackContext):
    # pprint(eval(str(update)))
    # update.effective_message.reply_text("Hola tester! _I_ *have* `markdown`", parse_mode=ParseMode.MARKDOWN)
    update.effective_message.reply_text("This person edited a message")
    print(update.effective_message)


@run_async
def start(update: Update, context: CallbackContext):
    args = context.args
    uptime = get_readable_time((time.time() - StartTime))
    if update.effective_chat.type == "private":
        if len(args) >= 1:
            if args[0].lower() == "help":
                send_help(update.effective_chat.id, HELP_STRINGS)
            elif args[0].lower().startswith("ghelp_"):
                mod = args[0].lower().split("_", 1)[1]
                if not HELPABLE.get(mod, False):
                    return
                send_help(
                    update.effective_chat.id,
                    HELPABLE[mod].__help__,
                    InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="⬅️ BACK", callback_data="help_back")]]
                    ),
                )

            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(match.group(1), update.effective_user.id, False)
                else:
                    send_settings(match.group(1), update.effective_user.id, True)

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
            update.effective_message.reply_text(
                PM_START_TEXT,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
            )
    else:
        update.effective_message.reply_photo(
            INNEXIA_IMG, caption= "I'm awake already!\n<b>Haven't slept since:</b> <code>{}</code>".format(
                uptime
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Sᴜᴘᴘᴏʀᴛ", url="t.me/SiderzChat")]]
            ),
        )
        
def error_handler(update, context):
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    LOGGER.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    message = (
        "An exception was raised while handling an update\n"
        "<pre>update = {}</pre>\n\n"
        "<pre>{}</pre>"
    ).format(
        html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False)),
        html.escape(tb),
    )

    if len(message) >= 4096:
        message = message[:4096]
    # Finally, send the message
    context.bot.send_message(chat_id=OWNER_ID, text=message, parse_mode=ParseMode.HTML)


# for test purposes
def error_callback(update: Update, context: CallbackContext):
    error = context.error
    try:
        raise error
    except Unauthorized:
        print("no nono1")
        print(error)
        # remove update.message.chat_id from conversation list
    except BadRequest:
        print("no nono2")
        print("BadRequest caught")
        print(error)

        # handle malformed requests - read more below!
    except TimedOut:
        print("no nono3")
        # handle slow connection problems
    except NetworkError:
        print("no nono4")
        # handle other connection problems
    except ChatMigrated as err:
        print("no nono5")
        print(err)
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        print(error)
        # handle all other telegram related errors


@run_async
def help_button(update, context):
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)

    print(query.message.chat.id)

    try:
        if mod_match:
            module = mod_match.group(1)
            text = (
                "Here is the help for the *{}* module:\n".format(
                    HELPABLE[module].__mod_name__
                )
                + HELPABLE[module].__help__
            )
            query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="Back", callback_data="help_back")]]
                ),
            )

        elif prev_match:
            curr_page = int(prev_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "help")
                ),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "help")
                ),
            )

        elif back_match:
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELPABLE, "help")
                ),
            )

        # ensure no spinny white circle
        context.bot.answer_callback_query(query.id)
        # query.message.delete()

    except BadRequest:
        pass

#---------------------------------------------------ABOUT-------------------------------------------------------
@run_async
def innexia_about_callback(update, context):
    query = update.callback_query
    if query.data == "innexia_":
        query.message.edit_text(
            text="""  ✗ 𝗔𝗕𝗢𝗨𝗧 𝗠𝗘 - A bot to manage your groups with additional features!
            \nHere's the basic help regarding use of PATRICIA.
            
            \nAlmost all modules usage defined in the help menu, checkout by sending `/help`
            \nReport error/bugs click the Button""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="ᴄʀᴇᴅɪᴛs", callback_data="credit_help"
                        ),
                        InlineKeyboardButton(
                            text="sᴜᴩᴩᴏʀᴛ", callback_data="support_help"
                        ),
                    ],[
                        InlineKeyboardButton(
                            text="ᴀᴅᴍɪɴ ʜᴇʟᴩ", callback_data="admin_help"
                        ),
                        InlineKeyboardButton(
                            text="ᴜsᴇʀ ʜᴇʟᴩ", callback_data="user_help"
                        ),
                    ],
                    [InlineKeyboardButton(text="ʙᴀᴄᴋ", callback_data="innexia_back")],
                ]
            ),
        )
    elif query.data == "innexia_back":
        query.message.edit_text(
                PM_START_TEXT,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
        )

    elif query.data == "user_help":
        query.message.edit_text(
            text=f"*ʙᴀsɪᴄ ᴜsᴇʀ ʜᴇʟᴘ*"
            f"\n\n➥ /zip: ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴛᴇʟᴇɢʀᴀᴍ ғɪʟᴇ ᴛᴏ ᴄᴏᴍᴘʀᴇss ɪᴛ ɪɴ .ᴢɪᴘ ғᴏʀᴍᴀᴛ\n"
            f"\n\n➥ /ud <ᴡᴏʀᴅ> ᴛᴏ ᴜsᴇ ᴜʀʙᴀɴ ᴅɪᴄᴛɪᴏɴᴀʀʏ"
            f"\n\n➥ ʀᴇᴘʟʏ ᴛᴏ ᴀ sᴛɪᴄᴋᴇʀ ᴀɴᴅ sᴇɴᴅ /kang <ᴇᴍᴏ> ᴛᴏ ᴀᴅᴅ ᴀ sᴛɪᴄᴋᴇʀ ɪɴ ʏᴏᴜʀ ᴘᴀᴄᴋ"
            f"\n\n➥ /song <sᴏɴɢ ɴᴀᴍᴇ> ᴛᴏ ɢᴇᴛ ᴀ sᴏɴɢ, /lyrics <sᴏɴɢ ɴᴀᴍᴇ> ᴛᴏ ɢᴇᴛ ʟʏʀɪᴄs ᴏғ ᴀ sᴏɴɢ"
            f"\n➥ /img <text>: sᴇᴀʀᴄʜ ɢᴏᴏɢʟᴇ ғᴏʀ ɪᴍᴀɢᴇs ᴀɴᴅ ʀᴇᴛᴜʀɴs ᴛʜᴇᴍғᴏʀ ɢʀᴇᴀᴛᴇʀ ɴᴏ. ᴏғ ʀᴇsᴜʟᴛs sᴘᴇᴄɪғʏ ʟɪᴍ, ғᴏʀ ᴇɢ: /img ʜᴇʟʟᴏ ʟɪᴍ=10",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="ʙᴀᴄᴋ", callback_data="innexia_")]]
            ),
        )
    elif query.data == "admin_help":
        query.message.edit_text(
            text=f"*ʙᴀsɪᴄ ᴀᴅᴍɪɴs ᴄᴏᴍᴍᴀɴᴅ's*"
            f"\n➥ /reload ᴜᴘᴅᴀᴛᴇs ᴛʜᴇ ᴀᴅᴍɪɴs ʟɪsᴛ ᴀɴᴅ ᴛʜᴇɪʀ ᴘʀɪᴠɪʟᴇɢᴇs"
            f"\n\n➥ /settings ʟᴇᴛs ʏᴏᴜ ᴍᴀɴᴀɢᴇ ᴀʟʟ ᴛʜᴇ ʙᴏᴛ sᴇᴛᴛɪɴɢs ɪɴ ᴀ ɢʀᴏᴜᴘ"
            f"\n➥ /ban ʟᴇᴛs ʏᴏᴜ ʙᴀɴ ᴀ ᴜsᴇʀ ғʀᴏᴍ ᴛʜᴇ ɢʀᴏᴜᴘ ᴡɪᴛʜᴏᴜᴛ ɢɪᴠɪɴɢ ʜɪᴍ ᴛʜᴇ ᴘᴏssɪʙɪʟɪᴛʏ ᴛᴏ ᴊᴏɪɴ ᴀɢᴀɪɴ ᴜsɪɴɢ ᴛʜᴇ ʟɪɴᴋ ᴏғ ᴛʜᴇ ɢʀᴏᴜᴘ"
            f"\n➥ /mute ᴘᴜᴛs ᴀ ᴜsᴇʀ ɪɴ ʀᴇᴀᴅ-ᴏɴʟʏ ᴍᴏᴅᴇ. ʜᴇ ᴄᴀɴ ʀᴇᴀᴅ ʙᴜᴛ ʜᴇ ᴄᴀɴ'ᴛ sᴇɴᴅ ᴀɴʏ ᴍᴇssᴀɢᴇs"
            f"\n\n➥ /punch ʙᴀɴs ᴀ ᴜsᴇʀ ғʀᴏᴍ ᴛʜᴇ ɢʀᴏᴜᴘ, ɢɪᴠɪɴɢ ʜɪᴍ ᴛʜᴇ ᴘᴏssɪʙɪʟɪᴛʏ ᴛᴏ ᴊᴏɪɴ ᴀɢᴀɪɴ ᴡɪᴛʜ ᴛʜᴇ ʟɪɴᴋ ᴏғ ᴛʜᴇ ɢʀᴏᴜᴘ
            f"\n➥ /unban ʟᴇᴛs ʏᴏᴜ ʀᴇᴍᴏᴠᴇ ᴀ ᴜsᴇʀ ғʀᴏᴍ ɢʀᴏᴜᴘ's ʙʟᴀᴄᴋʟɪsᴛ, ɢɪᴠɪɴɢ ᴛʜᴇᴍ ᴛʜᴇ ᴘᴏssɪʙɪʟɪᴛʏ ᴛᴏ ᴊᴏɪɴ ᴀɢᴀɪɴ ᴡɪᴛʜ ᴛʜᴇ ʟɪɴᴋ ᴏғ ᴛʜᴇ ɢʀᴏᴜᴘ."
            f"\n➥ /info ɢɪᴠᴇs ɪɴғᴏʀᴍᴀᴛɪᴏɴ ᴀʙᴏᴜᴛ ᴀ ᴜsᴇʀ."
            f"◽️ /admins ɢɪᴠᴇs ᴛʜᴇ ᴄᴏᴍᴘʟᴇᴛᴇ ʟɪsᴛ ᴏғ ɢʀᴏᴜᴘ sᴛᴀғғ.",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="ʙᴀᴄᴋ", callback_data="innexia_")]]
            ),
        )
    elif query.data == "support_help":
        query.message.edit_text(
            text="* Innexia support chats*"
            "\nJoin Support Group/Channel",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="Sᴜᴩᴩᴏʀᴛ", url="t.me/TGBOTSXD"),
                    InlineKeyboardButton(text="Uᴩᴅᴀᴛᴇs", url="t.me/TGBOTZXD"),
                 ],
                 [
                    InlineKeyboardButton(text="Lᴏɢs", url="t.me/PATRICIA_LOGS"),
                    InlineKeyboardButton(text="Cʜᴀᴛ", url="https://t.me/frndsXworld"),
                 ],
                 [
                    InlineKeyboardButton(text="ʙᴀᴄᴋ", callback_data="innexia_"),
                 
                 ]
                ]
            ),
        )
    elif query.data == "credit_help":
        query.message.edit_text(
            text=f"*ᴄʀᴇᴅɪᴛs Fᴏʀ ᴩᴀᴛʀɪᴄɪᴀ*"
            f"◽️ Bᴇʟᴏᴡ Aʀᴇ Tʜᴇ Pʀᴏғɪʟᴇ Uʀʟ Oғ Aʟʟ Dᴇʙ's",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="Bʟᴀᴢᴇ", url="t.me/useIes"),
                    InlineKeyboardButton(text="Sᴀᴍᴍʏ", url="t.me/useIes"),
                 ],
                 [
                    InlineKeyboardButton(text="Dᴇᴠɪʟ", url="t.me/DEVILDAD_PRINCE"),
                    InlineKeyboardButton(text="Tᴀɴᴀᴊɪ", url="https://t.me/XD_PERSON"),
                 ],
                 [
                    InlineKeyboardButton(text="ʙᴀᴄᴋ", callback_data="innexia_"),
                 
                 ]
                ]
            ),
        )
#----------------------------------------------------------------------CONFIGURATION------------------------------------------------------------------------------------------------------------------------------------------
    elif query.data == "config_help":
        query.message.edit_text(
            text=f"*ʜᴇʏ ᴛʜᴇʀᴇ, ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ  ᴄᴏɴғɪɢᴜʀᴀᴛɪᴏɴ ᴛᴜᴛᴏʀɪᴀʟ.*"
            f"\n\nᴛʜᴇ ғɪʀsᴛ ᴛʜɪɴɢ ᴛᴏ ᴅᴏ ɪs ᴛᴏ ᴀᴅᴅ *ᴩᴀᴛʀɪᴄɪᴀ* ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ! ғᴏʀ ᴅᴏɪɴɢ ᴛʜᴀᴛ, ᴘʀᴇss ᴛʜᴇ ᴜɴᴅᴇʀ ʙᴜᴛᴛᴏɴ ᴀɴᴅ sᴇʟᴇᴄᴛ ʏᴏᴜʀ ɢʀᴏᴜᴘ.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                   InlineKeyboardButton(
                            text="ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴩ", url="http://t.me/PATRICIA_ROBOT?startgroup=true"
                            ),
                 ],
                 [
                   InlineKeyboardButton(
                            text="ɴᴇxᴛ", callback_data="config_first"
                            ),
                 ],
                ]
            ),
        )
    elif query.data == "config_first":
        query.message.edit_text(
            text=f"*ʜᴇʏ ᴛʜᴇʀᴇ, ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ  ᴄᴏɴғɪɢᴜʀᴀᴛɪᴏɴ ᴛᴜᴛᴏʀɪᴀʟ.*"
            f"\n\nɴᴏᴡ ғᴏʀ ʟᴇᴛ ᴍᴇ ᴡᴏʀᴋ ᴄᴏʀʀᴇᴄᴛʟʏ, ʏᴏᴜ ɴᴇᴇᴅ ᴛᴏ ᴍᴀᴋᴇ ᴍᴇ ᴀᴅᴍɪɴ ᴏғ ʏᴏᴜʀ ɢʀᴏᴜᴘ!"
            f"\n ᴛᴏ ᴅᴏ ᴛʜᴀᴛ, ғᴏʟʟᴏᴡ ᴛʜɪs ᴇᴀsʏ sᴛᴇᴘs:"
            f"\n▫️ ɢᴏ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ"
            f"\n▫️ ᴘʀᴇss ᴛʜᴇ ɢʀᴏᴜᴘ's ɴᴀᴍᴇ"
            f"\n▫️ ᴘʀᴇss ᴍᴏᴅɪғʏ"
            f"\n▫️ ᴘʀᴇss ᴏɴ ᴀᴅᴍɪɴɪsᴛʀᴀᴛᴏʀ"
            f"\n▫️ ᴘʀᴇss ᴀᴅᴅ ᴀᴅᴍɪɴɪsᴛʀᴀᴛᴏʀ"
            f"\n▫️ ᴘʀᴇss ᴛʜᴇ ᴍᴀɢɴɪғʏɪɴɢ ɢʟᴀss"
            f"\n▫️ sᴇᴀʀᴄʜ @PATRICIA_ROBOT"
            f"\n▫️ ᴄᴏɴғɪʀᴍ",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="ɴᴇxᴛ", callback_data="config_second")]]
            ),
        )
    elif query.data == "config_second":
        query.message.edit_text(
            text=f"*ᴇxᴄᴇʟʟᴇɴᴛ!*"
            f"\n\nɴᴏᴡ ᴛʜᴇ ʙᴏᴛ ɪs ʀᴇᴀᴅʏ ᴛᴏ ᴜsᴇ!"
            f"\n\n*Note:* ɪɴ ᴄᴏɴᴄʟᴜsɪᴏɴ ɪ ᴡᴏᴜʟᴅ ᴘᴏɪɴᴛ ᴏᴜᴛ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ /reload ᴛʜᴀᴛ ᴡɪʟʟ ᴜᴘᴅᴀᴛᴇ ᴛʜᴇ ɢʀᴏᴜᴘ's ᴀᴅᴍɪɴ ʟɪsᴛ."
            f"\nғᴏʀ ᴇxᴀᴍᴘʟᴇ ɪғ ʏᴏᴜ ᴀᴅᴅ ᴏʀ ʀᴇᴍᴏᴠᴇ ᴀɴ ᴀᴅᴍɪɴ, ʀᴇᴍᴇᴍʙᴇʀ ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴏʀ ᴛʜᴇ ʙᴏᴛ ᴡɪʟʟ ɴᴏᴛ ɴᴏᴛɪᴄᴇ ᴛʜɪs ᴄʜᴀɴɢᴇ ғᴏʀ 4-5min.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="ɴᴇxᴛ", callback_data="start_help")]]
            ),
        ) 
    
        
        
@run_async
def Source_about_callback(update, context):
    query = update.callback_query
    if query.data == "source_":
        query.message.edit_text(
            text=""" Hi..😻 I'm *Innexia*
                 \nHere is the [🔥Source Code🔥](https://github.com/TEAM-PATRICIA) .""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="Go Back", callback_data="source_back")
                 ]
                ]
            ),
        )
    elif query.data == "source_back":
        query.message.edit_text(
                PM_START_TEXT,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
        )

@run_async
def get_help(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:
        if len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
            module = args[1].lower()
            update.effective_message.reply_text(
                f"Contact me in PM to get help of {module.capitalize()}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Help",
                                url="t.me/{}?start=ghelp_{}".format(
                                    context.bot.username, module
                                ),
                            )
                        ]
                    ]
                ),
            )
            return
        update.effective_message.reply_text(
            "Contact me in PM to get the list of possible commands.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Hᴇʟᴘ ❔",
                            url="t.me/{}?start=help".format(context.bot.username),
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="Sᴜᴘᴘᴏʀᴛ Cʜᴀᴛ 📢 ",
                            url="https://t.me/{}".format(SUPPORT_CHAT),
                        )
                    ],
                ]
            ),
        )
        return

    elif len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        text = (
            "Here is the available help for the *{}* module:\n".format(
                HELPABLE[module].__mod_name__
            )
            + HELPABLE[module].__help__
        )
        send_help(
            chat.id,
            text,
            InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="help_back")]]
            ),
        )

    else:
        send_help(chat.id, HELP_STRINGS)


def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                "*{}*:\n{}".format(mod.__mod_name__, mod.__user_settings__(user_id))
                for mod in USER_SETTINGS.values()
            )
            dispatcher.bot.send_message(
                user_id,
                "These are your current settings:" + "\n\n" + settings,
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any user specific settings available :'(",
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        if CHAT_SETTINGS:
            chat_name = dispatcher.bot.getChat(chat_id).title
            dispatcher.bot.send_message(
                user_id,
                text="Which module would you like to check {}'s settings for?".format(
                    chat_name
                ),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )
        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any chat settings available :'(\nSend this "
                "in a group chat you're admin in to find its current settings!",
                parse_mode=ParseMode.MARKDOWN,
            )


@run_async
def settings_button(update: Update, context: CallbackContext):
    query = update.callback_query
    user = update.effective_user
    bot = context.bot
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = bot.get_chat(chat_id)
            text = "*{}* has the following settings for the *{}* module:\n\n".format(
                escape_markdown(chat.title), CHAT_SETTINGS[module].__mod_name__
            ) + CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id)
            query.message.reply_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Back",
                                callback_data="stngs_back({})".format(chat_id),
                            )
                        ]
                    ]
                ),
            )

        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        curr_page - 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        next_page + 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif back_match:
            chat_id = back_match.group(1)
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                text="Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(escape_markdown(chat.title)),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )

        # ensure no spinny white circle
        bot.answer_callback_query(query.id)
        query.message.delete()
    except BadRequest as excp:
        if excp.message not in [
            "Message is not modified",
            "Query_id_invalid",
            "Message can't be deleted",
        ]:
            LOGGER.exception("Exception in settings buttons. %s", str(query.data))


@run_async
def get_settings(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    # ONLY send settings in PM
    if chat.type != chat.PRIVATE:
        if is_user_admin(chat, user.id):
            text = "Click here to get this chat's settings, as well as yours."
            msg.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Settings",
                                url="t.me/{}?start=stngs_{}".format(
                                    context.bot.username, chat.id
                                ),
                            )
                        ]
                    ]
                ),
            )
        else:
            text = "Click here to check your settings."

    else:
        send_settings(chat.id, user.id, True)


@run_async
def donate(update: Update, context: CallbackContext):
    user = update.effective_message.from_user
    chat = update.effective_chat  # type: Optional[Chat]
    bot = context.bot
    if chat.type == "private":
        update.effective_message.reply_text(
            DONATE_STRING, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )

        if OWNER_ID != 1947924017 and DONATION_LINK:
            update.effective_message.reply_text(
                "You can also donate to the person currently running me "
                "[here]({})".format(DONATION_LINK),
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        try:
            bot.send_message(
                user.id,
                DONATE_STRING,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )

            update.effective_message.reply_text(
                "I've PM'ed you about donating to my creator!"
            )
        except Unauthorized:
            update.effective_message.reply_text(
                "Contact me in PM first to get donation information."
            )


def migrate_chats(update: Update, context: CallbackContext):
    msg = update.effective_message  # type: Optional[Message]
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info("Migrating from %s, to %s", str(old_chat), str(new_chat))
    for mod in MIGRATEABLE:
        mod.__migrate__(old_chat, new_chat)

    LOGGER.info("Successfully migrated!")
    raise DispatcherHandlerStop


def main():

    if SUPPORT_CHAT is not None and isinstance(SUPPORT_CHAT, str):
        try:
            dispatcher.bot.sendMessage(f"@{SUPPORT_CHAT}", "I Aᴍ Aʟɪᴠᴇ 🔥")
        except Unauthorized:
            LOGGER.warning(
                "Bot isnt able to send message to support_chat, go and check!"
            )
        except BadRequest as e:
            LOGGER.warning(e.message)

    test_handler = CommandHandler("test", test)
    start_handler = CommandHandler("start", start)

    help_handler = CommandHandler("help", get_help)
    help_callback_handler = CallbackQueryHandler(help_button, pattern=r"help_.*")

    settings_handler = CommandHandler("settings", get_settings)
    settings_callback_handler = CallbackQueryHandler(settings_button, pattern=r"stngs_")

    about_callback_handler = CallbackQueryHandler(innexia_about_callback, pattern=r"innexia_")
    source_callback_handler = CallbackQueryHandler(Source_about_callback, pattern=r"source_")

    donate_handler = CommandHandler("donate", donate)
    migrate_handler = MessageHandler(Filters.status_update.migrate, migrate_chats)

    # dispatcher.add_handler(test_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(about_callback_handler)
    dispatcher.add_handler(source_callback_handler)
    dispatcher.add_handler(settings_handler)
    dispatcher.add_handler(help_callback_handler)
    dispatcher.add_handler(settings_callback_handler)
    dispatcher.add_handler(migrate_handler)
    dispatcher.add_handler(donate_handler)

    dispatcher.add_error_handler(error_callback)

    if WEBHOOK:
        LOGGER.info("Using webhooks.")
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)

        if CERT_PATH:
            updater.bot.set_webhook(url=URL + TOKEN, certificate=open(CERT_PATH, "rb"))
        else:
            updater.bot.set_webhook(url=URL + TOKEN)

    else:
        LOGGER.info("Using long polling.")
        updater.start_polling(timeout=15, read_latency=4, clean=True)

    if len(argv) not in (1, 3, 4):
        telethn.disconnect()
    else:
        telethn.run_until_disconnected()

    updater.idle()


if __name__ == "__main__":
    LOGGER.info("Successfully loaded modules: " + str(ALL_MODULES))
    telethn.start(bot_token=TOKEN)
    pbot.start()
    main()
