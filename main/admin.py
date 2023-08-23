import asyncio
import datetime
from typing import Optional, Union

import os
import sys
import time

from core import Admin, bot as main_bot, GitAutomation, log

try:
    import psutil
except ImportError:
    try:
        import pip

        pip.main(['install', 'psutil'])
        import psutil
    except ImportError:
        pip = None
        psutil = None
        log.warning('你使用的是exe部署,无法获取CPU及内存使用率')

from amiyabot import Message, Chain, MiraiBotInstance, CQHttpBotInstance, Event, Equal
from amiyabot.factory import BotHandlerFactory

from .main import bot, tool_is_close

from ..api import MiraiTools, GOCQTools
from ..utils import SQLHelper, run_async

special_title_cd = {}
global_dict = {}
command_error = '请输入正确的指令'


# 重启
@bot.on_message(keywords=Equal('兔兔重启'), check_prefix=False, allow_direct=True, level=5)
async def restart(data: Message):
    if await tool_is_close(data.instance.appid, 2, 1, 1):
        return
    config_ = bot.get_config('superuser')
    if config_ is not None and int(data.user_id) in config_:
        await data.send(Chain(data, at=False).text('重启中...'))
        os.execl(sys.executable, sys.executable, *sys.argv)
    else:
        return Chain(data).text('权限不足')


async def check_restart(t: int):
    if t > 10:
        return True
    else:
        return False


# noinspection PyUnusedLocal
@bot.timed_task(custom=check_restart, sub_tag='tools-restart')
async def restart_task(instance: BotHandlerFactory):
    bot.remove_timed_task('tools-restart')
    config_ = bot.get_config('superuser')
    if config_ is not None:
        for i in config_:
            for j in main_bot:
                try:
                    await j.send_message(Chain().text('兔兔启动成功或小工具插件安装成功！'), str(i))
                except AttributeError:
                    pass


# 好友申请
@bot.on_event('NewFriendRequestEvent')  # Mirai新好友申请
async def new_friend_request(event: Event, instance: MiraiBotInstance):
    if await tool_is_close(instance.appid, 2, 1, 2):
        return
    operators = bot.get_config('operators')
    operator = None
    auto = False
    for o in operators:
        if str(o.get('appid')) == instance.appid:
            operator = o['operator']
            auto = o.get('auto_friend', False)
            break
    if operator is None:
        return
    mirai = MiraiTools(instance, event=event)
    await mirai.new_friend_request(operator, auto)
    if not auto:
        await SQLHelper.add_friend(instance.appid, 'mirai', nickname=event.data['nick'], event_id=event.data['eventId'],
                                   from_id=event.data['fromId'], group_id=event.data['groupId'],
                                   message=event.data['message'])


@bot.on_event('request.friend')  # GOCQ新好友申请
async def new_friend_request(event: Event, instance: CQHttpBotInstance):
    if await tool_is_close(instance.appid, 2, 1, 2):
        return
    operators = bot.get_config('operators')
    operator = None
    auto = False
    for o in operators:
        if str(o.get('appid')) == instance.appid:
            operator = o['operator']
            auto = o.get('auto_friend', False)
            break
    if operator is None:
        return
    gocq = GOCQTools(instance, event=event)
    nickname = await gocq.new_friend_request(operator, auto)
    if not auto:
        await SQLHelper.add_friend(instance.appid, 'gocq', nickname=nickname, flag=event.data['flag'],
                                   user_id=event.data['user_id'], comment=event.data['comment'])


@bot.on_message(keywords=['同意好友', '拒绝好友', '拉黑好友'], direct_only=True, level=5)
async def new_friend_request(data: Message):
    if await tool_is_close(data.instance.appid, 2, 1, 2):
        return
    if data.text_original.startswith('兔兔'):
        data.text_original = data.text_original.replace('兔兔', '', 1)
    elif data.text_original.startswith('阿米娅'):
        data.text_original = data.text_original.replace('阿米娅', '', 1)
    elif data.text_original.startswith('Amiya'):
        data.text_original = data.text_original.replace('amiya', '', 1)
    operators = bot.get_config('operators')
    operator = None
    for o in operators:
        if str(o.get('appid')) == data.instance.appid:
            operator = o['operator']
            break
    if operator is not None and int(data.user_id) == operator:
        msg = data.text_original.split(' ')
        flag = False
        if type(data.instance) is MiraiBotInstance:
            mirai = MiraiTools(data.instance, data=data)
            if len(msg) == 1:
                return Chain(data).text('请输入QQ号, 注意空格')
            else:
                msg[1] = int(msg[1])
                info = await SQLHelper.get_friend(data.instance.appid, 'mirai', msg[1])
                if info is None:
                    return Chain(data).text('该好友申请不存在')
            if msg[0] == '同意好友':
                if len(msg) == 2:
                    flag = await mirai.new_friend_request_handle(info.event_id, info.from_id, info.group_id, 0)
                else:
                    text = ' '.join(msg[2:])
                    flag = await mirai.new_friend_request_handle(info.event_id, info.from_id, info.group_id, 0, text)
            elif msg[0] == '拒绝好友':
                flag = await mirai.new_friend_request_handle(info.event_id, info.from_id, info.group_id, 1)
            elif msg[0] == '拉黑好友':
                flag = await mirai.new_friend_request_handle(info.event_id, info.from_id, info.group_id, 2)
            else:
                return Chain(data).text(command_error)
        if type(data.instance) is CQHttpBotInstance:
            gocq = GOCQTools(data.instance, data=data)
            if len(msg) == 1:
                return Chain(data).text('请输入QQ号, 注意空格')
            else:
                msg[1] = int(msg[1])
                info = await SQLHelper.get_friend(data.instance.appid, 'gocq', msg[1])
                if info is None:
                    return Chain(data).text('该好友请求不存在')
            if msg[0] == '同意好友':
                if len(msg) == 2:
                    flag = await gocq.new_friend_request_handle(info.flag, True)
                else:
                    flag = await gocq.new_friend_request_handle(info.flag, True, msg[2])
            elif msg[0] == '拒绝好友':
                flag = gocq.new_friend_request_handle(info.flag, False)
            else:
                return Chain(data).text(command_error)
        if flag:
            await SQLHelper.delete_friend(data.instance.appid, msg[1])
            return Chain(data).text('操作成功')
        else:
            return Chain(data).text('操作失败')
    else:
        return Chain(data).text('权限不足')


@bot.on_message(keywords=['查看好友申请'], direct_only=True, level=5)
async def view_new_friends(data: Message):
    if await tool_is_close(data.instance.appid, 2, 1, 2):
        return
    operators = bot.get_config('operators')
    operator = None
    for o in operators:
        if str(o.get('appid')) == data.instance.appid:
            operator = o['operator']
            break
    if operator is not None and int(data.user_id) == operator:
        if type(data.instance) is MiraiBotInstance:
            info = await SQLHelper.get_friends(data.instance.appid, 'mirai')
            if info is None or len(info) == 0:
                return Chain(data).text('暂无好友申请')
            else:
                msg = '好友申请列表:\n'
                j = 1
                for i in info:
                    msg += f'{j}. QQ号: {i.from_id} 申请时间: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i.date))}\n'
                    j += 1
                msg += '回复 [序号] 查看申请信息\n发送"兔兔同意好友 [QQ号] ([回复信息])"以同意请求\n发送"兔兔拒绝好友 [QQ号]"以拒绝请求\n发送"兔兔拉黑好友 [QQ号]"以拉黑请求'
                while True:
                    reply = await data.wait(Chain(data).text(msg))
                    if reply:
                        try:
                            id_ = int(reply.text_original)
                        except ValueError:
                            break
                        if id_ > len(info):
                            break
                        else:
                            msg = f'QQ号: {info[id_ - 1].from_id}\n昵称: {info[id_ - 1].nickname}\n申请信息: {info[id_ - 1].message}\n申请时间: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info[id_ - 1].date))}'
                    else:
                        break
        if type(data.instance) is CQHttpBotInstance:
            info = await SQLHelper.get_friends(data.instance.appid, 'gocq')
            if info is None or len(info) == 0:
                return Chain(data).text('暂无好友申请')
            else:
                msg = '好友申请列表:\n'
                j = 1
                for i in info:
                    msg += f'{j}. QQ号: {i.user_id} 申请时间: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i.date))}\n'
                    j += 1
                msg += '回复 [序号] 查看申请信息\n发送"兔兔同意好友 [QQ号] ([好友备注])"以同意请求\n发送"兔兔拒绝好友 [QQ号]"以拒绝请求'
                while True:
                    reply = await data.wait(Chain(data).text(msg))
                    if reply:
                        try:
                            id_ = int(reply.text_original)
                        except ValueError:
                            break
                        if id_ > len(info):
                            break
                        else:
                            msg = f'QQ号: {info[id_ - 1].user_id}\n昵称: {info[id_ - 1].nickname}\n申请信息: {info[id_ - 1].comment}\n申请时间: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info[id_ - 1].date))}'
                    else:
                        break


@bot.on_message(keywords=['清空好友申请'], allow_direct=True, level=5)
async def clear_new_friends(data: Message):
    if await tool_is_close(data.instance.appid, 2, 1, 2):
        return
    operators = bot.get_config('operators')
    operator = None
    for o in operators:
        if str(o.get('appid')) == data.instance.appid:
            operator = o['operator']
            break
    if operator is not None and int(data.user_id) == operator:
        res = False
        if type(data.instance) is MiraiBotInstance:
            res = await SQLHelper.delete_friends(data.instance.appid, 'mirai')
        if type(data.instance) is CQHttpBotInstance:
            res = await SQLHelper.delete_friends(data.instance.appid, 'gocq')
        if res:
            return Chain(data).text('操作成功')
        else:
            return Chain(data).text('操作失败')
    else:
        return Chain(data).text('权限不足')


# 群聊邀请
@bot.on_event('BotInvitedJoinGroupRequestEvent')  # Mirai群聊邀请
async def group_invite(event: Event, instance: MiraiBotInstance):
    if await tool_is_close(instance.appid, 2, 1, 3):
        return
    operators = bot.get_config('operators')
    operator = None
    for o in operators:
        if str(o.get('appid')) == instance.appid:
            operator = o['operator']
            break
    if operator is None:
        return
    mirai = MiraiTools(instance, event=event)
    await mirai.group_invite(operator)
    await SQLHelper.add_invite(instance.appid, 'mirai', event.data['groupId'], event_id=event.data['eventId'],
                               from_id=event.data['fromId'], group_name=event.data['groupName'],
                               nick=event.data['nick'], message=event.data['message'])


@bot.on_event('request.group')  # GOCQ群聊邀请
async def group_invite(event: Event, instance: CQHttpBotInstance):
    if await tool_is_close(instance.appid, 2, 1, 3) or event.data['sub_type'] != 'invite':
        return
    operators = bot.get_config('operators')
    operator = None
    for o in operators:
        if str(o.get('appid')) == instance.appid:
            operator = o['operator']
            break
    if operator is None:
        return
    gocq = GOCQTools(instance, event=event)
    await gocq.group_invite(operator)
    await SQLHelper.add_invite(instance.appid, 'gocq', event.data['group_id'], flag=event.data['flag'],
                               user_id=event.data['user_id'], comment=event.data['comment'])


@bot.on_message(keywords=['同意邀请', '拒绝邀请'], allow_direct=True, level=5)
async def group_invite(data: Message):
    if await tool_is_close(data.instance.appid, 2, 1, 3):
        return
    if data.text_original.startswith('兔兔'):
        data.text_original = data.text_original.replace('兔兔', '', 1)
    elif data.text_original.startswith('阿米娅'):
        data.text_original = data.text_original.replace('阿米娅', '', 1)
    elif data.text_original.startswith('Amiya'):
        data.text_original = data.text_original.replace('Amiya', '', 1)
    elif data.text_original.startswith('amiya'):
        data.text_original = data.text_original.replace('amiya', '', 1)
    operators = bot.get_config('operators')
    operator = None
    for o in operators:
        if str(o.get('appid')) == data.instance.appid:
            operator = o['operator']
            break
    if operator is not None and int(data.user_id) == operator:
        msg = data.text_original.split(' ')
        flag = False
        if type(data.instance) is MiraiBotInstance:
            mirai = MiraiTools(data.instance, data=data)
            if len(msg) == 1:
                return Chain(data).text('请输入群号, 注意空格')
            else:
                msg[1] = int(msg[1])
                info = await SQLHelper.get_invite(data.instance.appid, 'mirai', msg[1])
                if info is None:
                    return Chain(data).text('该群聊邀请不存在')
            if msg[0] == '同意邀请':
                if len(msg) == 2:
                    flag = await mirai.group_invite_handle(info.event_id, info.from_id, info.group_id, 0)
                else:
                    text = ' '.join(msg[2:])
                    flag = await mirai.group_invite_handle(info.event_id, info.from_id, info.group_id, 0, text)
            elif msg[0] == '拒绝邀请':
                if len(msg) == 2:
                    flag = await mirai.group_invite_handle(info.event_id, info.from_id, info.group_id, 1)
                else:
                    text = ' '.join(msg[2:])
                    flag = await mirai.group_invite_handle(info.event_id, info.from_id, info.group_id, 1, text)
            else:
                return Chain(data).text(command_error)
        if type(data.instance) is CQHttpBotInstance:
            gocq = GOCQTools(data.instance, data=data)
            if len(msg) == 1:
                return Chain(data).text('请输入群号, 注意空格')
            else:
                msg[1] = int(msg[1])
                info = await SQLHelper.get_invite(data.instance.appid, 'gocq', msg[1])
                if info is None:
                    return Chain(data).text('该群聊邀请不存在')
            if msg[0] == '同意邀请':
                flag = await gocq.group_invite_handle(info.flag, True)
            elif msg[0] == '拒绝邀请':
                if len(msg) == 2:
                    flag = await gocq.group_invite_handle(info.flag, True)
                else:
                    text = ' '.join(msg[2:])
                    flag = await gocq.group_invite_handle(info.flag, True, text)
            else:
                return Chain(data).text(command_error)
        if flag:
            await SQLHelper.delete_invite(data.instance.appid, msg[1])
            return Chain(data).text('操作成功')
        else:
            return Chain(data).text('操作失败')
    else:
        return Chain(data).text('权限不足')


@bot.on_message(keywords=['查看邀请'], allow_direct=True, level=5)
async def view_group_invites(data: Message):
    if await tool_is_close(data.instance.appid, 2, 1, 3):
        return
    operators = bot.get_config('operators')
    operator = None
    for o in operators:
        if str(o.get('appid')) == data.instance.appid:
            operator = o['operator']
            break
    if operator is not None and int(data.user_id) == operator:
        if type(data.instance) is MiraiBotInstance:
            info = await SQLHelper.get_invites(data.instance.appid, 'mirai')
            if info is None or len(info) == 0:
                return Chain(data).text('暂无群聊邀请')
            else:
                msg = '群聊邀请列表:\n'
                j = 1
                for i in info:
                    msg += f'{j}. 群号: {i.group_id} 邀请时间: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i.date))}\n'
                    j += 1
                msg += '回复 [序号] 查看申请信息\n发送"兔兔同意邀请 [群号] [回复消息]"以同意邀请\n发送"兔兔拒绝邀请 [群号] [回复消息]"以拒绝邀请'
                while True:
                    reply = await data.wait(Chain(data).text(msg))
                    if reply:
                        try:
                            id_ = int(reply.text_original)
                        except ValueError:
                            break
                        if id_ > len(info):
                            break
                        else:
                            msg = f'邀请人: {info[id_ - 1].nick}\n邀请人QQ: {info[id_ - 1].from_id}\n群聊: {info[id_ - 1].group_name}\n群号: {info[id_ - 1].group_id}\n邀请信息: {info[id_ - 1].message}\n邀请时间: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info[id_ - 1].date))}'
                    else:
                        break
        if type(data.instance) is CQHttpBotInstance:
            info = await SQLHelper.get_invites(data.instance.appid, 'gocq')
            if info is None or len(info) == 0:
                return Chain(data).text('暂无群聊邀请')
            else:
                msg = '群聊邀请列表:\n'
                j = 1
                for i in info:
                    msg += f'{j}. 群号: {i.group_id} 邀请时间: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i.date))}\n'
                    j += 1
                msg += '回复 [序号] 查看申请信息\n发送"兔兔同意好友 [QQ号] ([好友备注])"以同意请求\n发送"兔兔拒绝好友 [QQ号]"以拒绝请求'
                while True:
                    reply = await data.wait(Chain(data).text(msg))
                    if reply:
                        try:
                            id_ = int(reply.text_original)
                        except ValueError:
                            break
                        if id_ > len(info):
                            break
                        else:
                            msg = f'邀请人QQ: {info[id_ - 1].user_id}\n群号: {info[id_ - 1].group_id}\n申请时间: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info[id_ - 1].date))}'
                    else:
                        break


@bot.on_message(keywords=['清空邀请'], allow_direct=True, level=5)
async def clear_new_friends(data: Message):
    if await tool_is_close(data.instance.appid, 2, 1, 3):
        return
    operators = bot.get_config('operators')
    operator = None
    for o in operators:
        if str(o.get('appid')) == data.instance.appid:
            operator = o['operator']
            break
    if operator is not None and int(data.user_id) == operator:
        res = False
        if type(data.instance) is MiraiBotInstance:
            res = await SQLHelper.delete_invites(data.instance.appid, 'mirai')
        if type(data.instance) is CQHttpBotInstance:
            res = await SQLHelper.delete_invites(data.instance.appid, 'gocq')
        if res:
            return Chain(data).text('操作成功')
        else:
            return Chain(data).text('操作失败')
    else:
        return Chain(data).text('权限不足')


async def update_resource(data: Message):
    keyword = bot.get_config('update_pool', '更新资源')
    if data.text_original != keyword or await tool_is_close(data.instance.appid, 2, 1, 4):
        return False
    if bool(Admin.get_or_none(account=data.user_id)):
        start = time.time()
        await data.send(Chain(data).text('开始更新卡池图片...'))
        git_path = 'resource/plugins/gacha/pool'
        git_url = 'https://gitlab.com/wutongshufqw/arknights-pool.git'
        GitAutomation(git_path, git_url).update()
        end = time.time()
        await data.send(Chain(data).text(f'更新完成, 耗时{end - start:.2f}s'))
    return False, 0


# 更新卡池图片
# noinspection PyUnusedLocal
@bot.on_message(verify=update_resource, check_prefix=False, allow_direct=True)
async def update_gacha_pool(data: Message):
    pass


# 禁言自动退群
@bot.on_event('BotMuteEvent')  # mirai
async def bot_mute_event(event: Event, instance: MiraiBotInstance):
    if await tool_is_close(instance.appid, 2, 1, 5):
        return
    mirai = MiraiTools(instance, event=event)
    await mirai.quit_group(event.data['operator']['group']['id'])


@bot.on_event('notice.group_ban')  # gocq
async def bot_mute_event(event: Event, instance: CQHttpBotInstance):
    if await tool_is_close(instance.appid, 2, 1, 5) or event.data['sub_type'] != 'ban':
        return
    if event.data['user_id'] != int(instance.appid):
        return
    gocq = GOCQTools(instance, event=event)
    await gocq.quit_group(event.data['group_id'])


def build_nickname(nick: Optional[str] = None) -> str:
    config_ = bot.get_config('nickname')
    runtime = config_.get('runtime')
    try:
        TIME = int(datetime.datetime.strptime(runtime, '%Y-%m-%dT%H:%M:%S.%f%z').timestamp())
    except ValueError:
        runtime = datetime.datetime.now().astimezone().isoformat()
        config_['runtime'] = runtime
        bot.set_config('nickname', config_)
        TIME = int(datetime.datetime.strptime(runtime, '%Y-%m-%dT%H:%M:%S%z').timestamp())
    time_ = int(time.time() - TIME)
    day = time_ // 86400
    hour = time_ // 3600 % 24
    minute = time_ // 60 % 60
    second = time_ % 60
    nickname_list = config_.get('nickname', [{'type': 'text', 'content': '兔兔'}])
    diy = config_.get('diy', [])
    nickname = ''
    for n in nickname_list:
        if n['type'] == 'text':
            nickname += n['content']
        elif n['type'] == 'day':
            nickname += n['content'].replace('%', str(day))
        elif n['type'] == 'hour':
            nickname += n['content'].replace('%', str(hour))
        elif n['type'] == 'minute':
            nickname += n['content'].replace('%', str(minute))
        elif n['type'] == 'second':
            nickname += n['content'].replace('%', str(second))
        elif n['type'] == 'reply_name' and nick:
            nickname += n['content'].replace('%', nick)
        elif n['type'] == 'reply_time':
            nickname += n['content'].replace('%', datetime.datetime.now().strftime('%H:%M:%S'))
        elif n['type'] == 'mem_use':
            if psutil:
                nickname += n['content'].replace('%', str(psutil.virtual_memory().percent))
            else:
                nickname += n['content'].replace('%', 'NaN')
        elif n['type'] == 'cpu_use':
            if psutil:
                nickname += n['content'].replace('%', str(psutil.cpu_percent()))
            else:
                nickname += n['content'].replace('%', 'NaN')
        elif n['type'] == 'diy':
            keywords = n['content'].split(':')
            if len(keywords) == 2:
                index = int(keywords[0]) - 1
                if index < len(diy):
                    local = {}
                    try:
                        code = diy[index].replace('\\n', '\n')
                        exec(code, {}, local)
                        nickname += str(local.get(keywords[1], ''))
                    except Exception as e:
                        log.error(f'自定义昵称错误: {e}')
    return nickname


# 修改群名片
# noinspection PyUnusedLocal
@bot.timed_task(each=10, sub_tag='update_nickname')
async def update_nickname(instance: BotHandlerFactory):
    async def _update_nickname():
        config_ = bot.get_config('nickname')

        async def loop_func():
            config = bot.get_config('nickname')
            for item in main_bot:
                if type(item.instance) == CQHttpBotInstance:
                    gocq = GOCQTools(item.instance)
                    groups = await gocq.get_group_list()
                    if groups:
                        for group in groups:
                            nickname = build_nickname()
                            await gocq.set_group_card(group['group_id'], item.appid, nickname)
                            log.info(f'更新群名片: {group["group_name"]}({group["group_id"]})')
                            await asyncio.sleep(5)
                elif type(item.instance) == MiraiBotInstance:
                    mirai = MiraiTools(item.instance)
                    groups = await mirai.get_group_list()
                    if groups:
                        for group in groups:
                            nickname = build_nickname()
                            await mirai.set_group_card(group['group']['id'], item.appid, nickname)
                            log.info(f'更新群名片: {group["group"]["name"]}({group["group"]["id"]})')
                            await asyncio.sleep(5)
            if config_["update"] == "circle":
                await asyncio.sleep(config.get("interval", 0))

        while True:
            await loop_func()
            log.info("-----群名片更新完成-----")
            if config_["update"] == "once":
                return

    bot.remove_timed_task('update_nickname')
    update = bot.get_config('nickname').get('update', 'none')
    if update == 'none':
        return
    run_async(_update_nickname)


@bot.message_before_send
async def update_nickname_on_reply(chain: Union[Chain, list], *_):
    try:
        config_ = bot.get_config('nickname')
        if config_['update'] != 'reply':
            return chain
        nickname = build_nickname(nick=chain.data.nickname)
        helper = None
        if type(chain.data.instance) == CQHttpBotInstance:
            helper = GOCQTools(chain.data.instance)
        elif type(chain.data.instance) == MiraiBotInstance:
            helper = MiraiTools(chain.data.instance)
        await helper.set_group_card(chain.data.channel_id, chain.data.instance.appid, nickname)
    except Exception as e:
        log.warning(f'获取Chain信息发生错误:\n{repr(e)}\n取消群名片更新')
    return chain


# 群聊人数限制
# noinspection PyUnusedLocal
@bot.timed_task(each=10, sub_tag='quit_group')
async def quit_group(instance: BotHandlerFactory):
    def check_group(appid: int, group_id: int, member_count: int) -> Union[str, bool]:
        config_ = bot.get_config('memberLimit')
        message = config_.get('message', '')
        blacklist = config_.get('blacklist', [])
        if group_id in blacklist:
            return True
        whitelist = config_.get('whitelist', [])
        if group_id in whitelist:
            return False
        limit = config_.get('limit', [])
        for item in limit:
            if item['appid'] == appid:
                if item['min'] <= member_count and (item['max'] == -1 or member_count <= item['max']):
                    return False
                else:
                    if message:
                        return message.replace('{min}', str(item['min'])).replace('{max}', str(
                            item['max'] if item['max'] != -1 else '∞'))
                    else:
                        return True
        return False

    async def _quit_group():
        async def loop_func():
            for item in main_bot:
                accounts = bot.get_config('operators')
                operator = None
                for account in accounts:
                    if account['appid'] == int(item.appid):
                        operator = str(account['operator'])
                        break
                if type(item.instance) == CQHttpBotInstance:
                    gocq = GOCQTools(item.instance)
                    groups = await gocq.get_group_list()
                    for group in groups:
                        if group['group_id'] == 491353154:
                            print('test')
                        msg = check_group(int(item.appid), group['group_id'], group['member_count'])
                        if msg:
                            if type(msg) == str:
                                await item.send_message(Chain().text(msg), channel_id=str(group['group_id']))
                            await gocq.quit_group(group['group_id'], True)
                            if bot.get_config('memberLimit').get('tip', True):
                                await item.send_message(
                                    Chain().text(f'群聊: {group["group_name"]}({group["group_id"]})已退群'),
                                    user_id=operator)
                if type(item.instance) == MiraiBotInstance:
                    mirai = MiraiTools(item.instance)
                    groups = await mirai.get_group_list()
                    for group in groups:
                        members = mirai.get_group_member_list(group['id'])
                        msg = check_group(int(item.appid), group['id'], len(members))
                        if msg:
                            if type(msg) == str:
                                await item.send_message(Chain().text(msg), channel_id=str(group['id']))
                            await mirai.quit_group(group['id'])
                            if bot.get_config('memberLimit').get('tip', True):
                                await item.send_message(
                                    Chain().text(f'群聊: {group["group_name"]}({group["group_id"]})已退群'),
                                    user_id=operator)

        while bot.get_config('memberLimit').get('enable', False):
            await loop_func()
            log.info("-----退出群聊完成-----")
            await asyncio.sleep(bot.get_config('memberLimit').get('interval', 60) * 60)

    bot.remove_timed_task('quit_group')
    run_async(_quit_group)
