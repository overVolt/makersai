from telepot import Bot
from time import time, sleep
import sched
from threading import Thread
from json import load as jsload
from os.path import abspath, dirname, join
from random import randint, uniform
from datetime import datetime
from textgenrnn import textgenrnn
from pony.orm import db_session, select, commit
from modules.database import User, Data

with open(join(dirname(abspath(__file__)), "settings.json")) as settings_file:
    settings = jsload(settings_file)

bot = Bot(settings["token"])
groupId = int(settings["groupId"])
sch = sched.scheduler(time, sleep)

aiConfigPath = join(dirname(abspath(__file__)), "weights", settings['aiModelName'])
ai = textgenrnn(weights_path=f"{aiConfigPath}_weights.hdf5",
                vocab_path=f"{aiConfigPath}_vocab.json",
                config_path=f"{aiConfigPath}_config.json")


def generateText():
    gen = ai.generate(
        n=1,
        return_as_list=True,
        temperature=[round(uniform(0.3, 0.9), 1)],
        max_gen_length=160,
        progress=False
    )[0].strip("\"'/\\ <>") # ", ', /, \, <space>, <, >
    return gen


@db_session
def sendText(chatId: int=groupId, replyId: int=None, userId: int=None):
    if not userId:
        bot.sendChatAction(chatId, "typing")
        bot.sendMessage(chatId, generateText(), reply_to_message_id=replyId)
    else:
        user = User.get(chatId=userId)
        if user.remainingCalls > 0:
            user.remainingCalls -= 1
            commit()
            bot.sendChatAction(chatId, "typing")
            bot.sendMessage(chatId, generateText(), reply_to_message_id=replyId)
            if user.remainingCalls == 0:
                sch.enter(settings["callsResetCooldown"], 5, resetCalls, argument=(userId,))
        else:
            sent = bot.sendMessage(chatId, "Hai superato gli utilizzi massimi del bot. "
                                           "Aspetta un po' prima di usarmi di nuovo.", reply_to_message_id=replyId)
            sleep(5)
            bot.deleteMessage((chatId, sent["message_id"]))


@db_session
def reloadAdmins(chatId: int=groupId):
    req = bot.getChatAdministrators(chatId)
    adminList = [int(user["user"]["id"]) for user in req if not user["user"]["is_bot"]]
    newAdmins = select(u for u in User if u.chatId in adminList)[:]
    for adm in newAdmins:
        adm.isAdmin = True


@db_session
def resetCalls(userId: int=None):
    if not userId:
        pendingUsers = select(u for u in User if u.remainingCalls < 3)[:]
        for user in pendingUsers:
            user.remainingCalls = 3
    else:
        user = User.get(chatId=userId)
        user.remainingCalls = 3


@db_session
def reply(msg):
    chatId = int(msg['chat']['id'])
    fromId = int(msg['from']['id'])
    msgId = int(msg['message_id'])
    chatInfo = bot.getChat(chatId)

    replyTrigger = False
    if "reply_to_message" in msg:
        if "username" in msg["reply_to_message"]["from"]:
            replyTrigger = msg["reply_to_message"]["from"].get("username") == "makersitabot"

    if "text" in msg:
        text = msg['text']
    elif "caption" in msg:
        text = msg['caption']
    else:
        text = ""

    # Strip self-username from commands
    if text.startswith("/"):
        text = text.replace("@makersitabot", "")
        try:
            bot.deleteMessage((chatId, msgId))
        except:
            pass

    ## CHAT PRIVATE
    if chatInfo["type"] == "private":
        bot.sendMessage(chatId, "Sorry, but I only work in the <a href=\"t.me/MakersITA\">MakersITA</a> group.",
                        parse_mode="HTML", disable_web_page_preview=True)

    ## GRUPPI/SUPERGRUPPI
    elif chatInfo["type"] in ["group", "supergroup"]:
        if chatId != groupId: # Only respond to selected group
            bot.sendMessage(chatId, "Sorry, but I only work in the <a href=\"t.me/MakersITA\">MakersITA</a> group.",
                            parse_mode="HTML", disable_web_page_preview=True)
            bot.leaveChat(chatId)
            return

        if not User.exists(lambda u: u.chatId == chatId):
            User(chatId=fromId)
        if not Data.exists(lambda d: d.id == 0):
            Data()
        user = User.get(chatId=fromId)
        data = Data.get(id=0)

        if text.lower() == "ping":
            if randint(1, 3) == 1:
                bot.sendMessage(chatId, "pong", reply_to_message_id=msgId)
        
        elif text.lower() == "over":
            if randint(1, 3) == 1:
                bot.sendMessage(chatId, "Volt!", reply_to_message_id=msgId)
        
        elif text.lower() == "no u":
            if randint(1, 3) == 1:
                bot.sendMessage(chatId, "no u", reply_to_message_id=msgId)

        elif text.lower().endswith("cose"):
            if randint(1, 3) == 1:
                bot.sendMessage(chatId, "varie", reply_to_message_id=msgId)

        elif ("cose diverse" in text.lower()) or ("cose strane" in text.lower()):
            if randint(1, 3) == 1:
                bot.sendMessage(chatId, "cose varie*", reply_to_message_id=msgId)

        elif text.startswith("/pronuncia ") and user.isAdmin:
            replyId = msg["reply_to_message"]["message_id"] if "reply_to_message" in msg else None
            bot.sendMessage(chatId, text.split(" ", 1)[1], parse_mode="HTML",
                            disable_web_page_preview=True, reply_to_message_id=replyId)

        elif text == "/bloccagen" and user.isAdmin:
            if not data.genLocked:
                data.genLocked = True
                bot.sendMessage(chatId, "Comando /genera bloccato!")

        elif text == "/sbloccagen" and user.isAdmin:
            if data.genLocked:
                data.genLocked = False
                bot.sendMessage(chatId, "Comando /genera sbloccato!")

        elif text == "/reload" and user.isAdmin:
            reloadAdmins()
            resetCalls()
            data.genLocked = False
            bot.sendMessage(chatId, "✅ Bot riavviato!")

        elif text == "/genera" and (not data.genLocked or user.isAdmin):
            sendText(chatId)

        elif ("@makersitabot" in text) and ((not data.genLocked) or user.isAdmin):
            sendText(chatId, msgId)

        elif replyTrigger and (not data.genLocked or user.isAdmin):
            replyMsgId = int(msg["reply_to_message"]["message_id"])
            if replyMsgId not in data.actSentMessages:
                sendText(chatId, msgId)
                if user.remainingCalls > 0:
                    data.actSentMessages.append(replyMsgId)
                    commit()


def accept_message(msg):
    Thread(target=reply, args=[msg]).start()

reloadAdmins()
bot.message_loop({'chat': accept_message})

while True:
    sleep(randint(settings["minSendInterval"]*60, settings["maxSendInterval"]*60))
    if datetime.now().hour in range(settings["sendStartHour"], settings["sendEndHour"]):
        sendText()
