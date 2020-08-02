import json

userBlacklist = [
    365866830,
    235898396,
    208056682,
    417753222
]

msgBlacklist = [
    "",
    "\n",
    " ",
    ".",
    "..",
    "..."
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
        if s in msgBlacklist:
            continue
        s += "\n"
        out.write(s)
