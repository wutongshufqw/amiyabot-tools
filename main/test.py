# 放置试验性功能
import re
import sys

from amiyabot import Message, Chain, Event, CQHttpBotInstance

from core import Admin

from .main import bot
from ..api import GOCQTools
from ..utils import OddText


class _Autonomy(object):
    """
   自定义变量的write方法
   """

    def __init__(self, data: Message):
        """
        init
        """
        self.buff = []

    def write(self, out_stream):
        """
        :param out_stream:
        :return:
        """
        self.buff.append(out_stream)


@bot.on_message(keywords=re.compile(r'^code py\s([\s\S]*)$'), allow_direct=True, check_prefix=False, level=5)
async def code_py(data: Message):
    if not bool(Admin.get_or_none(account=data.user_id)):
        return
    match = re.match(r'^code py\s([\s\S]*)$', data.text_original)
    if match:
        code = match.group(1)
        current = sys.stdout
        temp = _Autonomy(data)
        sys.stdout = temp
        try:
            exec(code)
        except Exception as e:
            print(e)
        finally:
            sys.stdout = current
        return Chain(data).text('执行完成\n' + '\n'.join(temp.buff))


@bot.on_event('notice.group_ban')
async def group_ban_ban(event: Event, instance: CQHttpBotInstance):
    white_list = [
        587250095
    ]
    if event.data['sub_type'] == 'ban' and event.data['group_id'] in white_list:
        gocq = GOCQTools(instance, event=event)
        await gocq.ban(event.data['group_id'], event.data['user_id'], 0)


async def odd_verify(data: Message):
    keywords = OddText().keywords
    if data.text_original.startswith(tuple(keywords)):
        msgs = data.text_original.split(' ')
        if len(msgs) > 1:
            return True, 5
    return False


@bot.on_message(verify=odd_verify, allow_direct=True, check_prefix=False)
async def odd_text(data: Message):
    msgs = data.text_original.split(' ')
    cmd = OddText.get_command(msgs[0])
    if cmd:
        res = cmd.func(' '.join(msgs[1:]))
        return Chain(data, at=False).text(res)
