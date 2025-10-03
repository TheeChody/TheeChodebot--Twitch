from mongoengine import Document, DictField, StringField


class Channels(Document):
    _id = StringField(primary_key=True)
    user_name = StringField(default="")
    user_login = StringField(default="")
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
        "restarting": False,
        "writing_clock": False
    })
    data_counters = DictField(default={
        "ats": {
            "game_crash": 0,
            "tractor_crash": 0
        },
        "cod": {
            "game_total": 0,
            "game_win": 0,
            "game_loss": 0,
            "game_crash": 0
        },
        "joints": {
            "current_session": {
                "last": None,
                "start": None,
                "total": 0
            },
            "session_history": {}
        },
        "stream": {
            "bot_restart": 0,
            "crash": 0
        }
    })
    data_games = DictField(default={
        "bingo": {
            "current_game": {
                "board_size": None,
                "chosen_pattern": [],
                "game_type": None,
                "game_started_time": None,
                "items_done": {},
                "major_bingo_pot": 0
            },
            "history": {}
        },
        "fish_recast": [],
        "gamble": {
            "total": 25000.0
        },
        "ranword": "",
        "tag": {
            "tagged_id": None,
            "tagged_name": None,
            "tagged_last": None
        }
    })
    data_lists = DictField(default={
        "ignore": [],
        "lurk": [],
        "mods": [],
        "non_tag": [],
        "spam": [],
        "coupons": []
    })


class Users(Document):
    _id = StringField(primary_key=True)
    name = StringField(default="")
    data_games = DictField(default={
        "bingo": {
           "current_game": {
               "game_board": {},
               "game_type": None,
               "joined_time": None,
               "items_chosen": [],
               "major_bingo": False,
               "minor_bingo": False
           },
           "history": {}
        },
        "fight": {
            # "streak": {
            #     "last": None,  # ToDo: Add Streak Counter For Win/Loss/Tied
            # },
            "times_aggressor": {
                "lost": 0,
                "tied": 0,
                "won": 0,
                "points_lost": 0.0,
                "points_won": 0.0
            },
            "times_defender": {
                "lost": 0,
                "tied": 0,
                "won": 0,
                "points_lost": 0.0,
                "points_won": 0.0
            },
            "shield": [None, 0],
            "weapon": [None, 0]
        },
        "fish": {
            "auto": {
                "cast": 0,
                "catches": {},
                "cost": 0,
                "initiated": None
            },
            "line": {
                "cast": False,
                "caught_last": [],
                "cut": False,
                "cut_by": "",
                "cut_last": None
            },
            "special": {
                "buff_luck": 0,
                "buff_speed": 0,
                "ice": 0,
                "lube": 0
            },
            "totals": {
                "auto": {
                    "catches": {},
                    "cost": 0.0
                },
                "line": {
                    "cut_by": {},
                    "cut_other": {}
                },
                "manual": {
                    "catches": {}
                }
            },
            "upgrade": {
                "line": 0,
                "lure": 0,
                "reel": 0,
                "rod": 0
            }
        },
        "gamble": {
            "total": 0,
            "won": 0,
            "lost": 0,
            "total_won": 0.0,
            "total_lost": 0.0,
            "last": None
        },
        "iq": {
            "current": 0.0,
            "last": None,
            "history": []
        },
        "jail": {
            "attempt_last": None,
            "escapes": 0,
            "history": {
                "attempt_fail": {},
                "attempt_success": {},
                "attempt_shielded": {},
                "early_released": 0,
                "escaped_attempt": {},
                "fished": 0,
                "in": {},
                "shielded_attempt": {},
                "times_shielded": 0
            },
            "in": False,
            "last": None,
            "shield": None
        },
        "other": {
            "bite": {
                "times_bite": 0,
                "times_bit": 0
            },
            "burn": {
                "times_burn": 0,
                "times_burned": 0
            },
            "kick": {
                "times_kick": 0,
                "times_kicked": 0
            },
            "lick": {
                "times_lick": 0,
                "times_licked": 0
            },
            "pants": {
                "times_pants": 0,
                "times_pantsed": 0
            },
            "pinch": {
                "times_pinch": 0,
                "times_pinched": 0
            },
            "pounce": {
                "times_pounce": 0,
                "times_pounced": 0
            },
            "punch": {
                "times_punch": 0,
                "times_punched": 0
            },
            "slap": {
                "times_slap": 0,
                "times_slapped": 0
            },
            "tickle": {
                "times_tickle": 0,
                "times_tickled": 0
            }
        },
        "pp": {
            "size": 0,
            "last": None,
            "history": []
        },
        "tag": {
            "total": 0,
            "success": 0,
            "fail": 0
        },
        "unoreverse": {
            "reverse": 0,
            "command": "jail"
        }
    })
    data_user = DictField(default={
        "id": "",
        "login": "",
        "rank": {
            "boost": 0.0,
            "level": 1,
            "points": 0.0,
            "xp": 0.0,
        },
        "dates": {
            "first_chat": None,
            "latest_chat": None,
            "checkin_streak": [0, None],
            "daily_cards": [0, None, []]
        },
        "channel": {
            "id": "",
            "name": ""
        }
    })
