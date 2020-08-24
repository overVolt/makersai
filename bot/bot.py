from telepot import Bot
from time import sleep
from threading import Thread, Lock
from json import load as jsload
from os.path import abspath, dirname, join
from random import randint, uniform
from datetime import datetime
from textgenrnn import textgenrnn

with open(join(dirname(abspath(__file__)), "settings.json")) as settings_file:
    settings = jsload(settings_file)

bot = Bot(settings["token"])
groupId = int(settings["groupId"])
generateLock = Lock()

aiConfigPath = join(dirname(abspath(__file__)), settings['aiModelName'])
ai = textgenrnn(weights_path=f"{aiConfigPath}_weights.hdf5",
                vocab_path=f"{aiConfigPath}_vocab.json",
                config_path=f"{aiConfigPath}_config.json")


def generateText():
    gen = ""
    while gen == "":
        gen = ai.generate(
            n=1,
            return_as_list=True,
            temperature=[round(uniform(0.3, 1.0), 1)],
            max_gen_length=160,
            progress=False
        )[0].strip("\"'/\\") # ", ', /, \
    return gen


def sendText(chatId: int=groupId, replyId: int=None, silent: bool=False):
    if generateLock.acquire(blocking=False):
        bot.sendChatAction(chatId, "typing")
        bot.sendMessage(chatId, generateText(), reply_to_message_id=replyId)
        sleep(settings["genCooldownSec"])
        generateLock.release()
    elif not silent:
        sent = bot.sendMessage(chatId, "Aspetta un po' prima di usarmi di nuovo.", reply_to_message_id=replyId)
        sleep(5)
        bot.deleteMessage((chatId, sent["message_id"]))


def isAdmin(userId: int, chatId: int):
    req = bot.getChatAdministrators(chatId)
    adminList = [int(user["user"]["id"]) for user in req if not user["user"]["is_bot"]]
    return userId in adminList


def reply(msg):
    chatId = int(msg['chat']['id'])
    fromId = int(msg['from']['id'])
    msgId = int(msg['message_id'])
    chatInfo = bot.getChat(chatId)

    #replyTrigger = False
    #if "reply_to_message" in msg:
    #    if "username" in msg["reply_to_message"]["from"]:
    #        replyTrigger = msg["reply_to_message"]["from"].get("username") == "makersitabot"

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

        if text.lower() == "ping":
            if randint(1, 4) == 1:
                bot.sendMessage(chatId, "pong", reply_to_message_id=msgId)
        
        elif text.lower() == "over":
            if randint(1, 4) == 1:
                bot.sendMessage(chatId, "Volt!", reply_to_message_id=msgId)
        
        elif text.lower() == "no u":
            if randint(1, 4) == 1:
                bot.sendMessage(chatId, "no u", reply_to_message_id=msgId)

        elif text.lower().endswith("cose"):
            if randint(1, 4) == 1:
                bot.sendMessage(chatId, "varie", reply_to_message_id=msgId)

        elif ("cose diverse" in text.lower()) or ("cose strane" in text.lower()):
            if randint(1, 4) == 1:
                bot.sendMessage(chatId, "cose varie*", reply_to_message_id=msgId)

        elif text.startswith("/pronuncia ") and isAdmin(fromId, chatId):
            replyId = msg["reply_to_message"]["message_id"] if "reply_to_message" in msg else None
            bot.sendMessage(chatId, text.split(" ", 1)[1], parse_mode="HTML",
                            disable_web_page_preview=True, reply_to_message_id=replyId)

        elif text == "/bloccagen" and isAdmin(fromId, chatId):
            if generateLock.acquire(blocking=True, timeout=20):
                bot.sendMessage(chatId, "Comando /genera bloccato!")

        elif text == "/sbloccagen" and isAdmin(fromId, chatId):
            if generateLock.locked():
                generateLock.release()
                bot.sendMessage(chatId, "Comando /genera sbloccato!")

        elif text == "/genera":
            sendText(chatId)

        #elif ("@makersitabot" in text) or replyTrigger:
        #    sendText(chatId, msgId)


def accept_message(msg):
    Thread(target=reply, args=[msg]).start()

bot.message_loop({'chat': accept_message})

while True:
    sleep(randint(settings["minSendInterval"]*60, settings["maxSendInterval"]*60))
    if datetime.now().hour in range(settings["sendStartHour"], settings["sendEndHour"]):
        if generateLock.acquire(blocking=False):
            sendText(groupId, silent=True)
