from telepot import Bot
from time import sleep
from threading import Thread
from json import load as jsload
from os.path import abspath, dirname, join
from random import randint
from datetime import datetime
from textgenrnn import textgenrnn

with open(join(dirname(abspath(__file__)), "settings.json")) as settings_file:
    settings = jsload(settings_file)

bot = Bot(settings["token"])
groupId = int(settings["groupId"])
generateLock = False
cachedString = "Message not generated."

aiConfigPath = join(dirname(abspath(__file__)), f"{settings['aiModelName']}")
ai = textgenrnn(weights_path=f"{aiConfigPath}_weights.hdf5",
                vocab_path=f"{aiConfigPath}_vocab.json",
                config_path=f"{aiConfigPath}_config.json")


def generateText():
    global generateLock, cachedString
    generateLock = True
    cachedString = ai.generate(
        n=1,
        return_as_list=True,
        temperature=[0.5],
        max_gen_length=280,
        progress=False
    )[0]
    sleep(settings["genCooldownSec"]-5)
    generateLock = False


def sendText(chatId: int):
    global generateLock
    if generateLock:
        sent = bot.sendMessage(chatId, f"Aspetta {settings['genCooldownSec']} secondi prima di usarmi di nuovo.")
        sleep(5)
        bot.deleteMessage((chatId, sent["message_id"]))
        return
    generateLock = True
    bot.sendChatAction(chatId, "typing")
    sleep(2)
    bot.sendMessage(chatId, cachedString)
    generateText()


def isAdmin(userId: int, chatId: int):
    req = bot.getChatAdministrators(chatId)
    adminList = [int(user["user"]["id"]) for user in req if not user["user"]["is_bot"]]
    return userId in adminList


def reply(msg):
    global generateLock
    chatId = int(msg['chat']['id'])
    fromId = int(msg['from']['id'])
    msgId = int(msg['message_id'])
    chatInfo = bot.getChat(chatId)

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
            if randint(0, 1) == 1:
                bot.sendMessage(chatId, "pong", reply_to_message_id=msgId)
        
        elif text.lower() == "over":
            if randint(0, 1) == 1:
                bot.sendMessage(chatId, "Volt!", reply_to_message_id=msgId)
        
        elif text.lower() == "no u":
            if randint(0, 1) == 1:
                bot.sendMessage(chatId, "no u", reply_to_message_id=msgId)

        elif text.lower().endswith("cose"):
            if randint(0, 1) == 1:
                bot.sendMessage(chatId, "varie", reply_to_message_id=msgId)

        elif ("cose diverse" in text.lower()) or ("cose strane" in text.lower()):
            if randint(0, 1) == 1:
                bot.sendMessage(chatId, "cose varie*", reply_to_message_id=msgId)

        elif text.startswith("/pronuncia ") and isAdmin(fromId, chatId):
            replyId = msg["reply_to_message"]["message_id"] if "reply_to_message" in msg else None
            bot.sendMessage(chatId, text.split(" ", 1)[1], parse_mode="HTML",
                            disable_web_page_preview=True, reply_to_message_id=replyId)

        elif text == "/bloccagen" and isAdmin(fromId, chatId):
            generateLock = True
            bot.sendMessage(chatId, "Comando /genera bloccato!")

        elif text == "/sbloccagen" and isAdmin(fromId, chatId):
            generateLock = False
            bot.sendMessage(chatId, "Comando /genera sbloccato!")

        elif (text == "/genera") or ("@makersitabot" in text):
            sendText(chatId)


def accept_message(msg):
    Thread(target=reply, args=[msg]).start()

bot.message_loop({'chat': accept_message})
generateText()

while True:
    sleep(randint(settings["minSendInterval"]*60, settings["maxSendInterval"]*60))
    hour = datetime.now().hour
    if hour in range(settings["sendStartHour"], settings["sendEndHour"]):
        if not generateLock:
            bot.sendChatAction(groupId, "typing")
            bot.sendMessage(groupId, cachedString)
            generateText()
