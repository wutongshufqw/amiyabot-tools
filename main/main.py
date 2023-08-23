import datetime
import os
import re
import shutil
import time
from typing import Optional

from amiyabot import Message
from amiyabot.builtin.messageChain import Chain
from amiyabot.factory import BotHandlerFactory

from core import AmiyaBotPluginInstance, log
from core.database.bot import Admin, connect_database
from core.util import create_dir, read_yaml
from ..config import tools, avatar_dir, bottle_dir

# 对数据库报错的修复
try:
    from ..utils import SQLHelper
except ValueError as e:
    log.warning(e.__str__())
    if e.__str__() == 'nickname is not null but has no default':
        import sqlite3

        conn = connect_database('resource/plugins/tools/tools.db')
        cursor = conn.cursor()
        cursor.execute('DROP TABLE IF EXISTS new_friends')
    from ..utils import SQLHelper

curr_dir = os.path.dirname(__file__)
recall_list = []


class ToolsPluginInstance(AmiyaBotPluginInstance):
    def install(self):
        install_main(self)


bot = ToolsPluginInstance(
    name='小工具合集',
    version='1.9.8.1',
    plugin_id='amiyabot-tools',
    plugin_type='tools',
    description='AmiyaBot小工具合集 By 天基',
    document=f'{curr_dir}/../README.md',
    instruction=f'{curr_dir}/../help.md',
    channel_config_default=f'{curr_dir}/../config/channel_config_default.json',
    channel_config_schema=f'{curr_dir}/../config/channel_config_schema.json',
    global_config_default=f'{curr_dir}/../config/global_config_default.json',
    global_config_schema=f'{curr_dir}/../config/global_config_schema.json',
)


def install_main(bot_: ToolsPluginInstance):
    config_file = 'resource/plugins/tools/config.yaml'
    if os.path.exists(config_file):
        config_ = read_yaml(config_file, _dict=True)
        for k, v in config_.items():
            bot_.set_config(k, v)
        os.remove(config_file)
    poke_ = bot_.get_config('poke').get('emojiPath')
    remove_dir(avatar_dir)
    create_dir(avatar_dir)
    create_dir(poke_)
    create_dir(bottle_dir)
    if bot.get_config('nickname'):
        bot_config = bot.get_config('nickname')
        if not bot_config.get('runtime'):
            bot_config['runtime'] = datetime.datetime.now().astimezone().isoformat()
        if not bot_config.get('diy'):
            bot_config['diy'] = []
        bot.set_config('nickname', bot_config)


def create_file(path: str, mode: str = 'a'):
    if not os.path.exists(path):
        create_dir(path, is_file=True)
    try:
        if mode.index('b') != -1:
            return open(path, mode)
    except ValueError:
        return open(path, mode, encoding='utf-8')


def remove_file(path: str):
    if os.path.exists(path):
        os.remove(path)


def remove_dir(path: str):
    if os.path.exists(path):
        shutil.rmtree(path)


def get_cooldown(flag, map_: dict):
    if not map_.__contains__(flag):
        return 0
    last = map_[flag]
    if time.time() >= last:
        return 0
    return 1


def set_cooldown(flag, map_, cd: int):
    map_[flag] = time.time() + cd


async def update_tools(data: Message):
    tool_list = await SQLHelper.get_tools_list(data.instance.appid)
    if tool_list is None or len(tool_list) == 0:
        for t in tools:
            await SQLHelper.add_tool(
                data.instance.appid,
                t['main_id'],
                t['sub_id'],
                t['sub_sub_id'],
                t['name'],
                False,
                bot.version,
            )
    elif tool_list[0].version != bot.version:
        for t in tools:
            flag = True
            for t1 in tool_list:
                if (
                    t['main_id'] == t1.main_id
                    and t['sub_id'] == t1.sub_id
                    and t['sub_sub_id'] == t1.sub_sub_id
                ):
                    await SQLHelper.update_tool(
                        t1.id, version=bot.version, name=t['name']
                    )
                    flag = False
                    break
            if flag:
                await SQLHelper.add_tool(
                    data.instance.appid,
                    t['main_id'],
                    t['sub_id'],
                    t['sub_sub_id'],
                    t['name'],
                    False,
                    bot.version,
                )


async def tool_is_close(
    appid: str,
    main_id: int,
    sub_id: int,
    sub_sub_id: int,
    channel_id: Optional[str] = None,
) -> bool:
    tool = await SQLHelper.get_tool(appid, main_id, sub_id, sub_sub_id)
    flag = False
    if tool is not None and tool.open:
        if channel_id is not None:
            ctl = await SQLHelper.get_channel_tool(tool.id, channel_id)
            flag = True if ctl is None else ctl.open
        else:
            flag = True
    return not flag


async def get_tool_list(appid: str) -> list:
    list_ = await SQLHelper.get_tools_list(appid)
    config_ = bot.get_config('functions')
    tool_list = []
    for t in list_:
        if (
            config_.get('default', False)
            and t.main_id == 1
            and t.sub_id == 1
            and t.sub_sub_id != 8
        ):
            tool_list.append(t)
        if (
            config_.get('emoji', False)
            and t.main_id == 1
            and t.sub_id == 1
            and t.sub_sub_id == 8
        ):
            tool_list.append(t)
        if config_.get('game', False) and t.main_id == 1 and t.sub_id == 2:
            tool_list.append(t)
        if config_.get('group', False) and t.main_id == 1 and t.sub_id == 3:
            tool_list.append(t)
        if config_.get('arknights', False) and t.main_id == 1 and t.sub_id == 4:
            tool_list.append(t)
        if config_.get('admin', False) and t.main_id == 2 and t.sub_id == 1:
            tool_list.append(t)
    return tool_list


# 功能管理
@bot.on_message(keywords=['小工具全局管理'], allow_direct=True, level=5)
async def tools_manage(data: Message):
    if bool(Admin.get_or_none(account=data.user_id)):
        await update_tools(data)
        limit_time = time.time() + 60
        flag = True
        tool_list = await get_tool_list(data.instance.appid)
        msg = Chain(data)
        text = '功能列表：\n'
        for i in range(len(tool_list)):
            text += f"{i}. {tool_list[i].tool_name} {'[已开启]' if tool_list[i].open else '[已关闭]'}\n"
        text += '请输入序号开启或关闭功能\n回复“退出”退出'
        msg.text(text)
        while True:
            if flag:
                reply = await data.wait(msg, True, int(limit_time - time.time()))
                flag = False
            else:
                reply = await data.wait(
                    force=True, max_time=int(limit_time - time.time())
                )
            if reply:
                if reply.text == '退出':
                    msg = Chain(data).text('已退出')
                    await data.send(msg)
                    break
                pattern = re.compile(r'^\D*(\d+).*$')
                match = pattern.match(reply.text_digits)
                if match:
                    index = int(match.group(1))
                    if 0 <= index < len(tool_list):
                        tool_list[index].open = not tool_list[index].open
                        await SQLHelper.update_tool(
                            tool_list[index].id, open_=tool_list[index].open
                        )
                        await data.send(
                            Chain(data).text(
                                f"已{'开启' if tool_list[index].open else '关闭'}{tool_list[index].tool_name}"
                            )
                        )
                        limit_time = time.time() + 60
                    else:
                        msg = Chain(data).text('输入序号有误')
                        await data.send(msg)
                        limit_time = time.time() + 60
            else:
                msg = Chain(data).text('已退出')
                await data.send(msg)
                break


@bot.on_message(keywords=['小工具管理'], allow_direct=False, level=5)
async def tools_manage_channel(data: Message):
    if data.is_admin or bool(Admin.get_or_none(account=data.user_id)):
        await update_tools(data)
        limit_time = time.time() + 60
        flag = True
        tool_list = await get_tool_list(data.instance.appid)
        msg = Chain(data)
        ctl = []
        for t in tool_list:
            if t.main_id == 1 and t.open:
                tl = await SQLHelper.get_channel_tool(t.id, data.channel_id)
                if tl is not None:
                    t.open = tl.open
                ctl.append(t)
        text = '功能列表：\n'
        for i in range(len(ctl)):
            text += f"{i}. {ctl[i].tool_name} {'[已开启]' if ctl[i].open else '[已关闭]'}\n"
        text += '请输入序号开启或关闭功能\n回复“退出”退出'
        msg.text(text)
        while True:
            if flag:
                reply = await data.wait(msg, True, int(limit_time - time.time()))
                flag = False
            else:
                reply = await data.wait(
                    force=True, max_time=int(limit_time - time.time())
                )
            if reply:
                if reply.text == '退出':
                    msg = Chain(data).text('已退出')
                    await data.send(msg)
                    break
                pattern = re.compile(r'^\D*(\d+).*$')
                match = pattern.match(reply.text_digits)
                if match:
                    index = int(match.group(1))
                    if 0 <= index < len(ctl):
                        ctl[index].open = not ctl[index].open
                        await SQLHelper.update_channel_tool(
                            ctl[index].id, data.channel_id, open_=ctl[index].open
                        )
                        await data.send(
                            Chain(data).text(
                                f"已{'开启' if ctl[index].open else '关闭'}{ctl[index].tool_name}"
                            )
                        )
                        limit_time = time.time() + 60
                    else:
                        msg = Chain(data).text('输入序号有误')
                        await data.send(msg)
                        limit_time = time.time() + 60
            else:
                msg = Chain(data).text('已退出')
                await data.send(msg)
                break


# 撤回控制
# noinspection PyUnusedLocal
@bot.timed_task(each=1)
async def _(instance: BotHandlerFactory):
    for recall_ in recall_list:
        if recall_.__contains__('res') and recall_.__contains__('time'):
            r = recall_['res']
            t = recall_['time']
            cur = time.time()
            if r and cur > t:
                await r.recall()
                recall_list.remove(recall_)
