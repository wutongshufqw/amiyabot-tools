# 放置试验性功能
import re
import sys

from amiyabot import Message, Chain
from core import Admin

from .main import bot


class __Autonomy__(object):
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
        temp = __Autonomy__(data)
        sys.stdout = temp
        try:
            exec(code)
        except Exception as e:
            print(e)
        finally:
            sys.stdout = current
        return Chain(data).text('执行完成\n' + '\n'.join(temp.buff))
    return
