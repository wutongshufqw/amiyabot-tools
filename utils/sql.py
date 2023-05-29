import datetime
import os
import time
from typing import Union

from amiyabot.database import *

from ..config import bottle_dir

db = connect_database('resource/plugins/tools/tools.db')


class ToolsBaseModel(ModelClass):
    class Meta:
        database = db


@table
class NewFriends(ToolsBaseModel):
    # Common
    id: int = AutoField()
    appid: int = IntegerField()
    adapter: str = CharField()
    date: int = IntegerField()
    nickname: str = CharField()
    # Mirai
    event_id: int = IntegerField(null=True)
    from_id: int = IntegerField(null=True)
    group_id: int = IntegerField(null=True)
    message: str = CharField(null=True)
    # Gocq
    flag: str = CharField(null=True)
    user_id: int = IntegerField(null=True)
    comment: str = CharField(null=True)


@table
class GroupInvite(ToolsBaseModel):
    # Common
    id: int = AutoField()
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
    id: int = AutoField()
    appid: int = IntegerField()
    channel_id: str = CharField()
    random: int = IntegerField()


@table
class Welcome(ToolsBaseModel):
    id: int = AutoField()
    appid: int = IntegerField()
    channel_id: str = CharField()
    message: str = CharField()


@table
class Quit(ToolsBaseModel):
    id: int = AutoField()
    appid: int = IntegerField()
    channel_id: str = CharField()
    message: str = CharField()


@table
class Fake(ToolsBaseModel):
    id: int = AutoField()
    appid: int = IntegerField()
    channel_id: str = CharField()
    open: bool = BooleanField()


@table
class Lottery(ToolsBaseModel):
    id: int = AutoField()
    appid: int = IntegerField()
    channel_id: str = CharField()
    date: datetime.date = DateField(null=True)
    times: int = IntegerField(null=True)


@table
class Tools(ToolsBaseModel):
    id: int = AutoField()
    main_id: int = IntegerField()
    sub_id: int = IntegerField()
    sub_sub_id: int = IntegerField()
    appid: int = IntegerField()
    tool_name: str = CharField()
    open: bool = BooleanField()
    version: str = CharField()


@table
class ToolsConfig(ToolsBaseModel):
    id: int = AutoField()
    tool_id: int = IntegerField()
    channel_id: str = CharField()
    open: bool = BooleanField()


@table
class TodayWife(ToolsBaseModel):
    id: int = AutoField()
    appid: int = IntegerField()
    channel_id: int = IntegerField()
    user_id: int = IntegerField()
    wife_id: int = IntegerField()
    nickname: str = CharField()
    date: datetime.date = DateField()


@table
class Caiyun(ToolsBaseModel):
    id: int = AutoField()
    user_id: int = IntegerField()
    apikey: int = IntegerField()
    model: int = IntegerField(default=1)


@table
class BottleFlow(ToolsBaseModel):
    id: int = AutoField()
    text: str = CharField(max_length=4096, null=True)
    picture: str = CharField(null=True)
    user_id: int = IntegerField()
    user_name: str = CharField()
    anonymous: bool = BooleanField()
    time: int = IntegerField()
    check: bool = BooleanField(default=False)


@table
class BottlePicture(ToolsBaseModel):
    id: int = AutoField()
    picture: str = CharField(unique=True)
    count: int = IntegerField(default=1)


class SQLHelper:
    @staticmethod
    async def add_friend(appid: str, adapter: str, nickname: str, event_id: int = None, from_id: int = None,
                         group_id: int = None, message: str = None, flag: str = None, user_id: int = None,
                         comment: str = None):
        date = int(time.time())
        friend = NewFriends.get_or_none(NewFriends.appid == appid, NewFriends.adapter == adapter,
                                        NewFriends.user_id == user_id, NewFriends.from_id == from_id)
        if friend:
            friend.date = date
            friend.event_id = event_id
            friend.from_id = from_id
            friend.group_id = group_id
            friend.nickname = nickname
            friend.message = message
            friend.flag = flag
            friend.comment = comment
            friend.save()
        else:
            NewFriends.create(appid=appid, adapter=adapter, date=date, nickname=nickname, event_id=event_id,
                              from_id=from_id, group_id=group_id, message=message, flag=flag, user_id=user_id,
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
        return Welcome.delete().where((Welcome.appid == appid) & (Welcome.channel_id == channel_id)).execute()

    @staticmethod
    async def set_quit(appid: str, channel_id: str, message: str):
        quit_ = Quit.get_or_none(Quit.appid == appid, Quit.channel_id == channel_id)
        if quit_:
            quit_.message = message
            quit_.save()
        else:
            Quit.create(appid=appid, channel_id=channel_id, message=message)

    @staticmethod
    async def get_quit(appid: str, channel_id: str):
        return Quit.get_or_none(Quit.appid == appid, Quit.channel_id == channel_id)

    @staticmethod
    async def delete_quit(appid: str, channel_id: str):
        return Quit.delete().where((Quit.appid == appid) & (Quit.channel_id == channel_id)).execute()

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
        return Tools.select().where(Tools.appid == appid).order_by(Tools.main_id.asc(), Tools.sub_id.asc(),
                                                                   Tools.sub_sub_id.asc())

    @staticmethod
    async def add_tool(appid: str, main_id: int, sub_id: int, sub_sub_id: int,
                       tool_name: str, open_: bool = False, version: str = None):
        return Tools.create(appid=appid, main_id=main_id, sub_id=sub_id, sub_sub_id=sub_sub_id, tool_name=tool_name,
                            open=open_, version=version)

    @staticmethod
    async def update_tool(id_: int, open_: bool = None, version: str = None, name: str = None):
        tool = Tools.get_or_none(Tools.id == id_)
        if tool:
            if open_ is not None:
                tool.open = open_
            if version is not None:
                tool.version = version
            if name is not None:
                tool.tool_name = name
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

    @staticmethod
    async def get_today_wife(appid: int, channel_id: int, user_id: int):
        return TodayWife.get_or_none(TodayWife.appid == appid, TodayWife.channel_id == channel_id,
                                     TodayWife.user_id == user_id, TodayWife.date == datetime.date.today())

    @staticmethod
    async def set_today_wife(appid: int, channel_id: int, user_id: int, wife_id: int, nickname: str):
        wife = TodayWife.get_or_none(TodayWife.appid == appid, TodayWife.channel_id == channel_id,
                                     TodayWife.user_id == user_id)
        if wife:
            wife.wife_id = wife_id
            wife.nickname = nickname
            wife.date = datetime.date.today()
            return wife.save()
        else:
            return TodayWife.create(appid=appid, channel_id=channel_id, user_id=user_id, wife_id=wife_id,
                                    nickname=nickname, date=datetime.date.today())

    @staticmethod
    async def set_caiyun_apikey(user_id: int, apikey: int):
        caiyun = Caiyun.get_or_none(Caiyun.user_id == user_id)
        if caiyun:
            caiyun.apikey = apikey
            return caiyun.save()
        else:
            return Caiyun.create(user_id=user_id, apikey=apikey)

    @staticmethod
    async def set_caiyun_model(user_id: int, model: int):
        caiyun = Caiyun.get_or_none(Caiyun.user_id == user_id)
        if caiyun:
            caiyun.model = model
            return caiyun.save()
        else:
            return False

    @staticmethod
    async def get_caiyun_info(user_id: int):
        return Caiyun.get_or_none(Caiyun.user_id == user_id)

    @staticmethod
    async def delete_caiyun_info(user_id: int):
        return Caiyun.delete().where(Caiyun.user_id == user_id).execute()

    @staticmethod
    async def create_bottle(user_id: int, user_name: str, anonymous: bool, max_bottle: int, time_: int,
                            text: Union[str, None] = None, picture: Union[str, None] = None, check: bool = False):
        res = None
        if max_bottle < 0:
            res = BottleFlow.create(user_id=user_id, user_name=user_name, anonymous=anonymous, time=time_, text=text,
                                    picture=picture, check=check)
        elif max_bottle == 0:
            pass
        else:
            count = BottleFlow.select().where(BottleFlow.check == False).count()
            if count < max_bottle:
                res = BottleFlow.create(user_id=user_id, user_name=user_name, anonymous=anonymous, time=time_,
                                        text=text, picture=picture, check=check)
            else:
                if check:
                    res = BottleFlow.create(user_id=user_id, user_name=user_name, anonymous=anonymous, time=time_,
                                            text=text, picture=picture, check=check)
                else:
                    while count >= max_bottle:
                        bottle = BottleFlow.select().where(BottleFlow.check == False).order_by(BottleFlow.time.asc())\
                            .first()
                        await SQLHelper.delete_bottle_by_id(bottle.id)
                        count -= 1
                    res = BottleFlow.create(user_id=user_id, user_name=user_name, anonymous=anonymous, time=time_,
                                            text=text, picture=picture, check=check)
        if res and picture:
            pictures = picture.split(';')
            for pic in pictures:
                exist = BottlePicture.get_or_none(BottlePicture.picture == pic)
                if exist:
                    exist.count += 1
                    exist.save()
                else:
                    BottlePicture.create(picture=pic)
        return res

    @staticmethod
    async def get_random_bottle(self: bool = False, user_id: int = None):
        if self:
            return BottleFlow.select().where(BottleFlow.check == False).order_by(fn.Random()).first()
        elif user_id:
            return BottleFlow.select().where(BottleFlow.check == False, BottleFlow.user_id != user_id)\
                .order_by(fn.Random()).first()

    @staticmethod
    async def delete_all_bottle():
        bottles = BottleFlow.select().where(BottleFlow.check == False)
        for bottle in bottles:
            await SQLHelper.delete_bottle_by_id(bottle.id)

    @staticmethod
    async def get_bottle_by_id(id_: int):
        return BottleFlow.get_or_none(BottleFlow.id == id_)

    @staticmethod
    async def delete_bottle_by_id(id_: int):
        bottle = BottleFlow.get_or_none(BottleFlow.id == id_)
        if bottle:
            if bottle.picture:
                pictures = bottle.picture.split(';')
                for pic in pictures:
                    exist = BottlePicture.get_or_none(BottlePicture.picture == pic)
                    if exist:
                        exist.count -= 1
                        if exist.count <= 0:
                            path = f'{bottle_dir}{pic}'
                            if os.path.exists(path):
                                os.remove(path)
                            exist.delete_instance()
                        exist.save()
            bottle.delete_instance()
            return True
        else:
            return False

    @staticmethod
    async def pass_bottle_by_id(id_: int):
        bottle = BottleFlow.get_or_none(BottleFlow.id == id_)
        if bottle:
            bottle.check = False
            return bottle.save()
        else:
            return False

    @staticmethod
    async def get_check_bottles():
        return BottleFlow.select().where(BottleFlow.check == True).order_by(BottleFlow.time.asc())
