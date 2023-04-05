import datetime
import time

from amiyabot.database import *

from core.database import config, is_mysql

db = connect_database('tools' if is_mysql else 'resource/plugins/tools/tools.db', is_mysql, config)


class ToolsBaseModel(ModelClass):
    class Meta:
        database = db


@table
class NewFriends(ToolsBaseModel):
    # Common
    id: int = IntegerField(primary_key=True)
    appid: int = IntegerField()
    adapter: str = CharField()
    date: int = IntegerField()
    # Mirai
    event_id: int = IntegerField(null=True)
    from_id: int = IntegerField(null=True)
    group_id: int = IntegerField(null=True)
    nick: str = CharField(null=True)
    message: str = CharField(null=True)
    # Gocq
    flag: str = CharField(null=True)
    user_id: int = IntegerField(null=True)
    comment: str = CharField(null=True)


@table
class GroupInvite(ToolsBaseModel):
    # Common
    id: int = IntegerField(primary_key=True)
    appid: int = IntegerField()
    adapter: str = CharField()
    date: int = IntegerField()
    group_id: int = IntegerField()
    # Mirai
    event_id: int = IntegerField(null=True)
    from_id: int = IntegerField(null=True)
    group_name: str = CharField(null=True)
    nick: str = CharField(null=True)
    message: str = CharField(null=True)
    # Gocq
    flag: str = CharField(null=True)
    user_id: int = IntegerField(null=True)
    comment: str = CharField(null=True)


@table
class AiBot(ToolsBaseModel):
    id: int = IntegerField(primary_key=True)
    appid: int = IntegerField()
    channel_id: str = CharField()
    random: int = IntegerField()


@table
class Welcome(ToolsBaseModel):
    id: int = IntegerField(primary_key=True)
    appid: int = IntegerField()
    channel_id: str = CharField()
    message: str = CharField()


@table
class Fake(ToolsBaseModel):
    id: int = IntegerField(primary_key=True)
    appid: int = IntegerField()
    channel_id: str = CharField()
    open: bool = BooleanField()


@table
class Lottery(ToolsBaseModel):
    id: int = IntegerField(primary_key=True)
    appid: int = IntegerField()
    channel_id: str = CharField()
    date: datetime.date = DateField(null=True)
    times: int = IntegerField(null=True)


@table
class Tools(ToolsBaseModel):
    id: int = IntegerField(primary_key=True)
    main_id: int = IntegerField()
    sub_id: int = IntegerField()
    sub_sub_id: int = IntegerField()
    appid: int = IntegerField()
    tool_name: str = CharField()
    open: bool = BooleanField()
    version: str = CharField()


@table
class ToolsConfig(ToolsBaseModel):
    id: int = IntegerField(primary_key=True)
    tool_id: int = IntegerField()
    channel_id: str = CharField()
    open: bool = BooleanField()


class SQLHelper:
    @staticmethod
    async def add_friend(appid: str, adapter: str, event_id: int = None, from_id: int = None, group_id: int = None,
                         nick: str = None, message: str = None, flag: str = None, user_id: int = None,
                         comment: str = None):
        date = int(time.time())
        friend = NewFriends.get_or_none(NewFriends.appid == appid, NewFriends.adapter == adapter,
                                        NewFriends.user_id == user_id, NewFriends.from_id == from_id)
        if friend:
            friend.date = date
            friend.event_id = event_id
            friend.from_id = from_id
            friend.group_id = group_id
            friend.nick = nick
            friend.message = message
            friend.flag = flag
            friend.comment = comment
            friend.save()
        else:
            NewFriends.create(appid=appid, adapter=adapter, date=date, event_id=event_id, from_id=from_id,
                              group_id=group_id, nick=nick, message=message, flag=flag, user_id=user_id,
                              comment=comment)

    @staticmethod
    async def get_friend(appid: str, adapter: str, qq: int):
        if adapter == 'mirai':
            return NewFriends.get(appid=appid, adapter=adapter, from_id=qq)
        elif adapter == 'gocq':
            return NewFriends.get(appid=appid, adapter=adapter, user_id=qq)

    @staticmethod
    async def get_friends(appid: str, adapter: str):
        return NewFriends.select().where((NewFriends.appid == appid) & (NewFriends.adapter == adapter))

    @staticmethod
    async def delete_friend(appid: str, qq: int):
        NewFriends.delete().where(
            (NewFriends.appid == appid) & ((NewFriends.from_id == qq) | (NewFriends.user_id == qq))).execute()

    @staticmethod
    async def delete_friends(appid: str, adapter: str):
        return NewFriends.delete().where(
            (NewFriends.appid == appid) & (NewFriends.adapter == adapter)).execute() is not None

    @staticmethod
    async def add_invite(appid: str, adapter: str, group_id: int, event_id: int = None, from_id: int = None,
                         group_name: str = None, nick: str = None, message: str = None, flag: str = None,
                         user_id: int = None, comment: str = None):
        date = int(time.time())
        invite = GroupInvite.get_or_none(GroupInvite.appid == appid, GroupInvite.adapter == adapter,
                                         GroupInvite.group_id == group_id)
        if invite:
            invite.date = date
            invite.event_id = event_id
            invite.from_id = from_id
            invite.group_name = group_name
            invite.nick = nick
            invite.flag = flag
            invite.user_id = user_id
            invite.comment = comment
            invite.save()
        else:
            GroupInvite.create(appid=appid, adapter=adapter, date=date, event_id=event_id, from_id=from_id,
                               group_id=group_id, group_name=group_name, nick=nick, message=message, flag=flag,
                               user_id=user_id, comment=comment)

    @staticmethod
    async def get_invite(appid: str, adapter: str, group_id: int):
        return GroupInvite.get(appid=appid, adapter=adapter, group_id=group_id)

    @staticmethod
    async def get_invites(appid: str, adapter: str):
        return GroupInvite.select().where((GroupInvite.appid == appid) & (GroupInvite.adapter == adapter))

    @staticmethod
    async def delete_invite(appid: str, group_id: int):
        GroupInvite.delete().where((GroupInvite.appid == appid) & (GroupInvite.group_id == group_id)).execute()

    @staticmethod
    async def delete_invites(appid: str, adapter: str):
        return GroupInvite.delete().where(
            (GroupInvite.appid == appid) & (GroupInvite.adapter == adapter)).execute() is not None

    @staticmethod
    async def set_ai_probability(appid: str, channel_id: str, random: int):
        ai = AiBot.get_or_none(AiBot.appid == appid, AiBot.channel_id == channel_id)
        if ai:
            ai.random = random
            ai.save()
        else:
            AiBot.create(appid=appid, channel_id=channel_id, random=random)

    @staticmethod
    async def get_ai_probability(appid: str, channel_id: str):
        return AiBot.get_or_none(AiBot.appid == appid, AiBot.channel_id == channel_id)

    @staticmethod
    async def set_welcome(appid: str, channel_id: str, message: str):
        welcome = Welcome.get_or_none(Welcome.appid == appid, Welcome.channel_id == channel_id)
        if welcome:
            welcome.message = message
            welcome.save()
        else:
            Welcome.create(appid=appid, channel_id=channel_id, message=message)

    @staticmethod
    async def get_welcome(appid: str, channel_id: str):
        return Welcome.get_or_none(Welcome.appid == appid, Welcome.channel_id == channel_id)

    @staticmethod
    async def delete_welcome(appid: str, channel_id: str):
        Welcome.delete().where((Welcome.appid == appid) & (Welcome.channel_id == channel_id)).execute()

    @staticmethod
    async def set_fake(appid: str, channel_id: str, open_: bool):
        fake = Fake.get_or_none(Fake.appid == appid, Fake.channel_id == channel_id)
        if fake:
            fake.open = open_
            return fake.save()
        else:
            return Fake.create(appid=appid, channel_id=channel_id, open=open_)

    @staticmethod
    async def get_fake(appid: str, channel_id: str):
        return Fake.get_or_none(Fake.appid == appid, Fake.channel_id == channel_id)

    @staticmethod
    async def get_lottery(appid: str, channel_id: str):
        lottery = Lottery.get_or_none(Lottery.appid == appid, Lottery.channel_id == channel_id)
        if lottery:
            return lottery
        else:
            return Lottery.create(appid=appid, channel_id=channel_id)

    @staticmethod
    async def set_lottery(id_: int, times: int, date: datetime.date = None):
        lottery = Lottery.get_or_none(Lottery.id == id_)
        if lottery:
            lottery.times = times
            if date:
                lottery.date = date
            return lottery.save()
        else:
            return None

    @staticmethod
    async def get_tools_list(appid: str):
        return Tools.select().where(Tools.appid == appid)

    @staticmethod
    async def add_tool(appid: str, main_id: int, sub_id: int, sub_sub_id: int,
                       tool_name: str, open_: bool = False, version: str = None):
        return Tools.create(appid=appid, main_id=main_id, sub_id=sub_id, sub_sub_id=sub_sub_id, tool_name=tool_name,
                            open=open_, version=version)

    @staticmethod
    async def update_tool(id_: int, open_: bool = None, version: str = None):
        tool = Tools.get_or_none(Tools.id == id_)
        if tool:
            if open_ is not None:
                tool.open = open_
            if version is not None:
                tool.version = version
            return tool.save()
        else:
            return None

    @staticmethod
    async def get_tool(appid: str, main_id: int, sub_id: int, sub_sub_id: int):
        return Tools.get_or_none(Tools.appid == appid, Tools.main_id == main_id, Tools.sub_id == sub_id,
                                 Tools.sub_sub_id == sub_sub_id)

    @staticmethod
    async def update_channel_tool(tool_id: int, channel_id: str, open_: bool):
        channel_tool = ToolsConfig.get_or_none(ToolsConfig.tool_id == tool_id, ToolsConfig.channel_id == channel_id)
        if channel_tool:
            channel_tool.open = open_
            return channel_tool.save()
        else:
            return ToolsConfig.create(tool_id=tool_id, channel_id=channel_id, open=open_)

    @staticmethod
    async def get_channel_tool(tool_id: int, channel_id: str):
        return ToolsConfig.get_or_none(ToolsConfig.tool_id == tool_id, ToolsConfig.channel_id == channel_id)
