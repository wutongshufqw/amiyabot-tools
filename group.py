from amiyabot import Message, Chain, MiraiBotInstance, CQHttpBotInstance, Event

from core import Admin
from .main import bot, tool_is_close, get_cooldown, set_cooldown
from ..api import MiraiTools, GOCQTools
from ..utils import SQLHelper


# 修改群名片&群头衔
@bot.on_message(keywords=['修改群名片'], allow_direct=False, level=5)
async def set_group_card(data: Message):
    if await tool_is_close(data.instance.appid, 1, 3, 1, data.channel_id):
        return
    if data.is_admin or bool(Admin.get_or_none(account=data.user_id)):
        msg = data.text_original.split(' ')
        if msg.__len__() == 1:
            return Chain(data).text('请输入新的群名片')
        elif msg.__len__() > 2:
            return Chain(data).text('群名片不能有空格')
        new_card = msg[1]
        at_member = data.at_target
        if at_member.__len__() == 0:
            target = data.instance.appid
        elif at_member.__len__() == 1:
            target = at_member[0]
        else:
            return Chain(data).text('请不要@多个人')
        group = data.channel_id
        res = False
        if type(data.instance) is MiraiBotInstance:
            mirai = MiraiTools(data.instance, data=data)
            res = await mirai.set_group_card(group, int(target), new_card)
        if type(data.instance) is CQHttpBotInstance:
            gocq = GOCQTools(data.instance, data=data)
            res = await gocq.set_group_card(group, int(target), new_card)
        if res:
            return Chain(data).text('修改成功')
        else:
            return Chain(data).text('修改失败, 请检查兔兔权限和昵称是否符合QQ规则')
    else:
        return Chain(data).text('权限不足')


@bot.on_message(keywords=['修改群头衔'], allow_direct=False, level=5)
async def set_group_special_title(data: Message, special_title_cd=None):
    if await tool_is_close(data.instance.appid, 1, 3, 2, data.channel_id):
        return
    config_ = bot.get_config('specialTitle')
    flag = 'deny'
    if bool(Admin.get_or_none(account=data.user_id)):
        flag = 'super'
    elif data.is_admin and config_.get('admin'):
        flag = 'admin'
    elif config_.get('guest'):
        flag = 'guest'
    if flag == 'deny':
        return Chain(data).text('权限不足')
    if flag == 'guest':
        if get_cooldown(f'{data.channel_id}-{data.user_id}', special_title_cd) == 1:
            return Chain(data).text('请勿频繁使用')
        set_cooldown(f'{data.channel_id}-{data.user_id}', special_title_cd, config_.get('cd'))
    msg = data.text_original.split(' ')
    if msg.__len__() == 1:
        return Chain(data).text('请输入新的群头衔')
    elif msg.__len__() > 2:
        return Chain(data).text('群头衔不能有空格')
    new_title = msg[1]
    at_member = data.at_target
    if at_member.__len__() > 1:
        return Chain(data).text('请不要@多个人')
    elif at_member.__len__() == 1:
        if at_member[0] == data.user_id:
            target = data.user_id
        else:
            target = at_member[0]
    else:
        target = data.user_id
    target = int(target)
    group = data.channel_id
    res = False
    if type(data.instance) is MiraiBotInstance:
        mirai = MiraiTools(data.instance, data=data)
        res = await mirai.set_group_special_title(group, target, new_title)
    if type(data.instance) is CQHttpBotInstance:
        gocq = GOCQTools(data.instance, data=data)
        res = await gocq.set_group_special_title(group, target, new_title)
    if res:
        return Chain(data).text('修改成功')
    else:
        return Chain(data).text('修改失败, 请检查兔兔权限和头衔是否符合QQ规则')


# 撤回消息
@bot.on_message(keywords=['撤回'], allow_direct=True, level=5)
async def recall(data: Message):
    if await tool_is_close(data.instance.appid, 1, 3, 3, data.channel_id):
        return
    if data.is_admin or bool(Admin.get_or_none(account=data.user_id)):
        if type(data.instance) is MiraiBotInstance:
            info = data.message['messageChain']
            for i in info:
                if i['type'] == 'Quote':
                    mirai = MiraiTools(data.instance, data=data)
                    await mirai.recall(i)
        if type(data.instance) is CQHttpBotInstance:
            info = data.message['message']
            for i in info:
                if i['type'] == 'reply':
                    gocq = GOCQTools(data.instance, data=data)
                    await gocq.recall(i)
    return


# 群欢迎消息
@bot.on_message(keywords=['设置欢迎消息'], allow_direct=False, level=5)
async def set_welcome(data: Message):
    if await tool_is_close(data.instance.appid, 1, 3, 4, data.channel_id):
        return
    if data.is_admin or bool(Admin.get_or_none(account=data.user_id)):
        try:
            welcome = data.text_original.split(' ', 1)[1]
            await SQLHelper.set_welcome(data.instance.appid, data.channel_id, welcome)
            return Chain(data).text('欢迎消息设置成功')
        except IndexError:
            return Chain(data).text('请输入欢迎消息')
    return Chain(data).text('权限不足')


@bot.on_message(keywords=['清除欢迎消息'], allow_direct=False, level=5)
async def clear_welcome(data: Message):
    if await tool_is_close(data.instance.appid, 1, 3, 4, data.channel_id):
        return
    if data.is_admin or bool(Admin.get_or_none(account=data.user_id)):
        await SQLHelper.delete_welcome(data.instance.appid, data.channel_id)
        return Chain(data).text('欢迎消息已清除')
    return Chain(data).text('权限不足')


@bot.on_event('MemberJoinEvent')  # Mirai群成员入群
async def member_join(event: Event, instance: MiraiBotInstance):
    if await tool_is_close(instance.appid, 1, 3, 4, event.data['member']['group']['id']):
        return
    message = await SQLHelper.get_welcome(instance.appid, event.data['member']['group']['id'])
    if message is not None:
        await instance.send_message(Chain().at(str(event.data['member']['id']), True).text(message.message),
                                    channel_id=str(event.data['member']['group']['id']))
    return


@bot.on_event('notice.group_increase')  # GOCQ群成员入群
async def member_join(event: Event, instance: CQHttpBotInstance):
    if await tool_is_close(instance.appid, 1, 3, 4, event.data['group_id']):
        return
    message = await SQLHelper.get_welcome(instance.appid, event.data['group_id'])
    if message is not None:
        await instance.send_message(Chain().at(str(event.data['user_id']), True).text(message.message),
                                    channel_id=str(event.data['group_id']))
    return


@bot.on_message(keywords=['退群'], allow_direct=False, level=5)
async def quit_group(data: Message):
    if await tool_is_close(data.instance.appid, 1, 3, 5, data.channel_id):
        return
    if data.is_at and (data.is_admin or bool(Admin.get_or_none(account=data.user_id))):
        if type(data.instance) is MiraiBotInstance:
            mirai = MiraiTools(data.instance, data=data)
            await mirai.quit_group(int(data.channel_id))
        if type(data.instance) is CQHttpBotInstance:
            gocq = GOCQTools(data.instance, data=data)
            await gocq.quit_group(int(data.channel_id))
    return
