from mongoengine import Document, BooleanField, IntField, DynamicField, ListField, DateTimeField


class Channels(Document):
    user_id = IntField(primary_key=True)
    user_name = DynamicField(default="")
    user_login = DynamicField(default="")
    channel_online = BooleanField(default=False)
    channel_title = DynamicField(default="")
    channel_game_id = DynamicField(default=0)
    channel_game_name = DynamicField(default="")
    channel_content_class = ListField(default=[])
    channel_tags = ListField(default=[])
    channel_branded = BooleanField(default=False)
    # followers_list = ListField(default=[])
    hype_train_last = DynamicField(default=None)
    hype_train_current = BooleanField(default=False)
    hype_train_current_level = IntField(default=0)
    hype_train_last_level = IntField(default=0)
    hype_train_record_level = IntField(default=0)
    cmd_gamble_last_chatter = DynamicField(default="")
    cmd_tag_last_it = DynamicField(default="")
    cmd_tag_last_it_time = DateTimeField(default=None)
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
    user_name = DynamicField(default="")
    user_login = DynamicField(default="")
    user_discord_id = IntField(default=0)
    user_level = IntField(default=1)  # FOR NEW LEVELING SYSTEM TO BE DONE
    user_xp_points = IntField(default=0)  # FOR NEW LEVELING SYSTEM TO BE DONE
    user_points = IntField(default=0)
    first_chat_date = DateTimeField(default=None)
    latest_chat_date = DateTimeField(default=None)
    meta = {"db_alias": "default"}
