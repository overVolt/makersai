from pony.orm import Database, Required

db = Database("sqlite", "../makersitabot.db", create_db=True)


class User(db.Entity):
    chatId = Required(int)
    isAdmin = Required(bool, default=False)
    remainingCalls = Required(int, default=3)


class Data(db.Entity):
    actSentMessages = Required(list, default=[])
    genLocked = Required(bool, default=False)


db.generate_mapping(create_tables=True)
