import asyncio
import re
import zipfile
from pathlib import Path
from typing import List, Union

from amiyabot import Message, Chain

from core import log


def unzip_file(ori_path, goal_path):
    """
    解决解压zip包时的中文乱码问题
    :param oriPath: 压缩文件的地址
    :param goalPath: 解压后存放的的目标位置
    :return: None
    """
    with zipfile.ZipFile(ori_path, 'r') as zf:
        # 解压到指定目录,首先创建一个解压目录
        if not Path(goal_path).exists():
            Path(goal_path).mkdir()
        for old_name in zf.namelist():
            # 获取文件大小，目的是区分文件夹还是文件，如果是空文件应该不好用。
            file_size = zf.getinfo(old_name).file_size
            # 由于源码遇到中文是cp437方式，所以解码成gbk，windows即可正常
            new_name = Path(old_name.encode('cp437').decode('gbk'))
            # 拼接文件的保存路径
            new_name = Path(goal_path).joinpath(new_name)
            # 判断是文件夹还是文件
            if file_size > 0:
                # 文件直接写入
                with open(new_name, 'wb') as f:
                    f.write(zf.read(old_name))
            else:
                # 文件夹创建
                new_name.mkdir(parents=True, exist_ok=True)


def run_async(func):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        loop.create_task(func())
    else:
        asyncio.run(func())


class DummyList(list):
    def __init__(self, l: List[int]):
        super().__init__(l)

    def __contains__(self, o: object) -> bool:
        if type(o) is set:
            for x in self:
                if x in o:
                    return True
            return False
        return super().__contains__(o)


def parse_condition(cond: str):
    """
    解析条件
    :param cond:
    :return:
    """
    reg_attr = re.compile(r'[A-Z]{3}')
    cond2 = (
        reg_attr.sub(
            lambda m: f'getattr(x, "{m.group()}")', cond.replace('AEVT', 'AVT')
        )
        .replace('?[', ' in DummyList([')
        .replace('![', ' not in DummyList([')
        .replace(']', '])')
        .replace('|', ' or ')
    )
    while True:
        try:
            func = eval(f'lambda x: {cond2}')
            func.__doc__ = cond2
            return func
        except Exception:
            log.warning(f'缺失 ) in {cond}')
            cond2 += ')'


async def send_msgs(data: Message, msgs: List[Chain], interval: float = 1):
    """
    发送多条消息
    :param data: 消息
    :param msgs: 消息列表
    :param interval: 间隔
    :return:
    """
    for msg in msgs:
        await data.send(msg)
        await asyncio.sleep(interval)
