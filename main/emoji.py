import os
import shutil
from core import log, GitAutomation

resources_dir = 'resource/plugins/tools'
import_success = True

# 尝试导入表情包组件
try:
    try:
        import imageio
        import numpy
        import cv2
        import typing_extensions
        import httpx
        import aiofiles
        import aiocache
        import emoji
        import fontTools
        import PIL
        import pydantic
        import matplotlib
        import bbcode
        import anyio
        import msgpack
        import ujson
        import pygtrie
    except ImportError as e:
        log.warning("Some requirements are missing, trying to fix...")
        log.info("Installing requirements...")
        os.system(f"cd {os.path.dirname(__file__)}/../ && pip install -r requirements.txt")
        log.info("Requirements installed.")
    finally:
        log.info('检查资源文件更新...')
        git_url = 'https://gitlab.com/wutongshufqw/emoji-resources.git'
        GitAutomation(os.path.join(resources_dir, 'emoji_resources'), git_url).update()
        log.info('更新完成')
        # copy resources from bot resource
        shutil.rmtree(os.path.join(os.path.dirname(__file__), '../emoji/resources'), ignore_errors=True)
        shutil.copytree(os.path.join(resources_dir, 'emoji_resources'),
                        os.path.join(os.path.dirname(__file__), '../emoji/resources'),
                        ignore=shutil.ignore_patterns('*.git*', '*.git', 'README.md'))
except ImportError as e:
    import_success = False
    shutil.copy(os.path.join(os.path.dirname(__file__), '..', 'requirements.txt'), resources_dir)
    log.error(
        '表情包组件导入失败, 请检查是否为代码部署, 若为代码部署可以尝试安装`resource/plugins/tools/requirements.txt`中的依赖后重启')
    raise e

if import_success:
    import shlex
    import traceback
    from io import BytesIO
    from typing import Union, List

    from amiyabot import Equal, Message, Chain, MiraiBotInstance, CQHttpBotInstance

    from ..api import GOCQTools
    from ..api import MiraiTools
    from ..emoji import *
    from .main import bot, tool_is_close
    install_emoji()


@bot.on_message(keywords=Equal('兔兔头像表情包帮助'), level=5)
async def help_text(data: Message):
    if await tool_is_close(data.instance.appid, 1, 1, 8, data.channel_id):
        return False, 0
    if type(data.instance) is not CQHttpBotInstance:
        return Chain(data).text('该功能仅支持CQHttp适配器')
    return Chain(data).markdown('发送`兔兔头像表情包` 获取全部功能帮助\n\n发送`兔兔头像详解` 获取特殊用法帮助')


@bot.on_message(keywords=Equal('兔兔头像表情包'), level=5)
async def help_img(data: Message):
    if await tool_is_close(data.instance.appid, 1, 1, 8, data.channel_id):
        return False, 0
    if type(data.instance) is not CQHttpBotInstance:
        return Chain(data).text('该功能仅支持CQHttp适配器')
    img: BytesIO = await help_image(commands, int(data.channel_id))
    return Chain(data, at=False).image(img.getvalue())


def is_qq(msg: str) -> bool:
    return msg.isdigit() and 5 <= len(msg) <= 11


async def get_user_info(instance: Union[MiraiBotInstance, CQHttpBotInstance], user: UserInfo):
    if not user.qq:
        return

    if user.group:
        if type(instance) is MiraiBotInstance:
            mirai = MiraiTools(instance)
            info = await mirai.get_group_member_info(int(user.group), int(user.qq))
            user.name = info.get('nickname')
            user.gender = info.get('sex').lower()
        elif type(instance) is CQHttpBotInstance:
            gocq = GOCQTools(instance)
            info = await gocq.get_group_member_info(int(user.group), int(user.qq))
            user.name = info.get('card', '') or info.get('nickname')
            user.gender = info.get('sex')
    else:
        if type(instance) is MiraiBotInstance:
            mirai = MiraiTools(instance)
            info = await mirai.get_stranger_info(int(user.qq))
            user.name = info.get('nickname')
            user.gender = info.get('sex').lower()
        elif type(instance) is CQHttpBotInstance:
            gocq = GOCQTools(instance)
            info = await gocq.get_stranger_info(int(user.qq))
            user.name = info.get('nickname')
            user.gender = info.get('sex')


async def handle_user_args(instance, data: Message):
    users: List[UserInfo] = []
    args: List[str] = []
    msg = data.message.get('message')
    gocq = GOCQTools(instance)
    # 回复前置处理
    if msg[0].get('type') == "reply":
        # 当回复目标是自己时，去除隐式at自己
        msg_id = msg[0].get('data')["id"]
        source_msg = await gocq.get_message(int(msg_id))
        source_qq = str(source_msg['sender']['user_id'])
        # 隐式at和显示at之间还有一个文本空格
        while len(msg) > 1 and (
            msg[1].get('type') == 'at' or msg[1].get('type') == 'text' and msg[1].get('data')['text'].strip() == ""):
            if msg[1].get('type') == 'at' and msg[1].get('data')['qq'] == source_qq \
                or msg[1].get('type') == 'text' and msg[1].get('data')['text'].strip() == "":
                msg.pop(1)
            else:
                break

    for msg_seg in msg:
        if msg_seg.get('type') == "at":
            users.append(
                UserInfo(
                    qq=msg_seg.get('data')["qq"],
                    group=data.channel_id
                )
            )
        elif msg_seg.get('type') == "image":
            users.append(UserInfo(img_url=msg_seg.get('data')["url"]))
        elif msg_seg.get('type') == "reply":
            msg_id = msg_seg.get('data')["id"]
            source_msg = await gocq.get_message(int(msg_id))
            source_qq = str(source_msg['sender']['user_id'])
            msgs = Message(instance)
            msgs.message = source_msg['message']
            get_img = False
            for each_msg in msgs.message:
                if each_msg.get('type') == "image":
                    users.append(UserInfo(img_url=each_msg.get('data')["url"]))
                    get_img = True
            else:
                if not get_img:
                    users.append(UserInfo(qq=source_qq))
        elif msg_seg.get('type') == "text":
            raw_text = str(msg_seg.get('data')["text"])
            try:
                texts = shlex.split(raw_text)
            except Exception as e:
                log.warning(f"{e}")
                texts = raw_text.split()
            for text in texts:
                if is_qq(text):
                    users.append(UserInfo(qq=text))
                elif text == "自己":
                    users.append(
                        UserInfo(
                            qq=str(data.user_id),
                            group=str(data.channel_id)
                        )
                    )
                else:
                    text = text.strip()
                    if text:
                        args.append(text)

    if not users:
        users.append(UserInfo(qq=str(data.instance.appid), group=str(data.channel_id)))

    sender = UserInfo(qq=str(data.user_id))
    await get_user_info(instance, sender)

    for user in users:
        await get_user_info(instance, user)

    return users, sender, args


async def verify(data: Message):
    if await tool_is_close(data.instance.appid, 1, 1, 8, data.channel_id) or type(data.instance) is not CQHttpBotInstance:
        return False, 0

    command = petpet_handler.find_handle(data)
    if not command:
        return False, 0

    prefix = command.keywords[0]
    handle_group = str(data.channel_id)

    if handle_group not in banned_command:
        banned_command[handle_group] = []
    if prefix in banned_command["global"]:
        await data.send(Chain(data).text(f"{prefix}已被全局禁用"))
        return False, 0
    if command.keywords[0] in banned_command[handle_group]:
        await data.send(Chain(data).text(f"{prefix}已被本群禁用"))
        return False, 0
    log.info(f"Message {data.message_id} triggered {prefix}")

    if prefix == "随机表情":
        command = await command.func_random(commands, banned_command, handle_group)
        if command is None:
            await data.send(Chain(data, at=False).text("本群已没有可使用的表情了捏qwq"))
            return False, 0
        await data.send(Chain(data, at=False).text(f"随机到了【{command.keywords[0]}】"))
    users, sender, args = await handle_user_args(data.instance, data)

    if len(args) > command.arg_num:
        if bot.get_config('emoji').get('tips'):
            await data.send(Chain(data).text(f"参数过多，最多只能有{command.arg_num}个参数"))
        return False, 0
    return True, 5, {'command': command, 'sender': sender, 'users': users, 'args': args}


@bot.on_message(verify=verify, check_prefix=False)
async def handle(data: Message):
    info = data.verify.keypoint
    img: Union[BytesIO, bytes] = b''
    text: str = ''
    try:
        img = await make_image(
            command=info.get('command'),
            sender=info.get('sender'),
            users=info.get('users'),
            args=info.get('args'))
        img = img.getvalue()
    except Exception as e:
        log.error(traceback.format_exc())
        img = b''
        text = '表情生成失败了'

    return Chain(data, at=False).text(text).image(img)
