"""
---channel_doc---
--data_cmd--
ats: Tractor/Game Crash
cod: Total/Wins/Lost/Crash
stream: Total
Tag: user_id, user_name, time tagged

---user_doc---
--user_data--
-cmd-
tag: Total/Good/Fail
pp: Size/LastDone/History
"""
from mongoengine import Document, IntField, DynamicField, DateTimeField, DictField


class Channels(Document):
    user_id = IntField(primary_key=True)
    user_name = DynamicField(default="")
    user_login = DynamicField(default="")
    channel_details = DictField(default={"online": False,
                                         "online_last": None,
                                         "branded": False,
                                         "title": "",
                                         "game_id": "",
                                         "game_name": "",
                                         "content_class": [],
                                         "tags": []})
    channel_data = DictField(default={"followers": ["774737491", "192918528"],
                                      "hype_train": {"last": None,
                                                     "current": False,
                                                     "current_level": 1,
                                                     "last_level": 2,
                                                     "record_level": 2},
                                      "writing_clock": False})
    data_cmd = DictField(default={"ats": [0, 0],
                                  "cod": [0, 0, 0, 0],
                                  "stream": 0,
                                  "tag": [None, None, None]})
    data_lists = DictField(default={"ignore": ["431026547", "52268235", "253326823", "100135110", "431199284", "216527497", "451658633", "656479529"],
                                    "lurk": ["848563434", "882825189", "99161823", "669781726"],
                                    "mods": ["542995008", "659673020", "800907099", "451658633", "842545503", "1023291886", "563919062"],
                                    "non_tag": ["777768639", "186953777", "1023291886", "881267248", "806552159", "121590725", "758228900", "268136120", "170147951"],
                                    "spam": []})
    meta = {"db_alias": "default"}


class EconomyData(Document):
    author_id = IntField(primary_key=True)
    author_name = DynamicField(default="")
    guild_name = DynamicField(default="")
    last_daily_done = DateTimeField(default=None)
    next_daily_avail = DateTimeField(default=None)
    points_value = DynamicField(default=0)
    last_gained_value = DynamicField(default=0)
    last_lost_value = DynamicField(default=0)
    highest_gained_value = DynamicField(default=0)
    highest_lost_value = DynamicField(default=0)
    highest_gambling_won = DynamicField(default=0)
    highest_gambling_lost = DynamicField(default=0)
    total_gambling_won = DynamicField(default=0)
    total_gambling_lost = DynamicField(default=0)
    twitch_id = DynamicField(default=0)
    meta = {"db_alias": "Discord_Database"}


class Users(Document):
    user_id = IntField(primary_key=True)
    user_discord_id = IntField(default=0)
    user_name = DynamicField(default="")
    user_login = DynamicField(default="")
    user_data = DictField(default={"level": 1,
                                   "xp": 0.0,
                                   "points": 0.0,
                                   "cmd": {"tag": [0, 0, 0],
                                           "pp": [None, None, []]},
                                   "first_chat": None,
                                   "latest_chat": None})
    meta = {"db_alias": "default"}
