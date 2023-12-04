import os
from dotenv import load_dotenv

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters
)

import logging
from random import randint

from __db__.index import connect_db, get_user, set_user, update_user, get_game, set_game, update_game
from __api__.index import balanceOf, transfer

logging.basicConfig(format="%(asctime)s -%(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
load_dotenv()

START, END = range(2)

MONGO_URI = os.getenv("MONGO_URI")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADDRESS="0xBD926935AB9EE431fB490AAe7A2d63eC2787a574"

db = None

def random_id() -> int:
    random_num = "".join([str(randint(0, 9)) for _ in range(10)])

    return int(random_num)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        user = update.message.from_user
        logger.info(f"{user.username} started a conversation.")

        if update.message.chat.type == "private":
            _user = get_user(db=db, query={"username" : user.username})

            if not _user:
                context.user_data["username"] = user.username

                user_ = set_user(db=db, value={"userId" : user.id, "username" : user.username, "balance" : 0, "address" : "0x0"})
                print(user_)

                keyboard = [
                    [InlineKeyboardButton("Set your ERC20 Address 🚀", callback_data="set")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                reply_msg = f"<b>Hello {user.username} 🎉, Welcome to the KingdomBot 🤖,</b>\n\n<i>🚫 Your address is not set and you are not able to play. Change your address with the command : /set 'your_erc20_address'</i>\n\n<b>By using our bot and playing, you agree to our terms of usage, available at:</b>\n<i><a href='https://docs.kingdomgame.live/legal'>🔰 Kingdom Game</a></i>"

                await update.message.reply_html(text=reply_msg, reply_markup=reply_markup)
            else:
                reply_msg = f"<b>Hello {user.username} 🎉, Welcome to the KingdomBot 🤖,</b>\n\n<i>✅ Your wallet address is well set to: <b>{_user['address']}.</b></i>\n\n<i>🔰 To fund your play wallet, do /fund __amount__</i>\n\n<i>🔰 To change address, do /set your_ERC20_address</i>\n\n<i>🔰 To withdraw your points/tokens, do /withdraw __amount__</i>\n\n<i>🔰 To check your balance, do /balance</i>\n\n<i>🔰 To get referral link, do /get_referral_link. <b>🚨 Get 2% of your referrals points forever. Every referral get free 25 points ie: 5 free runs.</b></i>\n\n<b>By using our bot and playing, you agree to our terms of usage, available at:</b>\n<i><a href='https://docs.kingdomgame.live/legal'>🔰 Kingdom Game</a></i>"
                await update.message.reply_html(text=reply_msg)
            
            return START
        else:
            reply_msg = "<b>🚨 This command is not used in groups</b>"
            await update.message.reply_html(text=reply_msg)

            return -1
    except Exception as e:
        print(e)
        logging.error("An error occured while processing this command.")

        reply_msg = f"<b>🚨 {user.username} An error occured while processing your request.</b>"
        await update.message.reply_html(text=reply_msg)

async def set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.message.from_user
        logger.info(f"{user.username} has set an ERC20 address.")

        if update.message.chat.type == "private":
            address = context.args
            _user = get_user(db=db, query={"username" : user.username})

            if not _user:
                context.user_data["username"] = user.username

                _user = set_user(db=db, value={"userId" : user.id, "username" : user.username, "balance" : 0, "address" : "0x0"})
                print(_user)
            
            if address:
                context.user_data["address"] = address[0]

                _user = update_user(db=db, query={"userId" : user.id}, value={"$set" :{"address" : address[0]}})
                print(_user)

                reply_msg = f"<b>Congratulations {user.username} 🎉, Your address is succesfully set to {address[0]} ✅.</b>"
                await update.message.reply_html(text=reply_msg)
            else:
                reply_msg = f"<b>Enter your ERC20 address.</b>\n\n<i>🔰 Use the following format:\n/set 'your_ERC20_address'</i>\n\n<i>🚨 Please ensure that you provide the correct address for the appropriate blockchain.</i>"
                await update.message.reply_html(text=reply_msg)
        else:
            reply_msg = "<b>🚨 This command is not used in groups</b>"
            await update.message.reply_html(text=reply_msg)
    except Exception as e:
        print(e)
        logging.error("An error occured while processing this command.")

        reply_msg = f"<b>🚨 {user.username} An error occured while processing your request.</b>"
        await update.message.reply_html(text=reply_msg)

async def _set(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        query = update.callback_query
        await query.answer()

        username = context.user_data["username"]
        logger.info(f"{username} wants to set an ERC20 address.")

        reply_msg = f"<b>Enter your ERC20 address.</b>\n\n<i>🚨 Please ensure that you provide the correct address for the approipate blockchain.</i>"
        await query.message.reply_html(text=reply_msg)

        return START
    except Exception as e:
        print(e)
        logging.error("An error occured while processing this command.")

        reply_msg = f"<b>🚨 {username}, An error occured while processing your request.</b>"
        await update.message.reply_html(text=reply_msg)

async def setMsg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        username = context.user_data["username"]
        logger.info(f"{username} has set an ERC20 address.")

        context.user_data["address"] = update.message.text.strip()

        _user = update_user(db=db, query={"username" : username}, value={"$set" : {"address" : update.message.text.strip()}})
        print(_user)

        keyboard = [
            [InlineKeyboardButton("End Conversation 👋", callback_data="end")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        reply_msg = f"<b>Congratulations {username} 🎉, Your address is successfully set to {update.message.text.strip()} ✅.</b>"

        await update.message.reply_html(text=reply_msg, reply_markup=reply_markup)

        return START
    except Exception as e:
        print(e)
        logging.error("An error occured while processing this command.")

        reply_msg = f"<b>🚨 {username}, An error occured while processing your request.</b>"
        await update.message.reply_html(text=reply_msg)

async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        query = update.callback_query
        await query.answer()

        username = context.user_data["username"]
        logger.info(f"{username} ended the conversation.")

        reply_msg = f"<b>See you soon {username} 👋.</b>"

        await query.message.reply_html(reply_msg)

        return END
    except Exception as e:
        print(e)
        logging.error("An error occured while processing this command.")

        reply_msg = f"<b>🚨 {username}, An error occured while processing your request.</b>"
        await update.message.reply_html(text=reply_msg)

async def create_battle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.message.from_user
        logger.info(f"{user.username} created a battle.")

        if update.message.chat.type == "group":
            args = context.args
            id = f"EMP-{random_id()}"
            _user = get_user(db=db, query={"username" : user.username})

            if not _user:
                reply_msg = "<b>🚨 You cannot use this command. You have to set your address and fund your play wallet before using this command</b>"
                await update.message.reply_html(text=reply_msg)

            if len(args) == 2:
                if int(args[0]) > 3 or int(args[0]) < 1:
                    reply_msg = "<b>🚨 Maximum duration for battles is 3 minutes while the minimum duration for battles is 1 minute</b>"
                    await update.message.reply_html(text=reply_msg)
                else:
                    if int(args[1]) > 5:
                        reply_msg = "<b>🚨 Maximum number of tanks to be deployed for battles is 5</b>"
                        await update.message.reply_html(text=reply_msg)
                    else:
                        if int(_user["balance"]) >= (1000 * int(args[1])):
                            user_ = update_user(db=db, query={"userId" : user.id}, value={"$inc" :{"balance" : -(1000 * int(args[1]))}})
                            print(user_)

                            game = set_game(db=db, value={"stake" : 1000 * int(args[1]), "gameId" : id, "duration" : int(args[0]), "state" : "Inactive", "players" : [{ "userId" : _user["userId"], "username" : user.username, "tanks" : int(args[1]) }]})
                            print(game)

                            reply_msg = f"<b>Congratulations {user.username} 🎉, Your battle have been successfully created a battle with the ID : {id} ✅.</b>\n\n<i>🔰 The duration of the battle is {args[0]} minute(s)</i>\n\n<i>🔰 {user.username} have deployed {args[1]} Tanks</i>\n\n<i>🔰 To join the battle use the command, /join_battle 'Battle_ID' 'Tanks'</i>"
                            await update.message.reply_html(text=reply_msg)
                        else:
                            reply_msg = "<b>🚨 Insufficent balance to create the battle.</b>"
                            await update.message.reply_html(text=reply_msg)
            else:
                reply_msg = f"<b>🚨 Use the command appropriately.</b>\n\n<i>🔰 Use the following format:\n/create_battle 'duration' 'Tanks'</i>"
                await update.message.reply_html(text=reply_msg)
        else:
            reply_msg = "<b>🚨 This command is only used in groups</b>"
            await update.message.reply_html(text=reply_msg)
    except Exception as e:
        print(e)
        logging.error("An error occured while processing this command.")

        reply_msg = f"<b>🚨 {user.username}, An error occured while processing your request.</b>"
        await update.message.reply_html(text=reply_msg)

async def join_battle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.message.from_user
        logger.info(f"{user.username} joined a battle.")

        if update.message.chat.type == "group":
            args = context.args
            _user = get_user(db=db, query={"username" : user.username})
            _game = get_game(db=db, query={"gameId" : args[0]})

            if not _user:
                reply_msg = "<b>🚨 You cannot use this command. You have to set your address and fund your play wallet before using this command</b>"
                await update.message.reply_html(text=reply_msg)

            if len(args) == 2:
                if _game["state"] == "Active" and len(_game["players"]) <= 4:
                    reply_msg = "<b>🚨 This battle is already Active</b>\n\n<i>🔰 To create a battle use the command, /create_battle 'duration' 'Active_Tanks' 'Reserve_Tanks'</i>"
                    await update.message.reply_html(text=reply_msg)
                else:
                    if _game["players"][0]["userId"] == user.id:
                        reply_msg = f"<b>🚨 {user.username} cannot join this battle</b>"
                        await update.message.reply_html(text=reply_msg)
                    else:
                        if int(args[1]) > 5:
                            reply_msg = "<b>🚨 Maximum number of tanks to be deployed for battles is 5</b>"
                            await update.message.reply_html(text=reply_msg)
                        else:
                            if int(_user["balance"]) >= (1000 * int(args[1])):
                                user_ = update_user(db=db, query={"userId" : user.id}, value={"$inc" :{"balance" : -(1000 * int(args[1]))}})
                                print(user_)

                                game = update_game(db=db, query={ "gameId" : args[0] }, value={"$push" : {"players" : {"userId" : _user["userId"], "username" : user.username, "tanks" : int(args[1])}}, "$inc" : {"stake" : 1000 * int(args[1])}})
                                print(game)

                                reply_msg = f"<b>Congratulations {user.username} 🎉, Your battle have been successfully joined the battle with the ID : {_game['gameId']} ✅.</b>\n\n<i>🔰 The duration of the battle is {_game['duration']} minute(s)</i>\n\n<i>🔰 {user.username} have deployed {args[1]} Tanks</i>\n\n<i>🔰 To create a battle use the command, /create_battle 'duration' 'Tanks'</i>"
                                await update.message.reply_html(text=reply_msg)
                            else:
                                reply_msg = "<b>🚨 Insufficent balance to join the battle.</b>"
                                await update.message.reply_html(text=reply_msg)
            else:
                reply_msg = f"<b>🚨 Use the command appropriately.</b>\n\n<i>🔰 Use the following format:\n/join_battle 'Battle_ID' 'Tanks'</i>"
                await update.message.reply_html(text=reply_msg)
        else:
            reply_msg = "<b>🚨 This command is only used in groups</b>"
            await update.message.reply_html(text=reply_msg)
    except Exception as e:
        print(e)
        logging.error("An error occured while processing this command.")

        reply_msg = f"<b>🚨 {user.username}, An error occured while processing your request.</b>"
        await update.message.reply_html(text=reply_msg)

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.message.from_user
        logger.info(f"{user.username} created a referral link.")

        if update.message.chat.type == "private":
            _user = get_user(db=db, query={"username" : user.username})

            if not _user:
                reply_msg = "<b>🚨 You cannot use this command. You have to set your address before using this command</b>"
                await update.message.reply_html(text=reply_msg)
            else:
                if hasattr(_user, "referral_link"):
                    referral_link = _user["referral_link"]

                    reply_msg = f"<b>🔰 Your referral link is {referral_link} ✅.</b>"
                    await update.message.reply_html(text=reply_msg)
                else:
                    id = random_id()
                    referral_link = f"https://t.me/empire_pvp_game_bot/emp-{id}"

                    _user = update_user(db=db, query={"userId" : user.id}, value={"$set" :{"referral_link" : referral_link}})
                    print(_user)

                    reply_msg = f"<b>🔰 Your referral link is {referral_link} ✅.</b>"
                    await update.message.reply_html(text=reply_msg)
        else:
            reply_msg = "<b>🚨 This command is not used in groups</b>"
            await update.message.reply_html(text=reply_msg)
    except Exception as e:
        print(e)
        logging.error("An error occured while processing this command.")

        reply_msg = f"<b>🚨 {user.username}, An error occured while processing your request.</b>"
        await update.message.reply_html(text=reply_msg)

async def fund(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.message.from_user
        logger.info(f"{user.username} funded a play wallet.")

        if update.message.chat.type == "private":
            _user = get_user(db=db, query={"username" : user.username})

            if not _user:
                reply_msg = "<b>🚨 You cannot use this command. You have to set your address before using this command</b>"
                await update.message.reply_html(text=reply_msg)
            else:
                args = context.args

                if len(args) == 1:
                    _balance = balanceOf(_user["address"])
                    print(_balance)

                    if float(_balance["_balance"]) > int(args[0]):
                        _transfer = transfer(_user["address"], ADDRESS, int(args[0]))
                        print(_transfer)

                        user_ = update_user(db=db, query={"userId" : user.id}, value={"$inc" :{"balance" : int(args[0])}})
                        print(user_)

                        reply_msg = f"<b>🔰 Funded your play wallet with {args[0]}$EMP. Your balance is {int(_user["balance"]) + int(args[0])}$EMP ✅.</b>"
                        await update.message.reply_html(text=reply_msg)
                    else:
                        reply_msg = "<b>🚨 Insufficent balance to complete the transaction.</b>"
                        await update.message.reply_html(text=reply_msg)
                else:
                    reply_msg = f"<b>🚨 Use the command appropriately.</b>\n\n<i>🔰 Use the following format:\n/fund 'amount'</i>"
                    await update.message.reply_html(text=reply_msg)
        else:
            reply_msg = "<b>🚨 This command is not used in groups</b>"
            await update.message.reply_html(text=reply_msg)
    except Exception as e:
        print(e)
        logging.error("An error occured while processing this command.")

        reply_msg = f"<b>🚨 {user.username}, An error occured while processing your request.</b>"
        await update.message.reply_html(text=reply_msg)

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.message.from_user
        logger.info(f"{user.username} withdrew from play wallet.")

        if update.message.chat.type == "private":
            _user = get_user(db=db, query={"username" : user.username})

            if not _user:
                reply_msg = "<b>🚨 You cannot use this command. You have to set your address before using this command</b>"
                await update.message.reply_html(text=reply_msg)
            else:
                args = context.args

                if len(args) == 1:
                    if _user["balance"] >= int(args[0]):
                        _transfer = transfer(ADDRESS, _user["address"], int(args[0]))
                        print(_transfer)

                        user_ = update_user(db=db, query={"userId" : user.id}, value={"$inc" :{"balance" : -int(args[0])}})
                        print(user_)

                        reply_msg = f"<b>🔰 Withdrawl of {args[0]}$EMP from your play wallet. Your balance is {int(_user["balance"]) - int(args[0])}$EMP ✅.</b>"
                        await update.message.reply_html(text=reply_msg)
                    else:
                        reply_msg = "<b>🚨 Insufficent balance to complete the transaction.</b>"
                        await update.message.reply_html(text=reply_msg)
                else:
                    reply_msg = f"<b>🚨 Use the command appropriately.</b>\n\n<i>🔰 Use the following format:\n/fund 'amount'</i>"
                    await update.message.reply_html(text=reply_msg)
        else:
            reply_msg = "<b>🚨 This command is not used in groups</b>"
            await update.message.reply_html(text=reply_msg)
    except Exception as e:
        print(e)
        logging.error("An error occured while processing this command.")

        reply_msg = f"<b>🚨 {user.username}, An error occured while processing your request.</b>"
        await update.message.reply_html(text=reply_msg)

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.message.from_user
        logger.info(f"{user.username} checked balance.")

        if update.message.chat.type == "private":
            _user = get_user(db=db, query={"username" : user.username})

            if not _user:
                reply_msg = "<b>🚨 You cannot use this command. You have to set your address before using this command</b>"
                await update.message.reply_html(text=reply_msg)
            else:
                _balance = balanceOf(_user["address"])
                wallet = _user["balance"]
                print(_balance, wallet)

                reply_msg = f"<b>🔰 Your wallet balance is {_balance["_balance"]}$EMP. Your available play wallet balance is {wallet}$EMP ✅.</b>"
                await update.message.reply_html(text=reply_msg)
        else:
            reply_msg = "<b>🚨 This command is not used in groups</b>"
            await update.message.reply_html(text=reply_msg)
    except Exception as e:
        print(e)
        logging.error("An error occured while processing this command.")

        reply_msg = f"<b>🚨 {user.username}, An error occured while processing your request.</b>"
        await update.message.reply_html(text=reply_msg)

def main() -> None:
    global db
    db = connect_db(uri=MONGO_URI)

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START: [
                CommandHandler("start", start),
                CallbackQueryHandler(_set, pattern="^set$"),
                MessageHandler(filters.Regex("^0x"), setMsg)
            ],
            END: [
                CallbackQueryHandler(end, pattern="^end$")
            ]
        },
        fallbacks=[CallbackQueryHandler(end, pattern="^end$")]
    )
    start_handler = CommandHandler("start", start)
    set_handler = CommandHandler("set", set)
    create_battle_handler = CommandHandler("create_battle", create_battle)
    join_battle_handler = CommandHandler("join_battle", join_battle)
    referral_handler = CommandHandler("get_referral_link", referral)
    fund_handler = CommandHandler("fund", fund)
    balance_handler = CommandHandler("balance", balance)
    withdraw_handler = CommandHandler("withdraw", withdraw)

    app.add_handler(conv_handler)
    app.add_handler(start_handler)
    app.add_handler(set_handler)
    app.add_handler(create_battle_handler)
    app.add_handler(join_battle_handler)
    app.add_handler(referral_handler)
    app.add_handler(fund_handler)
    app.add_handler(balance_handler)
    app.add_handler(withdraw_handler)

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()