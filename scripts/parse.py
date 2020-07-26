import json
import re

def deEmojify(input):
    regrex_pattern = re.compile(pattern = "["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
            "]+", flags = re.UNICODE)
    return regrex_pattern.sub(r'', input)

userBlacklist = [
    365866830,
    235898396,
    208056682,
    417753222
]

print("Loading JSON file...")
with open("makersdata.json") as raw:
    data = json.load(raw)

print("Loading messages...")
messages = data["messages"]

print("Parsing messages...")
strings = []
for msg in messages:
    if msg.get("actor_id"):
        if msg["actor_id"] in userBlacklist:
            continue

    if msg.get("from_id"):
        if msg["from_id"] in userBlacklist:
            continue

    if msg.get("type") == "message":
        text = msg.get("text")
        if text:
            if type(text) == str:
                strings.append(text)

            elif type(text) == list:
                for item in text:
                    if type(item) == str:
                        strings.append(item)

print("Writing to file...")
with open("output.txt", "w") as out:
    for s in strings:
        s += "\n"
        s = deEmojify(s)
        out.write(s)
