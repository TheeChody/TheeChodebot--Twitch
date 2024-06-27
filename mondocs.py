from mongoengine import Document, BooleanField, IntField, DynamicField, ListField, DateTimeField, FloatField


class Channels(Document):
    user_id = IntField(primary_key=True)
    user_name = DynamicField(default="")
    user_login = DynamicField(default="")
    channel_online = BooleanField(default=False)
    channel_online_last = DateTimeField(default=None)
    channel_title = DynamicField(default="")
    channel_game_id = DynamicField(default=0)
    channel_game_name = DynamicField(default="")
    channel_content_class = ListField(default=[])
    channel_tags = ListField(default=[])
    channel_branded = BooleanField(default=False)
    channel_followers_list = ListField(default=["774737491", "192918528"])
    hype_train_last = DynamicField(default=None)
    hype_train_current = BooleanField(default=False)
    hype_train_current_level = IntField(default=1)
    hype_train_last_level = IntField(default=2)
    hype_train_record_level = IntField(default=2)
    writing_to_clock = BooleanField(default=False)
    cmd_counter_list_ats = ListField(default=[0, 0])  # TractorCrash, GameCrash
    cmd_counter_list_cod = ListField(default=[0, 0, 0, 0])  # Total, Win, Lost, Crash
    cmd_counter_stream_crash = IntField(default=0)
    cmd_tag_last_it = ListField(default=[None, None, None])  # ID, NAME, TIME
    mod_list = ListField(default=["542995008", "659673020", "800907099", "451658633", "842545503", "1023291886", "563919062"])
    ignore_list = ListField(default=["431026547", "52268235", "253326823", "100135110", "431199284", "216527497", "451658633", "656479529"])
    spam_list = ListField(default=[])
    lurk_list = ListField(default=["848563434", "882825189", "99161823", "669781726"])
    non_tag_list = ListField(default=["777768639", "186953777", "1023291886", "881267248", "806552159", "121590725", "758228900", "268136120", "170147951"])
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
    user_level = IntField(default=1)
    user_xp_points = FloatField(default=0)
    user_points = IntField(default=0)
    user_pp = ListField(default=[None, None, ""])
    first_chat_date = DateTimeField(default=None)
    latest_chat_date = DateTimeField(default=None)
    meta = {"db_alias": "default"}
