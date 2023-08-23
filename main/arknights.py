from amiyabot import Message, Chain
from core import log

from .main import bot, tool_is_close

from ..utils import SklandPlus, SQLHelper

BROWSER = 0


@bot.on_message(keywords=['设置凭证'], allow_direct=True, level=5)
async def set_skland(data: Message):
    if await tool_is_close(data.instance.appid, 1, 4, 1, data.channel_id):
        return
    res = await data.wait(Chain(data).image(await SklandPlus.get_tip()).text(
        '森空岛网址: \nhttps://www.skland.com/\n方法二代码:\nlocalStorage.getItem("SK_OAUTH_CRED_KEY");\n方法三代码:\njavascript:prompt(undefined, localStorage.getItem("SK_OAUTH_CRED_KEY"));'),
        max_time=120)
    if res:
        await data.recall()
        cred = res.text_original
        await SQLHelper.set_skland(int(data.user_id), cred)
        return Chain(data).text('设置成功')
    return Chain(data).text('操作超时')


@bot.on_message(keywords=['方舟数据'], allow_direct=True, level=5)
async def get_skland(data: Message):
    if await tool_is_close(data.instance.appid, 1, 4, 1, data.channel_id):
        return
    global BROWSER
    if BROWSER > 0:
        return Chain(data).text('有其他用户正在使用, 请稍后再试')
    BROWSER += 1
    try:
        cred = await SQLHelper.get_skland(int(data.user_id))
        if not cred:
            BROWSER -= 1
            return Chain(data).text('未设置凭证, 请发送兔兔设置凭证以配置凭证')
        cred = cred.cred
        url = bot.get_config('skland', 'https://laviniafalcone.github.io/Enhance-for-Skland/')
        sp = SklandPlus(cred, url)
        msg, info = await sp.login()
        if info == 'error':
            BROWSER -= 1
            return Chain(data).text(msg)
        elif info == 'warning':
            BROWSER -= 1
            return Chain(data).text(msg).image(await SklandPlus.get_tip()).text(
                '森空岛网址: \nhttps://www.skland.com/\n方法二代码:\nlocalStorage.getItem("SK_OAUTH_CRED_KEY");\n方法三代码:\njavascript:prompt(undefined, localStorage.getItem("SK_OAUTH_CRED_KEY"));',
                max_time=120)

        async def verify(message: Message):
            if message.text_original.isdigit():
                return True
            return False

        while True:
            res = await data.wait(Chain(data).text(
                '请选择账号(使用纯数字回复，如: 1)\nps: 若发现未有任何账号显示则表示凭证过期，请重新获取').image(msg),
                                  data_filter=verify, level=5)
            if res:
                msg, info = await sp.choose_account(int(res.text_original))
                if info == 'warning':
                    await data.send(Chain(data).text(msg))
                else:
                    BROWSER -= 1
                    return Chain(data).image(msg)
            else:
                BROWSER -= 1
                return Chain(data).text('操作超时')
    except Exception as e:
        log.error(e)
        BROWSER -= 1
        return Chain(data).text('操作超时')
