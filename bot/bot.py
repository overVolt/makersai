from telepot import Bot
from time import sleep
from threading import Thread
from json import load as jsload
from os.path import abspath, dirname, join
from textgenrnn import textgenrnn

with open(join(dirname(abspath(__file__)), "settings.json")) as settings_file:
    settings = jsload(settings_file)

bot = Bot(settings["token"])
groupId = int(settings["groupId"])
generateLock = False

aiConfigPath = join(dirname(abspath(__file__)), f"{settings['aiModelName']}")
ai = textgenrnn(weights_path=f"{aiConfigPath}_weights.hdf5",
                vocab_path=f"{aiConfigPath}_vocab.json",
                config_path=f"{aiConfigPath}_config.json")


def generateText():
    return ai.generate(
        n=1,
        return_as_list=True,
        temperature=[0.5],
        max_gen_length=100,
        progress=False
    )[0]


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
        text = text.replace("@" + bot.getMe()["username"], "")

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

        if text == "ping":
            bot.sendMessage(chatId, "pong")
        elif text == "over":
            bot.sendMessage(chatId, "Volt!")

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

        elif text == "/genera" and not generateLock:
            generateLock = True
            bot.sendChatAction(chatId, "typing")
            bot.sendMessage(chatId, generateText())
            generateLock = False


def accept_message(msg):
    Thread(target=reply, args=[msg]).start()

bot.message_loop({'chat': accept_message})

while True:
    sleep(60)
