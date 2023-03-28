import json
import random

from amiyabot import Event
from amiyabot.adapters.mirai import MiraiBotInstance
from amiyabot.builtin.message import Message
from amiyabot.builtin.messageChain import Chain
from amiyabot.network.download import download_async
from amiyabot.network.httpRequests import http_requests

from core.database.bot import *
from .config import get_url, poke_message_send, request_headers


class MiraiHttpHelper:
    # noinspection HttpUrlsUsage
    def __init__(self, instance: MiraiBotInstance):
        self.session = instance.session
        host = instance.host
        port = instance.http_port
        self.url = f'http://{host}:{port}'

    async def post(self, path: str, data: dict):
        return await http_requests.post(self.url + path, data)

    async def get(self, path: str, data: dict):
        return await http_requests.get(self.url + path, params=data)

    async def send_nudge(self, target: int, subject: int, kind: str):
        return await self.post('/sendNudge',
                               {'sessionKey': self.session, 'target': target, 'subject': subject, 'kind': kind})

    async def member_info(self, target: int, member_id: int, name: str = None, special_title: str = None):
        if name is not None:
            return await self.post('/memberInfo', {'sessionKey': self.session, 'target': target, 'memberId': member_id,
                                                   'info': {'name': name}})
        elif special_title is not None:
            return await self.post('/memberInfo', {'sessionKey': self.session, 'target': target, 'memberId': member_id,
                                                   'info': {'specialTitle': special_title}})
        elif name is not None and special_title is not None:
            return await self.post('/memberInfo', {'sessionKey': self.session, 'target': target, 'memberId': member_id,
                                                   'info': {'name': name, 'specialTitle': special_title}})

    async def new_friend_request_event(self, eventId: int, from_id: int, group_id: int, operate: int,
                                       message: str = ''):
        return await self.post('/resp/newFriendRequestEvent', {'sessionKey': self.session, 'eventId': eventId,
                                                               'fromId': from_id, 'groupId': group_id,
                                                               'operate': operate,
                                                               'message': message})

    async def bot_invited_join_group_request_event(self, eventId: int, from_id: int, group_id: int, operate: int,
                                                   message: str = ''):
        return await self.post('/resp/botInvitedJoinGroupRequestEvent', {'sessionKey': self.session, 'eventId': eventId,
                                                                         'fromId': from_id, 'groupId': group_id,
                                                                         'operate': operate,
                                                                         'message': message})

    async def recall(self, target: int, message_id: int):
        return await self.post('/recall', {'sessionKey': self.session, 'target': target, 'messageId': message_id})

    async def member_profile(self, target: int, member_id: int):
        return await self.get('/memberProfile', {'sessionKey': self.session, 'target': target, 'memberId': member_id})


class MiraiTools:
    def __init__(self, instance: MiraiBotInstance, event: Event = None, data: Message = None):
        self.instance = instance
        self.event = event
        self.data = data
        self.helper = MiraiHttpHelper(instance)

    async def poke(self, config_):
        message = Chain()
        data = self.event.data
        msg = random.choice(config_['poke']['replies'])
        pattern = re.compile(r'\[.*?]')
        m0 = pattern.findall(msg)
        m1 = pattern.split(msg)
        flag = False
        for i in range(len(m1)):
            # m1
            if m1[i] != '':
                if not flag:
                    message = Chain()
                message = message.text(m1[i])
                flag = True
            # m0
            if i < len(m0):
                if m0[i] == '[pixiv]':
                    if flag:
                        await poke_message_send(message, self.event, self.instance)
                        flag = False
                    res = await http_requests.get(
                        'https://www.pixivs.cn/ajax/illust/discovery?mode=safe&max=1&_vercel_no_cache=1',
                        headers=request_headers)
                    result = json.loads(res)
                    if result['illusts'][0].get('id'):
                        illust = result['illusts'][0]
                    else:
                        illust = result['illusts'][1]
                    img_url = get_url(illust['id'])
                    img_name = illust['title']
                    img_author = illust['userName']
                    img_pid = illust['id']
                    img = await download_async(img_url, request_headers)
                    message = Chain().at(data['fromId']).text(
                        '\n标题：' + img_name + '\n作者：' + img_author + '\nPID：' + str(img_pid)).image(img)
                    await poke_message_send(message, self.event, self.instance)
                elif m0[i] == '[poke]':
                    if flag:
                        await poke_message_send(message, self.event, self.instance)
                        flag = False
                    await self.helper.send_nudge(data['fromId'], data['subject']['id'], data['subject']['kind'])
                elif m0[i].startswith('[face'):
                    if not flag:
                        message = Chain()
                        flag = True
                    id_ = int(m0[i].split(' ')[1].split(']')[0])
                    message = message.face(id_)
                else:
                    if not flag:
                        message = Chain()
                        flag = True
                    message = message.text(m0[i])
        if flag:
            await poke_message_send(message, self.event, self.instance)
        return

    async def set_group_card(self, group, target, card):
        res = await self.helper.member_info(group, target, name=card)
        result = json.loads(res)
        if result['code'] == 0:
            return True
        else:
            return False

    async def set_group_special_title(self, group, target, title):
        res = await self.helper.member_info(group, target, special_title=title)
        result = json.loads(res)
        if result['code'] == 0:
            return True
        else:
            return False

    async def new_friend_request(self, operator: int):
        data = self.event.data
        text = f'请求人：{data["nick"]}\n请求人QQ：{data["fromId"]}\n'
        if data['groupId'] != 0:
            text += f'来自群聊：{data["groupId"]}\n'
        text += f'请求信息：{data["message"]}'
        message = Chain().text(
            f'收到新的好友请求\n{text}\n发送"兔兔同意好友 [QQ号] [回复信息]"以同意请求\n发送"兔兔拒绝好友 [QQ号]"以拒绝请求\n发送"兔兔拉黑好友 ['
            f'QQ号]"以拉黑请求')
        await self.instance.send_message(message, str(operator))
        return

    async def new_friend_request_handle(self, event_id: int, from_id: int, group_id: int, operate: int,
                                        message: str = ''):
        res = await self.helper.new_friend_request_event(event_id, from_id, group_id, operate, message)
        result = json.loads(res)
        if result['code'] == 0:
            return True
        else:
            return False

    async def group_invite(self, operator: int):
        data = self.event.data
        text = f'邀请人：{data["nick"]}\n邀请人QQ：{data["fromId"]}\n群聊：{data["groupName"]}\n群号：{data["groupId"]}\n邀请信息：{data["message"]}'
        message = Chain().text(
            f'收到新的群聊邀请\n{text}\n发送"兔兔同意邀请 [群号] [回复消息]"以同意邀请\n发送"兔兔拒绝邀请 [群号] [回复消息]"以拒绝邀请')
        await self.instance.send_message(message, str(operator))
        return

    async def group_invite_handle(self, event_id: int, from_id: int, group_id: int, operate: int, message: str = ''):
        res = await self.helper.bot_invited_join_group_request_event(event_id, from_id, group_id, operate, message)
        result = json.loads(res)
        if result['code'] == 0:
            return True
        else:
            return False

    async def recall(self, message: dict):
        message_id = message['id']
        if message['groupId'] != 0:
            target = message['groupId']
            res = await self.helper.recall(target, message_id)
            result = json.loads(res)
            if result['code'] == 0:
                return True
        return False

    async def get_group_member_info(self, target: int, member_id: int):
        res = await self.helper.member_profile(target, member_id)
        result = json.loads(res)
        if result['code'] == 0:
            return result['data']
        else:
            return False
