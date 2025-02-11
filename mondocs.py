"""
---channel_doc---
--data_counters--
ats: TractorCrashes, GameCrashes
cod: TotalMatches, TotalWins, TotalLosses, TotalCrashes
stream_crash: TotalCrashes
--data_games--
ranword: Random_Word
tag: user_id, user_name, time tagged

---user_doc---
--data_games--
fish: Dict
    auto: Dict
        cast: AutoCastLeft Float
        cost: AutoCastCost Float
        gain: TotalGained Float
        lost: TotalLost Float
        rewards: Rewards List
    line: Dict
        cast: CurrentlyCasted Bool
        cut: Next/CurrentCastCut Bool
        cut_by: If^^NameOfChatterWhoDidIt Str
        cut_last: LastCut Datetime
iq: Dict
    current: CurrentIQ Int
    last: LastChecked Datetime
    history: HistoryIQ List
tag: [Total/Good/Fail]
pp: [Size/LastDone/[History]]
--data_rank--
id: user_id
login: user_login
discord_id: discord_user_id -- to be phased out?
points: points_earned
-dates-
first_chat: FirstChat
latest_chat: LastChat
checkin_streak: TimesCheckedIn(ResetOn5), LastCheckInDate
-channel-
id: broadcaster_id_document_created_with
name: broadcaster_name_document_created_with
"""
from mongoengine import Document, IntField, DynamicField, DictField, StringField


class Channels(Document):
    _id = IntField(primary_key=True)
    user_name = DynamicField(default="")
    user_login = DynamicField(default="")
    channel_details = DictField(default={
        "online": False,
        "online_last": None,
        "branded": False,
        "title": "",
        "game_id": "",
        "game_name": "",
        "content_class": [],
        "tags": []
    })
    data_channel = DictField(default={
        "followers": [],
        "hype_train": {
            "current": False,
            "current_level": 1,
            "last": None,
            "last_level": 0,
            "record_level": 0
        },
        "last_clip": None,
        "writing_clock": False
    })
    data_counters = DictField(default={
        "ats": [0, 0],
        "cod": [0, 0, 0, 0],
        "joints": [0, None],
        "stream_crash": 0
    })
    data_games = DictField(default={
        "fish_recast": [],
        "ranword": "",
        "tag": [None, None, None]
    })
    data_lists = DictField(default={
        "ignore": [],
        "lurk": [],
        "mods": [],
        "non_tag": [],
        "spam": []
    })


class Users(Document):
    _id = StringField(primary_key=True)
    name = StringField(default="")
    data_games = DictField(default={
        "fish": {
            "auto": {
                "cast": 0,
                "cost": 0,
                "gain": 0.0,
                "lost": 0.0,
                "rewards": []
            },
            "line": {
                "cast": False,
                "cut": False,
                "cut_by": "",
                "cut_last": None
            }
        },
        "iq": {
            "current": 0.0,
            "last": None,
            "history": []
        },
        "jail": {
            "in": False,
            "last": None,
            "escapes": 0
        },
        "tag": [0, 0, 0],
        "pp": [None, None, []]
    })
    data_rank = DictField(default={
        "boost": 0.0,
        "level": 1,
        "xp": 0.0
    })
    data_user = DictField(default={
        "id": "",
        "login": "",
        "discord_id": "",
        "points": 0.0,
        "dates": {
            "first_chat": None,
            "latest_chat": None,
            "checkin_streak": [0, None],
            "daily_cards": [0, None]
        },
        "channel": {
            "id": "",
            "name": ""
        }
    })
