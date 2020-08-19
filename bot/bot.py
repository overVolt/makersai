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

aiConfigPath = join(dirname(abspath(__file__)), f"{settings['aiModelName']}")
ai = textgenrnn(weights_path=f"{aiConfigPath}_weights.hdf5",
                vocab_path=f"{aiConfigPath}_vocab.json",
                config_path=f"{aiConfigPath}_config.json")


def generateText():
    return ai.generate(
        return_as_list=True,
        temperature=[0.2],
        max_gen_length=150,
        progress=False
    )[0]


def reply(msg):
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
        text.replace("@" + bot.getMe()["username"], "")

    ## CHAT PRIVATE
    if chatInfo["type"] == "private":
        bot.sendMessage(chatId, "Sorry, but I only work on the MakersITA group.")

    ## GRUPPI/SUPERGRUPPI
    elif chatInfo["type"] in ["group", "supergroup"]:
        if chatId != groupId: # Only respond to selected group
            bot.sendMessage(chatId, "Sorry, but I only work on the MakersITA group.")
            return

        if text == "ping":
            bot.sendMessage(chatId, "pong")

        elif text == "/genera":
            bot.sendMessage(chatId, generateText())

    print(bot.getChat(chatId))


def accept_message(msg):
    Thread(target=reply, args=[msg]).start()

bot.message_loop({'chat': accept_message})

while True:
    sleep(60)
