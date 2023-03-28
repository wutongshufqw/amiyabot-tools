from amiyabot import Event
from amiyabot.adapters import BotAdapterProtocol
from amiyabot.adapters.cqhttp import CQHttpBotInstance
from amiyabot.adapters.mirai import MiraiBotInstance

request_headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 '
                  'Safari/537.36',
    'accept': '*/*',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Content-Type': 'application/json;charset=UTF-8'
}


def get_url(id_):
    return 'https://pixiv.re/' + id_ + '.jpg'


async def poke_message_send(message_, event: Event, instance: BotAdapterProtocol):
    if type(instance) is MiraiBotInstance:
        if event.data['subject']['kind'] == 'Group':
            await instance.send_message(message_, channel_id=event.data['subject']['id'])
        elif event.data['subject']['kind'] == 'Friend':
            await instance.send_message(message_, user_id=event.data['subject']['id'])
    elif type(instance) is CQHttpBotInstance:
        if 'group_id' in event.data:
            await instance.send_message(message_, channel_id=event.data['group_id'])
        else:
            await instance.send_message(message_, user_id=event.data['sender_id'])
    return
