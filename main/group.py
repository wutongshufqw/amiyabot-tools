import asyncio
import functools
import re
import time

from amiyabot import Message, Chain, MiraiBotInstance, CQHttpBotInstance, Event

from core.database.bot import Admin
from core.database.user import User
from .main import bot, tool_is_close, get_cooldown, set_cooldown
from ..api import MiraiTools, GOCQTools
from ..utils import SQLHelper

special_title_cd = {}
ban_list = {}


# 修改群名片&群头衔
@bot.on_message(keywords=re.compile(r'^兔兔修改群名片\s?([\s\S]+)$'), level=5)
async def set_group_card(data: Message):
    if await tool_is_close(data.instance.appid, 1, 3, 1, data.channel_id):
        return
    if data.is_admin:
        match = re.match(r'^兔兔修改群名片\s?([\s\S]+)$', data.text_original)
        new_card = match.group(1)
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
            res = await gocq.set_group_card(int(group), int(target), new_card)
        if res:
            return Chain(data).text('修改成功')
        else:
            return Chain(data).text('修改失败, 请检查兔兔权限和昵称是否符合QQ规则')
    else:
        return Chain(data).text('权限不足')


@bot.on_message(keywords=['修改群头衔'], level=5)
async def set_group_special_title(data: Message):
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
    if data.is_admin:
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


# 群欢迎消息
@bot.on_message(keywords=['设置欢迎消息'], allow_direct=False, level=5)
async def set_welcome(data: Message):
    if await tool_is_close(data.instance.appid, 1, 3, 4, data.channel_id):
        return
    if data.is_admin:
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
    if data.is_admin:
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


@bot.on_event('notice.group_increase')  # GOCQ群成员入群
async def member_join(event: Event, instance: CQHttpBotInstance):
    if await tool_is_close(instance.appid, 1, 3, 4, event.data['group_id']):
        return
    message = await SQLHelper.get_welcome(instance.appid, event.data['group_id'])
    if message is not None:
        await instance.send_message(Chain().at(str(event.data['user_id']), True).text(message.message),
                                    channel_id=str(event.data['group_id']))


@bot.on_message(keywords=['设置退群消息'], allow_direct=False, level=5)
async def set_quit(data: Message):
    if await tool_is_close(data.instance.appid, 1, 3, 7, data.channel_id):
        return
    if data.is_admin:
        try:
            quit_ = data.text_original.split(' ', 1)[1].replace('｛', '{').replace('｝', '}')
            await SQLHelper.set_quit(data.instance.appid, data.channel_id, quit_)
            return Chain(data).text('退群消息设置成功')
        except IndexError:
            return Chain(data).text('请输入退群消息')


@bot.on_message(keywords=['清除退群消息'], allow_direct=False, level=5)
async def clear_quit(data: Message):
    if await tool_is_close(data.instance.appid, 1, 3, 7, data.channel_id):
        return
    if data.is_admin:
        await SQLHelper.delete_quit(data.instance.appid, data.channel_id)
        return Chain(data).text('退群消息已清除')


@bot.on_event('MemberLeaveEventQuit')  # Mirai群成员退群
async def member_quit(event: Event, instance: MiraiBotInstance):
    if await tool_is_close(instance.appid, 1, 3, 7, event.data['member']['group']['id']):
        return
    message = await SQLHelper.get_quit(instance.appid, event.data['member']['group']['id'])
    if message is not None:
        await instance.send_message(
            Chain().text(message.message.replace('{info}', f'{event.data["member"]["memberName"]}({event.data["member"]["id"]})')),
            channel_id=str(event.data['member']['group']['id'])
        )


@bot.on_event('notice.group_decrease')  # GOCQ群成员退群
async def member_quit(event: Event, instance: CQHttpBotInstance):
    if await tool_is_close(instance.appid, 1, 3, 7, event.data['group_id']) or event.data['sub_type'] != 'leave':
        return
    message = await SQLHelper.get_quit(instance.appid, event.data['group_id'])
    if message is not None:
        info = await GOCQTools(instance, event).get_stranger_info(event.data['user_id'])
        await instance.send_message(
            Chain().text(message.message.replace('{info}', f'{info["nickname"]}({event.data["user_id"]})')),
            channel_id=str(event.data['group_id'])
        )


@bot.on_message(keywords=['退群'], allow_direct=False, level=5)
async def quit_group(data: Message):
    if await tool_is_close(data.instance.appid, 1, 3, 5, data.channel_id):
        return
    if data.is_at and data.is_admin:
        if type(data.instance) is MiraiBotInstance:
            mirai = MiraiTools(data.instance, data=data)
            await mirai.quit_group(int(data.channel_id))
        if type(data.instance) is CQHttpBotInstance:
            gocq = GOCQTools(data.instance, data=data)
            await gocq.quit_group(int(data.channel_id))


# 群禁言
async def ban_verify(data: Message):
    if await tool_is_close(data.instance.appid, 1, 3, 6, data.channel_id):
        return False
    user = User.get_or_none(user_id=data.user_id)
    if not user or user.black:
        return False
    config_ = bot.get_config("ban", data.channel_id)
    if config_ is None:
        return False
    else:
        black_list = config_.get('black_list', [])
        flag = False
        for item in black_list:
            keyword = item.get('keyword', None)
            k_type = item.get('type', None)
            if keyword and k_type:
                if k_type == '包含关键词':
                    if keyword in data.text_original:
                        flag = True
                        break
                elif k_type == '等于关键词':
                    if keyword == data.text_original:
                        flag = True
                        break
                elif k_type == '正则表达式':
                    if re.search(keyword, data.text_original):
                        flag = True
                        break
        if flag:
            curr_time = int(time.time())
            info = ban_list.get(f'{data.channel_id}-{data.user_id}', {})
            if not info:
                info = {
                    'count': 1,
                    'time': curr_time
                }
            else:
                range_ = config_.get('range', 0)
                if curr_time - info['time'] <= range_ * 60:
                    info['count'] += 1
                else:
                    info['count'] = 1
                info['time'] = curr_time
            ban_list[f'{data.channel_id}-{data.user_id}'] = info
            ban_times = config_.get('time', [{"count": 1, "time": 1}])

            def cmp(t1, t2):
                return t1['count'] - t2['count']

            ban_times.sort(key=functools.cmp_to_key(cmp))
            ban_time = 0
            for item in ban_times:
                if info['count'] >= item['count']:
                    ban_time = item['time']
                else:
                    break
            if ban_time > 0:
                res = False
                await asyncio.sleep(1)
                if type(data.instance) is MiraiBotInstance:
                    mirai = MiraiTools(data.instance, data=data)
                    res = await mirai.ban(data.channel_id, data.user_id, ban_time * 60)
                if type(data.instance) is CQHttpBotInstance:
                    gocq = GOCQTools(data.instance, data=data)
                    res = await gocq.ban(data.channel_id, data.user_id, ban_time * 60)
                if res:
                    tip = config_.get('tip', '博士, 你触犯了禁言规则, 请注意~')
                    await data.send(Chain(data).text(tip))
                    return True, 99
    return False


@bot.on_message(verify=ban_verify, check_prefix=False)
async def ban(data: Message):
    return
