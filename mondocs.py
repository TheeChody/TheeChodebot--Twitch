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
            "boards": [3],
            "current_game": {
                "board_size": None,
                "chodelings": {},
                "chosen_pattern": [],
                "game_type": None,
                "game_ended_time": None,
                "game_started_time": None,
                "items": {},
                "major_bingo_pot": 0
            },
            "history": {},
            "modes": {
                "ats": [],
                "bf": [],
                "fails": [],
                "copshow": [],
                "hellskitchen": []
            },
            "patterns": {
                "major": {
                    "full_board": {
                        '3': {
                            "row_0": [0, 1, 2],
                            "row_1": [0, 1, 2],
                            "row_2": [0, 1, 2]
                        },
                        '5': {
                            "row_0": [0, 1, 2, 3, 4],
                            "row_1": [0, 1, 2, 3, 4],
                            "row_2": [0, 1, 2, 3, 4],
                            "row_3": [0, 1, 2, 3, 4],
                            "row_4": [0, 1, 2, 3, 4]
                        },
                        '7': {
                            "row_0": [0, 1, 2, 3, 4, 5, 6],
                            "row_1": [0, 1, 2, 3, 4, 5, 6],
                            "row_2": [0, 1, 2, 3, 4, 5, 6],
                            "row_3": [0, 1, 2, 3, 4, 5, 6],
                            "row_4": [0, 1, 2, 3, 4, 5, 6],
                            "row_5": [0, 1, 2, 3, 4, 5, 6],
                            "row_6": [0, 1, 2, 3, 4, 5, 6]
                        },
                        '9': {
                            "row_0": [0, 1, 2, 3, 4, 5, 6, 7, 8],
                            "row_1": [0, 1, 2, 3, 4, 5, 6, 7, 8],
                            "row_2": [0, 1, 2, 3, 4, 5, 6, 7, 8],
                            "row_3": [0, 1, 2, 3, 4, 5, 6, 7, 8],
                            "row_4": [0, 1, 2, 3, 4, 5, 6, 7, 8],
                            "row_5": [0, 1, 2, 3, 4, 5, 6, 7, 8],
                            "row_6": [0, 1, 2, 3, 4, 5, 6, 7, 8],
                            "row_7": [0, 1, 2, 3, 4, 5, 6, 7, 8],
                            "row_8": [0, 1, 2, 3, 4, 5, 6, 7, 8]
                        }
                    }
                },
                "minor": {
                    "corners": {
                        '3': {
                            "row_0": [0, 2],
                            "row_2": [0, 2]
                        },
                        '5': {
                            "row_0": [0, 4],
                            "row_4": [0, 4]
                        },
                        '7': {
                            "row_0": [0, 6],
                            "row_6": [0, 6]
                        },
                        '9': {
                            "row_0": [0, 8],
                            "row_8": [0, 8]
                        }
                    },
                    "shape_+": {
                        '3': {
                            "row_0": [1],
                            "row_1": [0, 1, 2],
                            "row_2": [1]
                        },
                        '5': {
                            "row_0": [2],
                            "row_1": [2],
                            "row_2": [0, 1, 2, 3, 4],
                            "row_3": [2],
                            "row_4": [2]
                        },
                        '7': {
                            "row_0": [3],
                            "row_1": [3],
                            "row_2": [3],
                            "row_3": [0, 1, 2, 3, 4, 5, 6],
                            "row_4": [3],
                            "row_5": [3],
                            "row_6": [3]
                        },
                        '9': {
                            "row_0": [4],
                            "row_1": [4],
                            "row_2": [4],
                            "row_3": [4],
                            "row_4": [0, 1, 2, 3, 4, 5, 6, 7, 8],
                            "row_5": [4],
                            "row_6": [4],
                            "row_7": [4],
                            "row_8": [4]
                        }
                    },
                    "shape_diamond": {
                        '3': {
                            "row_0": [1],
                            "row_1": [0, 2],
                            "row_2": [1]
                        },
                        '5': {
                            "row_0": [2],
                            "row_1": [1, 3],
                            "row_2": [0, 4],
                            "row_3": [1, 3],
                            "row_4": [2]
                        },
                        '7': {
                            "row_0": [3],
                            "row_1": [2, 4],
                            "row_2": [1, 5],
                            "row_3": [0, 6],
                            "row_4": [1, 5],
                            "row_5": [2, 4],
                            "row_6": [3]
                        },
                        '9': {
                            "row_0": [4],
                            "row_1": [3, 5],
                            "row_2": [2, 6],
                            "row_3": [1, 7],
                            "row_4": [0, 8],
                            "row_5": [1, 7],
                            "row_6": [2, 6],
                            "row_7": [3, 5],
                            "row_8": [4]
                        }
                    },
                    "shape_x": {
                        '3': {
                            "row_0": [0, 2],
                            "row_1": [1],
                            "row_2": [0, 2]
                        },
                        '5': {
                            "row_0": [0, 4],
                            "row_1": [1, 3],
                            "row_2": [2],
                            "row_3": [1, 3],
                            "row_4": [0, 4]
                        },
                        '7': {
                            "row_0": [0, 6],
                            "row_1": [1, 5],
                            "row_2": [2, 4],
                            "row_3": [3],
                            "row_4": [2, 4],
                            "row_5": [1, 5],
                            "row_6": [0, 6]
                        },
                        '9': {
                            "row_0": [0, 8],
                            "row_1": [1, 7],
                            "row_2": [2, 6],
                            "row_3": [3, 5],
                            "row_4": [4],
                            "row_5": [3, 5],
                            "row_6": [2, 6],
                            "row_7": [1, 7],
                            "row_8": [0, 8]
                        }
                    }
                }
            }
        },
        "fish": {
            "items": [],
            "recast": [],
            "upgrades": {
                "line": {
                    '0': {
                        "cost": 0,
                        "effect": 0,
                        "level": 0,
                        "name": "Standard"
                    },
                    '1': {
                        "cost": 5000,
                        "effect": 5,
                        "level": 1,
                        "name": "Common"
                    },
                    '2': {
                        "cost": 25000,
                        "effect": 10,
                        "level": 2,
                        "name": "UnCommon"
                    },
                    '3': {
                        "cost": 500000,
                        "effect": 20,
                        "level": 3,
                        "name": "Rare"
                    },
                    '4': {
                        "cost": 1000000,
                        "effect": 30,
                        "level": 4,
                        "name": "Epic"
                    },
                    '5': {
                        "cost": 1000000,
                        "effect": 45,
                        "level": 5,
                        "name": "Legendary"
                    },
                    '6': {
                        "cost": 2500000,
                        "effect": 60,
                        "level": 6,
                        "name": "TheeLine"
                    }
                },
                "lure": {
                    '0': {
                        "cost": 0,
                        "effect": 0,
                        "level": 0,
                        "name": "Standard",
                        "pLow": 0.0,
                        "pHigh": 100.0
                    },
                    '1': {
                        "cost": 5000,
                        "effect": 2.5,
                        "level": 1,
                        "name": "Common",
                        "pLow": 85.0,
                        "pHigh": 98.0
                    },
                    '2': {
                        "cost": 25000,
                        "effect": 5,
                        "level": 2,
                        "name": "UnCommon",
                        "pLow": 72.5,
                        "pHigh": 94.0
                    },
                    '3': {
                        "cost": 500000,
                        "effect": 10,
                        "level": 3,
                        "name": "Rare",
                        "pLow": 50.0,
                        "pHigh": 88.0
                    },
                    '4': {
                        "cost": 1000000,
                        "effect": 15,
                        "level": 4,
                        "name": "Epic",
                        "pLow": 34.0,
                        "pHigh": 80.0
                    },
                    '5': {
                        "cost": 1000000,
                        "effect": 20,
                        "level": 5,
                        "name": "Legendary",
                        "pLow": 16.9,
                        "pHigh": 69.0
                    },
                    '6': {
                        "cost": 2500000,
                        "effect": 30,
                        "level": 6,
                        "name": "TheeLure",
                        "pLow": 16.9,
                        "pHigh": 50.0
                    }
                },
                "reel": {
                    '0': {
                        "cost": 0,
                        "effect": 0,
                        "level": 0,
                        "name": "Standard",
                        "pLow": 0,
                        "pHigh": 100
                    },
                    '1': {
                        "cost": 5000,
                        "effect": 5,
                        "level": 1,
                        "name": "Common",
                        "pLow": 0,
                        "pHigh": 100
                    },
                    '2': {
                        "cost": 25000,
                        "effect": 10,
                        "level": 2,
                        "name": "UnCommon",
                        "pLow": 0,
                        "pHigh": 100
                    },
                    '3': {
                        "cost": 500000,
                        "effect": 15,
                        "level": 3,
                        "name": "Rare",
                        "pLow": 0,
                        "pHigh": 100
                    },
                    '4': {
                        "cost": 1000000,
                        "effect": 30,
                        "level": 4,
                        "name": "Epic",
                        "pLow": 0,
                        "pHigh": 100
                    },
                    '5': {
                        "cost": 100000,
                        "effect": 45,
                        "level": 5,
                        "name": "Legendary",
                        "pLow": 0,
                        "pHigh": 100
                    },
                    '6': {
                        "cost": 2500000,
                        "effect": 60,
                        "level": 6,
                        "name": "TheeReel",
                        "pLow": 0,
                        "pHigh": 100
                    }
                },
                "rod": {
                    '0': {
                        "cost": 0,
                        "effect": 0,
                        "level": 0,
                        "name": "Standard",
                        "autocast_limit": 5
                    },
                    '1': {
                        "cost": 5000,
                        "effect": 2.5,
                        "level": 1,
                        "name": "Common",
                        "autocast_limit": 25
                    },
                    '2': {
                        "cost": 25000,
                        "effect": 5,
                        "level": 2,
                        "name": "UnCommon",
                        "autocast_limit": 50
                    },
                    '3': {
                        "cost": 500000,
                        "effect": 10,
                        "level": 3,
                        "name": "Rare",
                        "autocast_limit": 100
                    },
                    '4': {
                        "cost": 1000000,
                        "effect": 15,
                        "level": 4,
                        "name": "Epic",
                        "autocast_limit": 150
                    },
                    '5': {
                        "cost": 1000000,
                        "effect": 20,
                        "level": 5,
                        "name": "Legendary",
                        "autocast_limit": 200
                    },
                    '6': {
                        "cost": 2500000,
                        "effect": 30,
                        "level": 6,
                        "name": "TheeRod",
                        "autocast_limit": 420
                    }
                }
            }
        },
        "gamble": {
            "total": 25000.0
        },
        "heist": {
            "crews": {
                '0': {
                    "name": "Basic Bitches",
                    "chance": 0.05,
                    "cost": 100
                },
                '1': {
                    "name": "Barely Able",
                    "chance": 0.5,
                    "cost": 25000
                },
                '2': {
                    "name": "Semi-Pro",
                    "chance": 1,
                    "cost": 50000
                },
                '3': {
                    "name": "Professionals",
                    "chance": 2.5,
                    "cost": 150000
                },
                '4': {
                    "name": "Thee A-Team",
                    "chance": 5,
                    "cost": 500000
                }
            }
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
               "game_started": None,
               "items_chosen": [],
               "major_bingo": False,
               "minor_bingo": False,
               "points_won": 0
           },
           "history": {}
        },
        "fight": {
            "aggressor": {},
            "defender": {},
            "streak": {
                "type": None,
                "value": 0
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
        "heist": {
            "gamble": {
                "last": None,
                "history": {}
            }
        },
        "iq": {
            "current": 0.0,
            "last": None,
            "history": []
        },
        "jail": {
            "attempt_other_last": None,
            "early_release": 0,
            "escape_cards": 0,
            "fish_jails": 0,
            "history": {},
            "in_jail": False,
            "in_last": None,
            "shield_last": None,
            "shield_times": 0
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
