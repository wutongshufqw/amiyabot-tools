# 放置试验性功能
import random
import re
import sys
from datetime import datetime

from amiyabot import Message, Chain, Event, CQHttpBotInstance, Equal, MiraiBotInstance
from amiyabot.adapters.cqhttp import CQHTTPForwardMessage
from amiyabot.adapters.mirai import MiraiForwardMessage
from amiyabot.factory import BotHandlerFactory

from core import bot as main_bot, log
from core.database.bot import Admin
from .main import bot, tool_is_close, curr_dir
from ..api import GOCQTools
from ..utils import OddText
try:
    from ..utils.immortal import Immortal
except ImportError as e:
    log.warning(f'加载Immortal模块失败: {e}')
    raise e

double_exp_limit = 3


class _Autonomy(object):
    """
   自定义变量的write方法
   """

    def __init__(self):
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
        temp = _Autonomy()
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


async def send_message_to_superuser(msg: str):
    config_ = bot.get_config('superuser')
    if config_ is not None:
        for i in config_:
            for j in main_bot:
                try:
                    await j.send_message(Chain().text(msg), str(i))
                except AttributeError:
                    pass


def is_superuser(user_id: int) -> bool:
    config_ = bot.get_config('superuser')
    if config_ is not None:
        for i in config_:
            if i == user_id:
                return True
    return False


# 修仙插件 start
# 定时任务
# 1.重置签到
@bot.timed_task(sub_tag='immortal_sign_reset', trigger='cron', hour=0, minute=0)
async def sign_reset(instance: BotHandlerFactory):
    Immortal.sql_manager().sign_reset()
    await send_message_to_superuser('修仙签到重置成功!')


# 2.重置双修次数, 用户宗门任务次数, 宗门丹药领取次数
@bot.timed_task(sub_tag='immortal_double_exp_reset', trigger='cron', hour=0, minute=0)
async def double_exp_reset(instance: BotHandlerFactory):
    Immortal.double_exp_cd().re_data()
    await send_message_to_superuser('双修次数已更新!')


# 3.每日某1小时按照宗门贡献度增加资材
@bot.timed_task(sub_tag='immortal_material_update', trigger='cron', hour=Immortal.sect_config()['发放宗门资材']['时间'])
async def immortal_material_update(instance: BotHandlerFactory):
    all_sects = Immortal.sql_manager().get_all_sects_id_scale()
    for s in all_sects:
        Immortal.sql_manager().update_sect_materials(
            sect_id=s.sect_id, sect_materials=s.sect_scale * Immortal.sect_config()['发放宗门资材']['倍率'], key=1
        )

    await send_message_to_superuser('已更新所有宗门的资材!')


# 4.每日0点重置用户宗门任务次数、宗门丹药领取次数
@bot.timed_task(sub_tag='immortal_reset_user_task', trigger='cron', hour=0, minute=0)
async def reset_user_task(instance: BotHandlerFactory):
    Immortal.sql_manager().sect_task_reset()
    Immortal.sql_manager().sect_elixir_get_num_reset()
    all_sects = Immortal.sql_manager().get_all_sects_id_scale()
    for s in all_sects:
        sect_info = Immortal.sql_manager().get_sect_info(s[0])
        if int(sect_info.elixir_room_level) != 0:
            elixir_room_cost = \
                Immortal.sect_config()['宗门丹房参数']['elixir_room_level'][str(sect_info.elixir_room_level)][
                    'level_up_cost'][
                    '建设度']
            if sect_info.sect_materials < elixir_room_cost:
                await send_message_to_superuser(f'宗门{sect_info.sect_name}的资材无法维持丹房')
                continue
            else:
                Immortal.sql_manager().update_sect_materials(
                    sect_id=sect_info.sect_id, sect_materials=elixir_room_cost, key=2
                )
    await send_message_to_superuser('已重置用户宗门任务次数、宗门丹药领取次数, 已扣除丹房维护费')


# 功能函数
# 基础功能
# 0. 修仙帮助
@bot.on_message(keywords=Equal('修仙帮助'), check_prefix=False, level=5)
async def immortal_help(data: Message):
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    msg = Immortal.help()
    return Chain(data).markdown(msg, is_dark=True)


# 1.我要修仙: 进入修仙模式
@bot.on_message(keywords=Equal('我要修仙'), check_prefix=False, level=8)
async def immortal_start(data: Message):
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    user_id = int(data.user_id)
    user_name = data.nickname
    root, root_type = Immortal.new_json_data().get_linggen()  # 获取灵根，灵根类型
    rate = Immortal.sql_manager().get_root_rate(root_type)  # 获取灵根倍率
    power = 100 * float(rate)  # 战力 = 境界的power字段 * 灵根的rate字段
    create_time = datetime.now()
    success = Immortal.sql_manager().create_user(user_id, root, root_type, int(power), create_time, user_name)
    if success:
        return Chain(data).html(
            f'{curr_dir}/../template/html/immortal/start.html',
            {'msg': '欢迎进入修仙世界', 'root': root, 'root_type': root_type, 'power': power},
            700, 300
        )
    else:
        return Chain(data).text('您已迈入修仙世界，输入 [我的修仙信息] 获取数据吧！')


# 2.我的修仙信息: 获取修仙数据
@bot.on_message(keywords=[Equal('我的修仙信息'), Equal('我的存档')], check_prefix=False, level=23)
async def immortal_info(data: Message):
    """我的修仙信息"""
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    is_user, user_info, msg = Immortal.utils().check_user(data)
    if not is_user:
        return Chain(data).text(msg)
    user_id = user_info.user_id
    user_info = Immortal.sql_manager().get_user_real_info(user_id)
    user_name = user_info.user_name
    user_num = user_info.id
    user_rank = Immortal.sql_manager().get_exp_rank(user_id)
    user_stone = Immortal.sql_manager().get_stone_rank(user_id)
    if not user_name:
        user_name = '佚名(发送改名+道号修改)'

    level_rate = Immortal.sql_manager().get_root_rate(user_info.root_type)  # 灵根倍率
    realm_rate = Immortal.json_data().level_data()[user_info.level]['spend']  # 境界倍率
    sect_id = user_info.sect_id
    if sect_id:
        sect_info = Immortal.sql_manager().get_sect_info(sect_id)
        sect_msg = sect_info.sect_name
        sect_zw = Immortal.json_data().sect_config_data()[str(user_info.sect_position)]['title']
    else:
        sect_msg = '无宗门'
        sect_zw = '无'

    # 判断突破的修为
    list_all = len(Immortal.other_set().level) - 1
    now_index = Immortal.other_set().level.index(user_info.level)
    if list_all == now_index:
        exp_meg = '位面至高'
    else:
        is_up_data_level = Immortal.other_set().level[now_index + 1]
        need_exp = Immortal.sql_manager().get_level_power(is_up_data_level)
        get_exp = need_exp - user_info.exp
        if get_exp > 0:
            exp_meg = f'还需{get_exp}修为可突破!'
        else:
            exp_meg = '可突破!'

    user_buff_data = Immortal.buff_data(user_id)
    user_main_buff_data = user_buff_data.get_user_main_buff_data()
    user_sec_buff_data = user_buff_data.get_user_sec_buff_data()
    user_weapon_data = user_buff_data.get_user_weapon_data()
    user_armor_data = user_buff_data.get_user_armor_buff_data()
    main_buff_name = '无'
    sec_buff_name = '无'
    weapon_name = '无'
    armor_name = '无'
    if user_main_buff_data:
        main_buff_name = f'{user_main_buff_data["name"]}({user_main_buff_data["level"]})'
    if user_sec_buff_data:
        sec_buff_name = f'{user_sec_buff_data["name"]}({user_sec_buff_data["level"]})'
    if user_weapon_data:
        weapon_name = f'{user_weapon_data["name"]}({user_weapon_data["level"]})'
    if user_armor_data:
        armor_name = f'{user_armor_data["name"]}({user_armor_data["level"]})'

    info = {
        '道号': f'{user_name}',
        '境界': f'{user_info.level}',
        '修为': f'{Immortal.utils().number_to(user_info.exp)}',
        '灵石': f'{Immortal.utils().number_to(user_info.stone)}',
        '战力': f'{Immortal.utils().number_to(int(user_info.exp * level_rate * realm_rate))}',
        '灵根': f'{user_info.root}({user_info.root_type}+{int(level_rate * 100)}%)',
        '突破状态': f'{exp_meg} 概率：{Immortal.json_data().level_rate_data()[user_info.level] + int(user_info.level_up_rate)}%',
        '攻击力': f'{Immortal.utils().number_to(user_info.atk)}，攻修等级{user_info.atk_practice}级',
        '所在宗门': sect_msg,
        '宗门职位': sect_zw,
        '主修功法': main_buff_name,
        '副修神通': sec_buff_name,
        "法器": weapon_name,
        "防具": armor_name,
        '注册位数': f'道友是踏入修仙世界的第{int(user_num)}人',
        '修为排行': f'道友的修为排在第{int(user_rank)}位',
        '灵石排行': f'道友的灵石排在第{int(user_stone)}位',
    }

    msg = '<div align="center">\n\n# ✨修仙信息✨\n\n</div>\n\n'
    for k, v in info.items():
        msg += f'**{k}**: {v}\n\n'
    return Chain(data).markdown(msg, is_dark=True)


# 3.修仙签到: 获取灵石及修为
@bot.on_message(keywords=Equal('修仙签到'), check_prefix=False, level=13)
async def immortal_sign(data: Message):
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    is_user, user_info, msg = Immortal.utils().check_user(data)
    if not is_user:
        return Chain(data).text(msg)
    user_id = user_info.user_id
    msg = Immortal.sql_manager().get_sign(user_id)
    return Chain(data).text(msg)


# 4.重入仙途: 重置灵根数据,每次{immortal_config.remake}灵石
@bot.on_message(keywords=Equal('重入仙途'), check_prefix=False, level=7)
async def immortal_restart(data: Message):
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    is_user, user_info, msg = Immortal.utils().check_user(data)
    if not is_user:
        return Chain(data).text(msg)
    user_id = user_info.user_id
    root, root_type = Immortal.new_json_data().get_linggen()  # 获取灵根，灵根类型
    result, power = Immortal.sql_manager().remake(root, root_type, user_id)
    if result:
        return Chain(data).html(
            f'{curr_dir}/../template/html/immortal/start.html',
            {'msg': '逆天之行，重获新生', 'root': root, 'root_type': root_type, 'power': power},
            700, 300
        )
    else:
        return Chain(data).text('你的灵石还不够呢，快去赚点灵石吧！')


# 5.改名 <新的名字>: 修改你的道号
@bot.on_message(keywords=re.compile(r'^改名\s([\s\S]+)$'), check_prefix=False, level=5)
async def immortal_rename(data: Message):
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    is_user, user_info, msg = Immortal.utils().check_user(data)
    if not is_user:
        return Chain(data).text(msg)
    user_id = user_info.user_id
    match = re.match(r'^改名\s([\s\S]+)$', data.text_original)
    user_name = match.group(1)
    len_name = len(user_name.encode('gbk'))
    if len_name > 20:
        return Chain(data).text('道号长度过长，请修改后重试！')
    msg = Immortal.sql_manager().rename(user_id, user_name)
    return Chain(data).text(msg)


# 6.闭关、出关、灵石出关、灵石修仙、双修: 修炼增加修为,挂机功能
@bot.on_message(keywords=Equal('闭关'), check_prefix=False, level=5)
async def immortal_in_closing(data: Message):
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    user_type = 1  # 状态0为无事件
    is_user, user_info, msg = Immortal.utils().check_user(data)
    if not is_user:
        return Chain(data).text(msg)
    user_id = user_info.user_id
    is_type, msg = Immortal.utils().check_user_type(user_id, 0)
    if is_type:  # 符合
        Immortal.sql_manager().in_closing(user_id, user_type)
        msg = "进入闭关状态，如需出关，发送 [出关] ！"
        return Chain(data).text(msg)
    else:
        return Chain(data).text(msg)


@bot.on_message(keywords=[Equal('出关'), Equal('灵石出关')], check_prefix=False, level=5)
async def immortal_out_closing(data: Message):
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    user_type = 0  # 状态0为无事件
    is_user, user_info, msg = Immortal.utils().check_user(data)
    if not is_user:
        return Chain(data).text(msg)
    user_id = user_info.user_id
    user_msg = Immortal.sql_manager().get_user_message(user_id)
    level = user_msg.level
    user_exp = user_msg.exp
    hp_speed = 25
    mp_speed = 50

    max_exp = int(Immortal.other_set().set_closing_type(level)) * Immortal.get_config().closing_exp_upper_limit
    user_get_exp_max = int(max_exp) - user_exp

    if user_get_exp_max < 0:
        user_get_exp_max = 0

    now_time = datetime.now()
    user_cd_msg = Immortal.sql_manager().get_user_cd(user_id)
    is_type, msg = Immortal.utils().check_user_type(user_id, 1)
    if is_type:  # 符合
        in_closing_time = user_cd_msg.create_time  # 进入闭关的时间
        exp_time = Immortal.other_set().date_diff(now_time, in_closing_time) // 60  # 闭关时长计算(分钟) = second // 60
        level_rate = Immortal.sql_manager().get_root_rate(user_msg.root_type)  # 灵根倍率
        realm_rate = Immortal.json_data().level_data()[level]['spend']  # 境界倍率
        user_buff_data = Immortal.buff_data(user_id)
        main_buff_data = user_buff_data.get_user_main_buff_data()
        main_buff_rate_buff = main_buff_data.get('ratebuff', 0) if main_buff_data else 0  # 功法修炼倍率
        # 本次闭关获取的修为
        exp = int((exp_time * Immortal.get_config().closing_exp) * (
            level_rate * realm_rate * (1 + main_buff_rate_buff)))  # 洞天福地为加法
        # 计算传承增益
        impart_data = Immortal.impart_data().get_user_message(user_id)
        impart_exp_up = impart_data.impart_exp_up if impart_data else 0
        exp = int(exp * (1 + impart_exp_up))
        if exp > user_get_exp_max:
            # 用户获取的修为到达上限
            Immortal.sql_manager().in_closing(user_id, user_type)
            Immortal.sql_manager().update_exp(user_id, user_get_exp_max)
            Immortal.sql_manager().update_power2(user_id)  # 更新战力

            result_msg, result_hp_mp = Immortal.other_set().send_hp_mp(user_id, int(exp * hp_speed),
                                                                       int(exp * mp_speed))
            Immortal.sql_manager().update_user_attribute(user_id, result_hp_mp[0], result_hp_mp[1],
                                                         int(result_hp_mp[2] / 10))
            msg = f'闭关结束, 本次闭关到达上限, 共增加\n修为: {user_get_exp_max}\n{result_msg[0]}\n{result_msg[1]}'
            return Chain(data).text(msg)
        else:
            # 用户获取的修为没有到达上限
            if data.text_original == '灵石出关':
                user_stone = user_msg.stone  # 用户灵石数
                if user_stone <= 0:
                    user_stone = 0
                if exp <= user_stone:
                    exp = exp * 2
                    Immortal.sql_manager().in_closing(user_id, user_type)
                    Immortal.sql_manager().update_exp(user_id, exp)
                    Immortal.sql_manager().update_ls(user_id, int(exp / 2), 2)
                    Immortal.sql_manager().update_power2(user_id)  # 更新战力

                    result_msg, result_hp_mp = Immortal.other_set().send_hp_mp(user_id, int(exp * hp_speed),
                                                                               int(exp * mp_speed))
                    Immortal.sql_manager().update_user_attribute(user_id, result_hp_mp[0], result_hp_mp[1],
                                                                 int(result_hp_mp[2] / 10))
                    msg = f'闭关结束，共闭关{exp_time}分钟，本次闭关增加修为: {exp}\n消耗灵石{int(exp / 2)}枚\n{result_msg[0]}\n{result_msg[1]}'
                    return Chain(data).text(msg)
                else:
                    exp = exp + user_stone
                    Immortal.sql_manager().in_closing(user_id, user_type)
                    Immortal.sql_manager().update_exp(user_id, exp)
                    Immortal.sql_manager().update_ls(user_id, user_stone, 2)
                    Immortal.sql_manager().update_power2(user_id)  # 更新战力

                    result_msg, result_hp_mp = Immortal.other_set().send_hp_mp(user_id, int(exp * hp_speed),
                                                                               int(exp * mp_speed))
                    Immortal.sql_manager().update_user_attribute(user_id, result_hp_mp[0], result_hp_mp[1],
                                                                 int(result_hp_mp[2] / 10))
                    msg = f'闭关结束，共闭关{exp_time}分钟，本次闭关增加修为: {exp}\n消耗灵石{user_stone}枚\n{result_msg[0]}\n{result_msg[1]}'
                    return Chain(data).text(msg)
            else:
                Immortal.sql_manager().in_closing(user_id, user_type)
                Immortal.sql_manager().update_exp(user_id, exp)
                Immortal.sql_manager().update_power2(user_id)

                result_msg, result_hp_mp = Immortal.other_set().send_hp_mp(user_id, int(exp * hp_speed),
                                                                           int(exp * mp_speed))
                Immortal.sql_manager().update_user_attribute(user_id, result_hp_mp[0], result_hp_mp[1],
                                                             int(result_hp_mp[2] / 10))
                msg = f'闭关结束，共闭关{exp_time}分钟，本次闭关增加修为: {exp}\n{result_msg[0]}\n{result_msg[1]}'
                return Chain(data).text(msg)
    else:
        return Chain(data).text(msg)


@bot.on_message(keywords=re.compile(r'^灵石(修仙|修炼)\s?(\d+)$'), check_prefix=False, level=5)
async def immortal_ls_closing(data: Message):
    """灵石修炼"""
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    is_user, user_info, msg = Immortal.utils().check_user(data)
    if not is_user:
        return Chain(data).text(msg)
    user_id = user_info.user_id
    user_msg = Immortal.sql_manager().get_user_message(user_id)  # 获取用户信息
    level = user_msg.level
    user_exp = user_msg.exp
    user_stone = user_msg.stone  # 用户灵石数
    max_exp = int(Immortal.other_set().set_closing_type(level)) * Immortal.get_config().closing_exp_upper_limit
    user_get_exp_max = int(max_exp) - user_exp

    if user_get_exp_max < 0:
        # 校验当当前修为超出上限的问题，不可为负数
        user_get_exp_max = 0

    match = re.match(r'^灵石(修仙|修炼)\s?(\d+)$', data.text_original)
    stone_num = match.group(2)
    if not stone_num:
        return Chain(data).text('请输入正确的灵石数量!')
    stone_num = int(stone_num)
    if stone_num > user_stone:
        return Chain(data).text('你的灵石还不够呢，快去赚点灵石吧!')

    exp = int(stone_num / 10)
    if exp >= user_get_exp_max:
        # 用户获取的修为到达上限
        Immortal.sql_manager().update_exp(user_id, user_get_exp_max)
        Immortal.sql_manager().update_power2(user_id)  # 更新战力
        msg = f'修炼结束, 本次修炼到达上限, 共增加修为: {user_get_exp_max}\n消耗灵石{int(user_get_exp_max * 10)}枚'
        Immortal.sql_manager().update_ls(user_id, int(user_get_exp_max * 10), 2)
        return Chain(data).text(msg)
    else:
        # 用户获取的修为没有到达上限
        Immortal.sql_manager().update_exp(user_id, exp)
        Immortal.sql_manager().update_power2(user_id)
        msg = f'修炼结束, 本次修炼共增加修为: {exp}\n消耗灵石{stone_num}枚'
        Immortal.sql_manager().update_ls(user_id, stone_num, 2)
        return Chain(data).text(msg)


@bot.on_message(keywords=Equal('双修'), check_prefix=False, level=5)
async def immortal_double_closing(data: Message):
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    global double_exp_limit
    is_user, user_1, msg = Immortal.utils().check_user(data)
    if not is_user:
        return Chain(data).text(msg)

    if len(data.at_target) > 1:
        return Chain(data).text('只能选择一个双休伴侣哦!')
    elif len(data.at_target) == 0:
        return Chain(data).text('请@你的道侣, 与其一起双修!')
    else:
        double_user = int(data.at_target[0])

    user_2 = Immortal.sql_manager().get_user_message(double_user)
    if user_1.user_id == double_user:
        return Chain(data).text('道友无法与自己双修!')
    if user_2:
        exp_1 = user_1.exp
        exp_2 = user_2.exp
        if exp_2 > exp_1:
            msg = '修仙大能看了看你，不屑一顾，扬长而去!'
            return Chain(data).text(msg)
        else:
            limit_1 = Immortal.double_exp_cd().find_user(user_1.user_id)
            limit_2 = Immortal.double_exp_cd().find_user(user_2.user_id)
            # 加入传承
            impart_data_1 = Immortal.impart_data().get_user_message(user_1.user_id)
            impart_data_2 = Immortal.impart_data().get_user_message(user_2.user_id)
            impart_double_exp_1 = impart_data_1.impart_double_exp if impart_data_1 else 0
            impart_double_exp_2 = impart_data_2.impart_double_exp if impart_data_2 else 0
            if limit_1 >= double_exp_limit + impart_double_exp_1:
                msg = '道友今天双修次数已经到达上限!'
                return Chain(data).text(msg)
            if limit_2 >= double_exp_limit + impart_double_exp_2:
                msg = '对方今天双修次数已经到达上限!'
                return Chain(data).text(msg)
            max_exp_1 = int(Immortal.other_set().set_closing_type(
                user_1.level)) * Immortal.get_config().closing_exp_upper_limit  # 获取下个境界需要的修为 * 1.5为闭关上限
            max_exp_2 = int(
                Immortal.other_set().set_closing_type(user_2.level)) * Immortal.get_config().closing_exp_upper_limit
            user_get_exp_max_1 = int(max_exp_1) - exp_1
            user_get_exp_max_2 = int(max_exp_2) - exp_2

            if user_get_exp_max_1 < 0:
                user_get_exp_max_1 = 0
            if user_get_exp_max_2 < 0:
                user_get_exp_max_2 = 0
            msg = ''
            msg += f'{user_1.user_name}与{user_2.user_name}情投意合，于某地一起修炼了一晚.'
            if random.randint(1, 100) in [13, 14, 52, 10, 66]:
                exp = int((exp_1 + exp_2) * 0.0055)

                if not user_1.sect_position:
                    max_exp_limit = 4
                else:
                    max_exp_limit = user_1.sect_position
                max_exp = Immortal.json_data().sect_config_data()[str(max_exp_limit)]['max_exp']
                if exp >= max_exp:
                    exp_limit_1 = max_exp
                else:
                    exp_limit_1 = exp

                if exp_limit_1 >= user_get_exp_max_1:
                    Immortal.sql_manager().update_exp(user_1.user_id, user_get_exp_max_1)
                    msg += f'\n{user_1.user_name}修为到达上限，增加修为{user_get_exp_max_1}.'
                else:
                    Immortal.sql_manager().update_exp(user_1.user_id, exp_limit_1)
                    msg += f'\n{user_1.user_name}增加修为{exp_limit_1}.'
                Immortal.sql_manager().update_power2(user_1.user_id)  # 更新战力

                if not user_2.sect_position:
                    max_exp_limit = 4
                else:
                    max_exp_limit = user_2.sect_position
                max_exp = Immortal.json_data().sect_config_data()[str(max_exp_limit)]['max_exp']
                if exp >= max_exp:
                    exp_limit_2 = max_exp
                else:
                    exp_limit_2 = exp

                if exp_limit_2 >= user_get_exp_max_2:
                    Immortal.sql_manager().update_exp(user_2.user_id, user_get_exp_max_2)
                    msg += f'\n{user_2.user_name}修为到达上限，增加修为{user_get_exp_max_2}.'
                else:
                    Immortal.sql_manager().update_exp(user_2.user_id, exp_limit_2)
                    msg += f'\n{user_2.user_name}增加修为{exp_limit_2}.'
                Immortal.sql_manager().update_power2(user_2.user_id)  # 更新战力
                Immortal.sql_manager().update_level_rate(user_1.user_id, user_1.level_up_rate + 2)
                Immortal.sql_manager().update_level_rate(user_2.user_id, user_2.level_up_rate + 2)
                Immortal.double_exp_cd().add_user(user_1.user_id)
                Immortal.double_exp_cd().add_user(user_2.user_id)
                msg += '\n离开时双方互相留法宝为对方护道,双方各增加突破概率2%.'
                return Chain(data).text(msg)
            else:
                exp = int((exp_1 + exp_2) * 0.0055)

                if not user_1.sect_position:
                    max_exp_limit = 4
                else:
                    max_exp_limit = user_1.sect_position
                max_exp = Immortal.json_data().sect_config_data()[str(max_exp_limit)]['max_exp']
                if exp >= max_exp:
                    exp_limit_1 = max_exp
                else:
                    exp_limit_1 = exp
                if exp_limit_1 >= user_get_exp_max_1:
                    Immortal.sql_manager().update_exp(user_1.user_id, user_get_exp_max_1)
                    msg += f'\n{user_1.user_name}修为到达上限，增加修为{user_get_exp_max_1}.'
                else:
                    Immortal.sql_manager().update_exp(user_1.user_id, exp_limit_1)
                    msg += f'\n{user_1.user_name}增加修为{exp_limit_1}.'
                Immortal.sql_manager().update_power2(user_1.user_id)  # 更新战力

                if not user_2.sect_position:
                    max_exp_limit = 4
                else:
                    max_exp_limit = user_2.sect_position
                max_exp = Immortal.json_data().sect_config_data()[str(max_exp_limit)]['max_exp']
                if exp >= max_exp:
                    exp_limit_2 = max_exp
                else:
                    exp_limit_2 = exp
                if exp_limit_2 >= user_get_exp_max_2:
                    Immortal.sql_manager().update_exp(user_2.user_id, user_get_exp_max_2)
                    msg += f'\n{user_2.user_name}修为到达上限，增加修为{user_get_exp_max_2}.'
                else:
                    Immortal.sql_manager().update_exp(user_2.user_id, exp_limit_2)
                    msg += f'\n{user_2.user_name}增加修为{exp_limit_2}.'
                Immortal.sql_manager().update_power2(user_2.user_id)  # 更新战力
                Immortal.double_exp_cd().add_user(user_1.user_id)
                Immortal.double_exp_cd().add_user(user_2.user_id)
                return Chain(data).text(msg)
    else:
        msg = '修仙者应一心向道, 务要留恋凡人!'
        return Chain(data).text(msg)


# 7.突破: 修为足够后, 可突破境界(一定几率失败)
@bot.on_message(keywords=Equal('突破'), check_prefix=False, level=6)
async def immortal_level_up(data: Message):
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    is_user, user_info, msg = Immortal.utils().check_user(data)  # 检查用户是否存在
    if not is_user:
        return Chain(data).text(msg)
    user_id = user_info.user_id
    if not user_info.hp:
        # 判断用户气血是否为空
        Immortal.sql_manager().update_user_hp(user_id)
    user_msg = Immortal.sql_manager().get_user_message(user_id)  # 获取用户信息
    user_level_up_rate = user_msg.level_up_rate  # 用户失败次数加成
    level_cd = user_msg.level_up_cd
    if level_cd:
        # 校验是否存在CD
        now_time = datetime.now()
        cd = Immortal.other_set().date_diff(now_time, level_cd)  # 获取second
        if cd < Immortal.get_config().level_up_cd * 60:
            # CD未到
            return Chain(data).text(f'目前无法突破，还需要{Immortal.get_config().level_up_cd - cd // 60}分钟')

    level_name = user_msg.level  # 用户境界
    level_rate = Immortal.json_data().level_rate_data()[level_name]  # 对应境界突破的概率
    user_backs = Immortal.sql_manager().get_back_msg(user_id)  # 获取用户背包
    items = Immortal.items()
    pause_flag = False
    elixir_name = None
    elixir_desc = None
    if user_backs:
        for back in user_backs:
            if back.goods_id == 1999 and back.goods_num > 0:  # 检测到有对应丹药
                pause_flag = True
                elixir_name = back.goods_name
                elixir_desc = items.get_data_by_item_id(back.goods_id)['desc']
                break
    if pause_flag:
        msg = f'由于检测到背包有丹药: {elixir_name}, 效果: {elixir_desc}, 突破已经准备就绪, 请发送 [渡厄突破] 或 [直接突破] 来选择是否使用丹药突破! 本次突破概率为: {level_rate + user_level_up_rate}%'
        return Chain(data).text(msg)
    else:
        msg = f'由于检测到背包没有 [渡厄丹] , 突破已经准备就绪, 请发送, [直接突破] 来突破! 请注意, 本次突破失败将会损失部分修为, 本次突破概率为: {level_rate + user_level_up_rate}%'
        return Chain(data).text(msg)


# 7.1 直接突破: 不使用渡厄丹突破, 会损失部分修为
@bot.on_message(keywords=Equal('直接突破'), check_prefix=False, level=7)
async def immortal_level_up_1(data: Message):
    """直接突破"""
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    is_user, user_info, msg = Immortal.utils().check_user(data)
    if not is_user:
        return Chain(data).text(msg)
    user_id = user_info.user_id
    if not user_info.hp:
        # 判断用户气血是否为空
        Immortal.sql_manager().update_user_hp(user_id)
    user_msg = Immortal.sql_manager().get_user_message(user_id)  # 获取用户信息
    level_cd = user_msg.level_up_cd
    if level_cd:
        # 校验是否存在CD
        now_time = datetime.now()
        cd = Immortal.other_set().date_diff(now_time, level_cd)  # 获取second
        if cd < Immortal.get_config().level_up_cd * 60:
            # 如果cd小于配置的cd，返回等待时间
            return Chain(data).text(f'目前无法突破，还需要{Immortal.get_config().level_up_cd - cd // 60}分钟')
    level_name = user_msg.level  # 用户境界
    exp = user_msg.exp  # 用户修为
    level_rate = Immortal.json_data().level_rate_data()[level_name]  # 对应境界突破的概率
    user_level_up_rate = user_msg.level_up_rate  # 用户失败次数加成
    le = Immortal.other_set().get_type(exp, level_rate + user_level_up_rate, level_name)  # 获取突破结果
    if le == '失败':
        # 突破失败
        Immortal.sql_manager().update_level_cd(user_id)  # 更新突破CD
        # 失败惩罚, 随机扣减修为
        percentage = random.randint(Immortal.get_config().level_punishment_floor,
                                    Immortal.get_config().level_punishment_limit)
        now_exp = int(exp * (percentage / 100))
        Immortal.sql_manager().update_minus_exp(user_id, now_exp)
        now_hp = int(max(user_msg.hp - (now_exp / 2), 1))
        now_mp = max(user_msg.mp - now_exp, 1)
        Immortal.sql_manager().update_user_hp_mp(user_id, now_hp, now_mp)  # 修为掉了，血量、真元也要掉
        update_rate = max(int(level_rate * Immortal.get_config().level_up_probability), 1)  # 失败增加突破几率
        Immortal.sql_manager().update_level_rate(user_id, user_level_up_rate + update_rate)
        msg = f'道友突破失败, 境界受损, 修为减少{now_exp}, 下次突破成功率增加{update_rate}%, 道友不要放弃!'
        return Chain(data).text(msg)
    elif type(le) == list:
        # 突破成功
        Immortal.sql_manager().update_level(user_id, le[0])  # 更新境界
        Immortal.sql_manager().update_power2(user_id)  # 更新战力
        Immortal.sql_manager().update_level_cd(user_id)  # 更新突破CD
        Immortal.sql_manager().update_level_rate(user_id, 0)  # 更新突破几率
        Immortal.sql_manager().update_user_hp(user_id)  # 重置用户hp，mp，atk状态
        msg = f'恭喜道友突破{le[0]}成功'
        return Chain(data).text(msg)
    else:
        # 最高境界
        msg = le
        return Chain(data).text(msg)


# 7.2 渡厄突破: 使用渡厄丹突破, 不会损失修为
@bot.on_message(keywords=Equal('渡厄突破'), check_prefix=False, level=7)
async def immortal_level_up_2(data: Message):
    """渡厄突破"""
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    is_user, user_info, msg = Immortal.utils().check_user(data)
    if not is_user:
        return Chain(data).text(msg)
    user_id = user_info.user_id
    if not user_info.hp:
        # 判断用户气血是否为空
        Immortal.sql_manager().update_user_hp(user_id)
    user_msg = Immortal.sql_manager().get_user_message(user_id)  # 获取用户信息
    level_cd = user_msg.level_up_cd
    if level_cd:
        # 校验是否存在CD
        now_time = datetime.now()
        cd = Immortal.other_set().date_diff(now_time, level_cd)  # 获取second
        if cd < Immortal.get_config().level_up_cd * 60:
            # 如果cd小于配置的cd，返回等待时间
            return Chain(data).text(f'目前无法突破，还需要{Immortal.get_config().level_up_cd - cd // 60}分钟')
    elixir_name = '渡厄丹'
    level_name = user_msg.level  # 用户境界
    exp = user_msg.exp  # 用户修为
    level_rate = Immortal.json_data().level_rate_data()[level_name]  # 对应境界突破的概率
    user_level_up_rate = user_msg.level_up_rate  # 用户失败次数加成
    le = Immortal.other_set().get_type(exp, level_rate + user_level_up_rate, level_name)  # 获取突破结果
    user_backs = Immortal.sql_manager().get_back_msg(user_id)  # 获取用户背包
    pause_flag = False
    if user_backs:
        for back in user_backs:
            if back.goods_id == 1999 and back.goods_num > 0:  # 检测到有对应丹药
                pause_flag = True
                elixir_name = back.goods_name
                break
    if le == '失败':
        # 突破失败
        Immortal.sql_manager().update_level_cd(user_id)  # 更新突破CD
        if pause_flag and Immortal.sql_manager().update_back_minus(user_id, 1999, use_key=1):  # 使用丹药
            update_rate = max(int(level_rate * Immortal.get_config().level_up_probability), 1)  # 失败增加突破几率
            Immortal.sql_manager().update_level_rate(user_id, user_level_up_rate + update_rate)
            msg = f'道友突破失败, 但是使用了丹药{elixir_name}, 本次突破失败不扣除修为下次突破成功率增加{update_rate}%, 道友不要放弃!'
        else:
            # 失败惩罚, 随机扣减修为
            percentage = random.randint(Immortal.get_config().level_punishment_floor,
                                        Immortal.get_config().level_punishment_limit)
            now_exp = int(exp * (percentage / 100))
            Immortal.sql_manager().update_minus_exp(user_id, now_exp)
            now_hp = int(max(user_msg.hp - (now_exp / 2), 1))
            now_mp = max(user_msg.mp - now_exp, 1)
            Immortal.sql_manager().update_user_hp_mp(user_id, now_hp, now_mp)  # 修为掉了，血量、真元也要掉
            update_rate = max(int(level_rate * Immortal.get_config().level_up_probability), 1)  # 失败增加突破几率
            Immortal.sql_manager().update_level_rate(user_id, user_level_up_rate + update_rate)
            msg = f'没有检测到{elixir_name}, 道友突破失败, 境界受损, 修为减少{now_exp}, 下次突破成功率增加{update_rate}%, 道友不要放弃!'
        return Chain(data).text(msg)
    elif type(le) == list:
        # 突破成功
        Immortal.sql_manager().update_level(user_id, le[0])  # 更新境界
        Immortal.sql_manager().update_power2(user_id)  # 更新战力
        Immortal.sql_manager().update_level_cd(user_id)  # 更新突破CD
        Immortal.sql_manager().update_level_rate(user_id, 0)  # 更新突破几率
        Immortal.sql_manager().update_user_hp(user_id)  # 重置用户hp，mp，atk状态
        msg = f'恭喜道友突破{le[0]}成功'
        return Chain(data).text(msg)
    else:
        # 最高境界
        msg = le
        return Chain(data).text(msg)


# 8.送灵石, 偷灵石, 抢灵石: 送灵石给道友, 偷道友灵石, 抢夺道友灵石
# 8.1 送灵石: 送灵石给道友, 收取10%手续费
@bot.on_message(keywords=re.compile(r'^送灵石\s*(\S+(\s+\S+)*)\s*$'), check_prefix=False, level=5)
async def immortal_send_stone(data: Message):
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    is_user, user_info, msg = Immortal.utils().check_user(data)  # 检查用户是否存在
    if not is_user:
        return Chain(data).text(msg)
    user_id = user_info.user_id
    user_stone_num = user_info.stone  # 用户灵石数
    give_user = None  # 艾特的时候存到这里
    match = re.match(r'^送灵石\s*(\S+(\s+\S+)*)\s*$', data.text_original)
    msg = match.group(1).strip()
    stone_num = re.findall(r'\d+', msg)  # 灵石数量
    nick_name = re.findall(r'\D+', msg)  # 道号
    if not stone_num:
        return Chain(data).text('请输入正确的灵石数量!')
    give_stone_num = int(stone_num[0])
    if give_stone_num > user_stone_num:
        return Chain(data).text('道友的灵石不够, 请重新输入!')
    if len(data.at_target) > 0:
        give_user = int(data.at_target[0])
    if give_user:
        if give_user == user_id:
            return Chain(data).text('请不要送灵石给自己!')
        else:
            give_user = Immortal.sql_manager().get_user_message(give_user)
            if give_user:
                Immortal.sql_manager().update_ls(user_id, give_stone_num, 2)  # 更新用户灵石
                give_stone_num_2 = int(give_stone_num * 0.1)
                num = give_stone_num - give_stone_num_2
                Immortal.sql_manager().update_ls(give_user.user_id, num, 1)  # 更新用户灵石
                msg = f'共赠送 {give_stone_num} 枚灵石给 {give_user.user_name} 道友! 收取手续费 {give_stone_num_2} 枚'
                return Chain(data).text(msg)
            else:
                return Chain(data).text('对方未踏入修仙界，不可赠送!')
    if nick_name:
        give_user = Immortal.sql_manager().get_user_message2(nick_name[0].strip())
        if give_user:
            if give_user.user_id == user_id:
                return Chain(data).text('请不要送灵石给自己!')
            else:
                Immortal.sql_manager().update_ls(user_id, give_stone_num, 2)  # 更新用户灵石
                give_stone_num_2 = int(give_stone_num * 0.1)
                num = give_stone_num - give_stone_num_2
                Immortal.sql_manager().update_ls(give_user.user_id, num, 1)  # 更新用户灵石
                msg = f'共赠送 {give_stone_num} 枚灵石给 {give_user.user_name} 道友! 收取手续费 {give_stone_num_2} 枚'
                return Chain(data).text(msg)
        else:
            return Chain(data).text('对方未踏入修仙界, 不可赠送!')
    else:
        return Chain(data).text('未获到对方信息, 请输入正确的道号!')


# 8.2 偷灵石: 偷道友灵石, 取决于两位道友的战力差距, 每次偷取需要 1000000 手续费, 失败将会被对方获得, 成功则不扣除
@bot.on_message(keywords=[Equal('偷灵石'), Equal('飞龙探云手')], check_prefix=False, level=4)
async def immortal_steal_stone(data: Message):
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    is_user, user_info, msg = Immortal.utils().check_user(data)  # 检查用户是否存在
    if not is_user:
        return Chain(data).text(msg)
    user_id = user_info.user_id
    steal_user = None
    steal_user_stone = None
    user_stone_num = user_info.stone  # 用户灵石数
    steal_target = None  # 艾特的时候存到这里, 被偷的人
    cost_stone_num = Immortal.get_config().tou
    if user_stone_num < cost_stone_num:
        return Chain(data).text('道友的偷窃准备(灵石)不足，请打工之后再切格瓦拉!')
    if len(data.at_target) > 0:
        steal_target = int(data.at_target[0])
    if steal_target:
        if steal_target == user_id:
            return Chain(data).text('请不要偷自己刷成就!')
        else:
            steal_user = Immortal.sql_manager().get_user_message(steal_target)
    if steal_user:
        steal_user_stone = steal_user.stone
        steal_success = random.randint(0, 100)
        result = Immortal.other_set().get_power_rate(user_info.power, steal_user.power)
        if isinstance(result, int):
            if steal_success > result:
                Immortal.sql_manager().update_ls(user_id, cost_stone_num, 2)  # 减少手续费
                Immortal.sql_manager().update_ls(steal_target, cost_stone_num, 1)  # 增加被偷的人的灵石
                msg = f'道友偷窃失手了, 被对方发现并被派去华哥厕所义务劳工! 赔款 {cost_stone_num} 灵石'
                return Chain(data).text(msg)
            get_stone = random.randint(int(Immortal.get_config().tou_lower_limit * steal_user_stone),
                                       int(Immortal.get_config().tou_upper_limit * steal_user_stone))
            if get_stone > steal_user_stone:
                Immortal.sql_manager().update_ls(user_id, cost_stone_num, 1)  # 增加偷到的灵石
                Immortal.sql_manager().update_ls(steal_target, steal_user_stone, 2)  # 减少被偷的人的灵石
                msg = f'{steal_user.user_name} 道友已经被榨干了~\n偷到了 {steal_user_stone} 枚灵石'
                return Chain(data).text(msg)
            else:
                Immortal.sql_manager().update_ls(user_id, get_stone, 1)  # 增加偷到的灵石
                Immortal.sql_manager().update_ls(steal_target, get_stone, 2)  # 减少被偷的人的灵石
                msg = f'共偷取 {steal_user.user_name} 道友 {get_stone} 枚灵石'
                return Chain(data).text(msg)
        else:
            return Chain(data).text(result)
    else:
        return Chain(data).text('对方未踏入修仙界, 不要对杂修出手!')


# 8.3 抢灵石: 抢夺道友灵石, 抢夺成功, 抢夺失败
@bot.on_message(keywords=[Equal('抢灵石'), Equal('抢劫')], check_prefix=False, level=5)
async def immortal_rob_stone(data: Message):
    """抢灵石
        player1 = {
        "NAME": player,
        "HP": player,
        "ATK": ATK,
        "COMBO": COMBO
        }
    """
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    is_user, user_info, msg = Immortal.utils().check_user(data)  # 检查用户是否存在
    if not is_user:
        return Chain(data).text(msg)
    if user_info.root == '器师':
        return Chain(data).text('目前职业无法抢劫!')
    user_id = user_info.user_id
    give_user = None  # 艾特的时候存到这里
    if len(data.at_target) > 0:
        give_user = int(data.at_target[0])
    player_1 = {
        "user_id": None,
        "道号": None,
        "气血": None,
        "攻击": None,
        "真元": None,
        "会心": None,
        "爆伤": None,
        "防御": 0
    }
    player_2 = {
        "user_id": None,
        "道号": None,
        "气血": None,
        "攻击": None,
        "真元": None,
        "会心": None,
        "爆伤": None,
        "防御": 0
    }
    if give_user:
        if give_user == user_id:
            return Chain(data).text('请不要抢自己刷成就!')
        user_2 = Immortal.sql_manager().get_user_message(give_user)
        if user_2:
            if user_2.root == '器师':
                return Chain(data).text('对方职业无法被抢劫!')
            if not user_info.hp:
                # 判断用户气血是否为None
                Immortal.sql_manager().update_user_hp(user_id)
                user_info = Immortal.sql_manager().get_user_message(user_id)
            if not user_2.hp:
                # 判断用户气血是否为None
                Immortal.sql_manager().update_user_hp(user_2.user_id)
                user_2 = Immortal.sql_manager().get_user_message(user_2.user_id)

            if user_2.hp <= user_2.exp / 10:
                time_2 = Immortal.impart_data().leave_harm_time(give_user)
                msg = f'对方重伤藏匿了, 无法抢劫! 距离对方脱离生命危险还需要{time_2}分钟!'
                return Chain(data).text(msg)

            if user_info.hp <= user_info.exp / 10:
                time_1 = Immortal.impart_data().leave_harm_time(user_id)
                msg = f'重伤未愈, 动弹不得! 距离脱离生命危险还需要{time_1}分钟!'
                return Chain(data).text(msg)

            impart_data_1 = Immortal.impart_data().get_user_message(user_id)  # 获取用户功法信息
            player_1['user_id'] = user_info.user_id
            player_1['道号'] = user_info.user_name
            player_1['气血'] = user_info.hp
            player_1['攻击'] = user_info.atk
            player_1['真元'] = user_info.mp
            player_1['会心'] = int((0.01 + impart_data_1.impart_know_per if impart_data_1 else 0) * 100)
            player_1['爆伤'] = int(1.5 + impart_data_1.impart_burst_per if impart_data_1 else 0)
            user_buff_data = Immortal.buff_data(user_id)
            user_armor_data = user_buff_data.get_user_armor_buff_data()
            if user_armor_data:
                def_buff = int(user_armor_data['def_buff'])
            else:
                def_buff = 0
            player_1['防御'] = def_buff

            impart_data_2 = Immortal.impart_data().get_user_message(give_user)  # 获取用户功法信息
            player_2['user_id'] = user_2.user_id
            player_2['道号'] = user_2.user_name
            player_2['气血'] = user_2.hp
            player_2['攻击'] = user_2.atk
            player_2['真元'] = user_2.mp
            player_2['会心'] = int((0.01 + impart_data_2.impart_know_per if impart_data_2 else 0) * 100)
            player_2['爆伤'] = int(1.5 + impart_data_2.impart_burst_per if impart_data_2 else 0)
            user_buff_data = Immortal.buff_data(give_user)
            user_armor_data = user_buff_data.get_user_armor_buff_data()
            if user_armor_data:
                def_buff = int(user_armor_data['def_buff'])
            else:
                def_buff = 0
            player_2['防御'] = def_buff

            result, victor = Immortal.other_set().player_fight(player_1, player_2)
            if type(data.instance) in [CQHttpBotInstance, MiraiBotInstance]:
                forward = MiraiForwardMessage(data) if type(
                    data.instance) == MiraiBotInstance else CQHTTPForwardMessage(data)
                for msg in result:
                    await forward.add_message(Chain(data, at=False).text(msg['msg']), msg['user_id'], msg['nickname'])
                await forward.send()
            else:
                msg = '\n'.join([msg['msg'] for msg in result])
                await data.send(Chain(data, at=False).text(msg))
            if victor == player_1['道号']:
                foe_stone = user_2.stone
                if foe_stone > 0:
                    Immortal.sql_manager().update_ls(user_id, int(foe_stone * 0.1), 1)  # 增加抢到到的灵石
                    Immortal.sql_manager().update_ls(give_user, int(foe_stone * 0.1), 2)  # 减少被抢的人的灵石
                    exps = int(user_2.exp * 0.005)
                    Immortal.sql_manager().update_exp(user_id, exps)  # 增加修为
                    Immortal.sql_manager().update_minus_exp(give_user, exps // 2)  # 减少修为
                    msg = f'大战一番, 战胜对手, 获取灵石{int(foe_stone * 0.1)}枚, 修为增加{exps}, 对手修为减少{exps // 2}'
                    return Chain(data).text(msg)
                else:
                    exps = int(user_2.exp * 0.005)
                    Immortal.sql_manager().update_exp(user_id, exps)
                    Immortal.sql_manager().update_minus_exp(give_user, exps // 2)
                    msg = f'大战一番, 战胜对手, 结果对方是个穷光蛋, 修为增加{exps}, 对手修为减少{exps // 2}'
                    return Chain(data).text(msg)
            elif victor == player_2['道号']:
                mind_stone = user_info.stone
                if mind_stone > 0:
                    Immortal.sql_manager().update_ls(user_id, int(mind_stone * 0.1), 2)  # 减少损失的灵石
                    Immortal.sql_manager().update_ls(give_user, int(mind_stone * 0.1), 1)  # 增加被抢的人的灵石
                    exps = int(user_info.exp * 0.005)
                    Immortal.sql_manager().update_minus_exp(give_user, exps)  # 减少修为
                    Immortal.sql_manager().update_exp(user_id, exps // 2)  # 增加修为
                    msg = f'大战一番, 被对手反杀, 损失灵石{int(mind_stone * 0.1)}枚, 修为减少{exps}, 对手修为增加{exps // 2}'
                    return Chain(data).text(msg)
                else:
                    exps = int(user_info.exp * 0.005)
                    Immortal.sql_manager().update_minus_exp(give_user, exps)
                    Immortal.sql_manager().update_exp(user_id, exps // 2)
                    msg = f'大战一番, 被对手反杀, 修为减少{exps}, 对手修为增加{exps // 2}'
                    return Chain(data).text(msg)
            else:
                return Chain(data).text('修仙界动荡, 你什么都没做!')
        else:
            return Chain(data).text('没有对方的信息!')


# 9.排行榜: 修仙排行榜, 灵石排行榜, 战力排行榜, 境界排行榜, 宗门排行榜
@bot.on_message(keywords=re.compile(r'^(修仙|灵石|战力|境界|宗门(建设度)?)?排行榜$'), check_prefix=False, level=7)
async def immortal_rank(data: Message):
    """排行榜"""
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    match = re.match(r'^(修仙|灵石|战力|境界|宗门(建设度)?)?排行榜$', data.text_original)
    rank_type = match.group(1)
    if not rank_type or rank_type in ['修仙', '境界']:
        p_rank = Immortal.sql_manager().realm_top()
        msg = '<div align="center">\n\n# ✨位面境界排行榜TOP10✨\n\n'
        num = 0
        for p in p_rank:
            num += 1
            msg += f'第**{num}**位 **{p.user_name}** **{p.level}**, 修为: **{Immortal.utils().number_to(p.exp)}**\n\n'
        msg += '</div>'
        return Chain(data).markdown(msg, is_dark=True)
    elif rank_type == '灵石':
        a_rank = Immortal.sql_manager().stone_top()
        msg = '<div align="center">\n\n# ✨位面灵石排行榜TOP10✨\n\n'
        num = 0
        for a in a_rank:
            num += 1
            msg += f'第**{num}**位 **{a.user_name}**, 灵石: **{Immortal.utils().number_to(a.stone)}**\n\n'
        msg += '</div>'
        return Chain(data).markdown(msg, is_dark=True)
    elif rank_type == '战力':
        c_rank = Immortal.sql_manager().power_top()
        msg = '<div align="center">\n\n# ✨位面战力排行榜TOP10✨\n\n'
        num = 0
        for c in c_rank:
            num += 1
            msg += f'第**{num}**位 **{c.user_name}**, 战力: **{Immortal.utils().number_to(c.power)}**\n\n'
        msg += '</div>'
        return Chain(data).markdown(msg, is_dark=True)
    elif rank_type in ['宗门', '宗门建设度']:
        c_rank = Immortal.sql_manager().scale_top()
        msg = '<div align="center">\n\n# ✨位面宗门建设度排行榜TOP10✨\n\n'
        num = 0
        for c in c_rank:
            num += 1
            msg += f'第**{num}**位 **{c.sect_name}**, 建设度: **{Immortal.utils().number_to(c.sect_scale)}**\n\n'
        msg += '</div>'
        return Chain(data).markdown(msg, is_dark=True)


# 10.悬赏令帮助: 获取悬赏令帮助信息
@bot.on_message(keywords=Equal('悬赏令帮助'), check_prefix=False, level=5)
async def immortal_work_help(data: Message):
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    msg = Immortal.work_help()
    return Chain(data).markdown(msg, is_dark=True)


# 11. 我的状态: 查看当前状态, 我的功法: 查看当前技能
# 11.1 我的状态: 查看当前状态
@bot.on_message(keywords=Equal('我的状态'), check_prefix=False, level=7)
async def immortal_my_status(data: Message):
    """我的状态信息"""
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    is_user, user_info, msg = Immortal.utils().check_user(data)
    if not is_user:
        return Chain(data).text(msg)
    user_id = user_info.user_id
    if not user_info.hp or user_info.hp == 0:
        Immortal.sql_manager().update_user_hp(user_id)
    user_msg = Immortal.sql_manager().get_user_real_info(user_id)

    level_rate = Immortal.sql_manager().get_root_rate(user_msg.root_type)  # 灵根倍率
    realm_rate = Immortal.json_data().level_data()[user_msg.level]['spend']  # 境界倍率
    user_buff_data = Immortal.buff_data(user_id)
    main_buff_data = user_buff_data.get_user_main_buff_data()
    user_weapon_data = user_buff_data.get_user_weapon_data()
    if user_weapon_data:
        crit_buff = int(user_weapon_data['crit_buff'] * 100)
    else:
        crit_buff = 1

    user_armor_data = user_buff_data.get_user_armor_buff_data()
    if user_armor_data:
        def_buff = int(user_armor_data['def_buff'] * 100)
    else:
        def_buff = 0

    main_buff_rate_buff = main_buff_data['ratebuff'] if main_buff_data else 0
    main_hp_buff = main_buff_data['hpbuff'] if main_buff_data else 0
    impart_data = Immortal.impart_data().get_user_message(user_id)  # 获取用户功法信息
    impart_hp_per = impart_data.impart_hp_per if impart_data else 0
    impart_know_per = impart_data.impart_know_per if impart_data else 0
    impart_burst_per = impart_data.impart_burst_per if impart_data else 0
    boss_atk = impart_data.boss_atk if impart_data else 0

    info = {
        '道号': user_msg.user_name,
        '气血': f'{Immortal.utils().number_to(user_msg.hp)}/{Immortal.utils().number_to(int((user_msg.exp / 2) * (1 + main_hp_buff + impart_hp_per)))}',
        '攻击': Immortal.utils().number_to(user_msg.atk),
        '攻击修炼': f'{user_msg.atk_practice}级 (提升攻击力 {user_msg.atk_practice * 4}%)',
        '修炼效率': f'{int(((level_rate * realm_rate) * (1 + main_buff_rate_buff)) * 100)}%',
        '会心': f'{crit_buff + int(impart_know_per * 100)}%',
        '减伤率': f'{def_buff}%',
        'boss战增益': f'{int(boss_atk * 100)}%',
        '会心伤害增益': f'{int((1.5 + impart_burst_per) * 100)}%'
    }
    msg = '<div align="center">\n\n# ✨状态信息✨\n\n</div>\n\n'
    for k, v in info.items():
        msg += f'**{k}**: {v}\n\n'
    return Chain(data).markdown(msg, is_dark=True)


# 11.2 我的功法: 查看当前技能
@bot.on_message(keywords=Equal('我的功法'), check_prefix=False, level=25)
async def immortal_my_impart(data: Message):
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    is_user, user_info, msg = Immortal.utils().check_user(data)
    if not is_user:
        return Chain(data).text(msg)
    user_id = user_info.user_id
    main_buff_data = Immortal.buff_data(user_id).get_user_main_buff_data()
    if main_buff_data:
        _, main_buff_msg = Immortal.buff_helper().get_main_info_msg(
            Immortal.buff_helper().get_user_buff(user_id).main_buff)
    else:
        main_buff_msg = ''
    sec_buff_data = Immortal.buff_data(user_id).get_user_sec_buff_data()
    sec_buff_msg = Immortal.buff_helper().get_sec_msg(sec_buff_data) if Immortal.buff_helper().get_sec_msg(
        sec_buff_data) != '无' else ''

    info = {
        '道友的主功法': f'{main_buff_data["name"] if main_buff_data else "无"}\n\n{main_buff_msg}',
        '道友的神通': f'{sec_buff_data["name"] if sec_buff_data else "无"}\n\n{sec_buff_msg}'
    }
    msg = '<div align="center">\n\n# ✨功法信息✨\n\n</div>\n\n'
    for k, v in info.items():
        msg += f'**{k}**: {v}\n\n'
    return Chain(data).markdown(msg, is_dark=True)


# 12.神秘力量
@bot.on_message(keywords=re.compile(r'^神秘力量\s*(\S+(\s+\S+)*)\s*$'), check_prefix=False, level=5)
async def immortal_mystery_power(data: Message):
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    if not is_superuser(int(data.user_id)):
        return
    give_user = None  # 艾特的时候存到这里
    match = re.match(r'^神秘力量\s*(\S+(\s+\S+)*)\s*$', data.text_original)
    msg = match.group(1).strip()
    stone_num = re.findall(r'\d+', msg)  # 灵石数量
    nick_name = re.findall(r'\D+', msg)  # 道号
    give_stone_num = int(stone_num[0])
    if give_stone_num < 1 or give_stone_num > 100000000:
        msg = '请输入正确的灵石数量!'
        return Chain(data).text(msg)
    for target in data.at_target:
        give_user = int(target)
    if give_user:
        give_user = Immortal.sql_manager().get_user_message(give_user)
        if give_user:
            Immortal.sql_manager().update_ls(give_user.user_id, give_stone_num, 1)  # 增加用户灵石
            msg = '共赠送{}枚灵石给{}道友!'.format(give_stone_num, give_user.user_name)
            return Chain(data).text(msg)
        else:
            msg = "对方未踏入修仙界，不可赠送！"
            return Chain(data).text(msg)
    elif nick_name:
        give_message = Immortal.sql_manager().get_user_message2(nick_name[0])
        if give_message:
            Immortal.sql_manager().update_ls(give_message.user_id, give_stone_num, 1)  # 增加用户灵石
            msg = '共赠送{}枚灵石给{}道友!'.format(give_stone_num, give_message.user_name)
            return Chain(data).text(msg)
        else:
            msg = '对方未踏入修仙界，不可赠送!'
            return Chain(data).text(msg)
    else:
        Immortal.sql_manager().update_ls_all(give_stone_num)
        msg = f'全服通告：赠送所有用户{give_stone_num}灵石,请注意查收!'
        return Chain(data, at=False).text(msg)


# 13.重置状态
@bot.on_message(keywords=Equal('重置状态'), check_prefix=False, level=12)
async def immortal_reset_status(data: Message):
    """重置用户状态。
    单用户：重置状态@xxx
    多用户：重置状态"""
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    if not is_superuser(int(data.user_id)):
        return
    is_user, _, msg = Immortal.utils().check_user(data)
    if not is_user:
        return Chain(data).text(msg)
    give_user = None  # 艾特的时候存到这里
    for target in data.at_target:
        give_user = int(target)
    if give_user:
        Immortal.sql_manager().restate(give_user)
        msg = '已重置{}道友状态!'.format(Immortal.sql_manager().get_user_message(give_user).user_name)
        return Chain(data).text(msg)
    else:
        Immortal.sql_manager().restate()
        msg = '已重置所有道友状态!'
        return Chain(data).text(msg)


# 13.重置突破
@bot.on_message(keywords=Equal('重置突破'), check_prefix=False, level=12)
async def immortal_reset_status(data: Message):
    """重置用户突破。
    单用户：重置状态@xxx
    多用户：重置状态"""
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    if not is_superuser(int(data.user_id)):
        return
    is_user, _, msg = Immortal.utils().check_user(data)
    if not is_user:
        return Chain(data).text(msg)
    give_user = None  # 艾特的时候存到这里
    for target in data.at_target:
        give_user = int(target)
    if give_user:
        Immortal.sql_manager().restate_break(give_user)
        msg = '已重置{}道友突破!'.format(Immortal.sql_manager().get_user_message(give_user).user_name)
        return Chain(data).text(msg)
    else:
        Immortal.sql_manager().restate_break()
        msg = '已重置所有道友突破!'
        return Chain(data).text(msg)


# 14.炼丹帮助: 炼丹功能
@bot.on_message(keywords=Equal('炼丹帮助'), check_prefix=False, level=5)
async def immortal_alchemy_help(data: Message):
    """炼丹帮助"""
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    msg = Immortal.alchemy_help()
    return Chain(data).markdown(msg, is_dark=True)


# 宗门系统
# 0.宗门帮助: 宗门帮助信息
@bot.on_message(keywords=Equal('宗门帮助'), check_prefix=False, level=5)
async def immortal_sect_help(data: Message):
    """宗门帮助信息"""
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    msg = Immortal.sect_help()
    return Chain(data).markdown(msg, is_dark=True)


# 1.我的宗门: 查看当前所处宗门信息
@bot.on_message(keywords=[Equal('我的宗门'), Equal('宗门信息')], check_prefix=False, level=5)
async def immortal_my_sect(data: Message):
    """查看所在宗门信息"""
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    is_user, user_info, msg = Immortal.utils().check_user(data)
    if not is_user:
        msg = '守山弟子: 凡人, 回去吧, 仙途难入, 莫要自误!'
        return Chain(data).text(msg)
    elixir_room_level_up_config = Immortal.sect_config()['宗门丹房参数']['elixir_room_level']
    sect_id = user_info.sect_id
    sect_position = user_info.sect_position
    user_name = user_info.user_name
    sect_info = Immortal.sql_manager().get_sect_info(sect_id)
    owner_idx = [k for k, v in Immortal.json_data().sect_config_data().items() if v.get('title', '') == '宗主']
    owner_position = int(owner_idx[0]) if len(owner_idx) == 1 else 0
    if sect_id:
        sql_res = Immortal.sql_manager().scale_top()
        top_idx_list = [_.sect_id for _ in sql_res]
        if int(sect_info.elixir_room_level) == 0:
            elixir_room_name = '暂无'
        else:
            elixir_room_name = elixir_room_level_up_config[str(sect_info.elixir_room_level)]['name']
        info = {
            '宗门名讳': sect_info.sect_name,
            '宗门编号': sect_id,
            '宗主': Immortal.sql_manager().get_user_message(sect_info.sect_owner).user_name,
            '道友职位': Immortal.json_data().sect_config_data()[str(sect_position)]['title'],
            '宗门建设度': Immortal.utils().number_to(sect_info.sect_scale),
            '洞天福地': sect_info.sect_fairyland if sect_info.sect_fairyland else '暂无',
            '宗门位面排名': top_idx_list.index(sect_id) + 1,
            '宗门拥有资材': Immortal.utils().number_to(sect_info.sect_materials),
            '宗门贡献度': Immortal.utils().number_to(user_info.sect_contribution),
            '宗门丹房': elixir_room_name
        }
        if sect_position == owner_position:
            info['宗门储备'] = f'{sect_info.sect_used_stone}灵石'
    else:
        info = "一介散修, 莫要再问."
    if isinstance(info, str):
        return Chain(data).text(info)
    msg = f'<div align="center">\n\n# ✨{user_name}所在宗门✨\n\n</div>\n\n'
    for k, v in info.items():
        msg += f'**{k}**: {v}\n\n'
    return Chain(data).markdown(msg, is_dark=True)


# 2.创建宗门: 创建宗门, 需求: 5000000 灵石,需求境界 铭纹境圆满
@bot.on_message(keywords=re.compile(r'^创建宗门([\s\S]+)$'), check_prefix=False, level=5)
async def immortal_create_sect(data: Message):
    """创建宗门，对灵石、修为等级有要求，且需要当前状态无宗门"""
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    is_user, user_info, msg = Immortal.utils().check_user(data)
    if not is_user:
        msg = '区区凡人, 也想创立万世仙门, 大胆!'
        return Chain(data).text(msg)
    user_id = user_info.user_id
    # 首先判断是否满足创建宗门的三大条件
    level = user_info.level
    list_level_all = list(Immortal.json_data().level_data().keys())
    if (list_level_all.index(level) < list_level_all.index(Immortal.get_config().sect_min_level) or
        user_info.stone < Immortal.get_config().sect_create_cost or
        user_info.sect_id
    ):
        msg = '<div align="center">\n\n# ✨创建宗门要求✨\n\n</div>\n\n'
        msg += f'1. 创建者境界最低要求为{Immortal.get_config().sect_min_level}\n\n'
        msg += f'2. 花费{Immortal.get_config().sect_create_cost}灵石费用\n\n'
        msg += f'3. 创建者当前处于无宗门状态\n\n'
        msg += f'道友暂未满足所有条件, 请逐一核实后, 再来寻我.'
        return Chain(data).markdown(msg, is_dark=True)
    else:
        # 切割command获取宗门名称
        match = re.match(r'^创建宗门([\s\S]+)$', data.text_original)
        sect_name = match.group(1).strip()
        if sect_name:
            # sect表新增
            Immortal.sql_manager().create_sect(user_id, sect_name)
            # 获取新增宗门的id（自增而非可设定）
            new_sect = Immortal.sql_manager().get_sect_info_by_qq(user_id)
            owner_idx = [k for k, v in Immortal.json_data().sect_config_data().items() if v.get('title', '') == '宗主']
            owner_position = int(owner_idx[0]) if len(owner_idx) == 1 else 0
            # 设置用户信息表的宗门字段
            Immortal.sql_manager().update_usr_sect(user_id, new_sect.sect_id, owner_position)
            # 扣灵石
            Immortal.sql_manager().update_ls(user_id, Immortal.get_config().sect_create_cost, 2)
            msg = f'恭喜{user_info.user_name}道友创建宗门——{sect_name}, 宗门编号为{new_sect.sect_id}. 为道友贺! 为仙道贺!'
        else:
            msg = '道友确定要创建无名之宗门? 还请三思.'
        return Chain(data).text(msg)


# 3.加入宗门: 加入宗门
@bot.on_message(keywords=re.compile(r'^加入宗门\s?(\d+)$'), check_prefix=False, level=5)
async def immortal_join_sect(data: Message):
    """加入宗门,后跟宗门ID,要求加入者当前状态无宗门,入门默认为外门弟子"""
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    is_user, user_info, msg = Immortal.utils().check_user(data)
    if not is_user:
        msg = '守山弟子: 凡人, 回去吧, 仙途难入, 莫要自误!'
        return Chain(data).text(msg)
    user_id = user_info.user_id
    if not user_info.sect_id:
        match = re.match(r'^加入宗门\s?(\d+)$', data.text_original)
        sect_no = match.group(1)
        sql_sects = Immortal.sql_manager().get_all_sect_id()
        sects_all = [tup.sect_id for tup in sql_sects]
        if not sect_no.isdigit():
            msg = f'申请加入的宗门编号解析异常, 应全为数字!'
        elif int(sect_no) not in sects_all:
            msg = f"申请加入的宗门编号似乎有误, 未在宗门名录上发现!"
        else:
            owner_idx = [k for k, v in Immortal.json_data().sect_config_data().items() if
                         v.get('title', '') == '外门弟子']
            owner_position = int(owner_idx[0]) if len(owner_idx) == 1 else 4
            Immortal.sql_manager().update_usr_sect(user_id, int(sect_no), owner_position)
            new_sect = Immortal.sql_manager().get_sect_info_by_id(int(sect_no))
            msg = f'欢迎{user_info.user_name}师弟入我{new_sect.sect_name}, 共参天道。'
    else:
        msg = f'守山弟子: 我观道友气运中已有宗门气运加持, 又何必与我为难.'
    return Chain(data).text(msg)


# 4.宗门职位变更: 宗主可以改变宗门成员的职位等级 `[0-4]` 分别对应 `[宗主 长老 亲传 内门 外门]` 外门弟子无法获得宗门修炼资源
@bot.on_message(keywords=re.compile(r'^宗门职位变更\s?(\d)$'), check_prefix=False, level=5)
async def immortal_sect_position_change(data: Message):
    """宗门职位变更，首先确认操作者的职位是长老及以上（宗主可以变更宗主及以下，长老可以变更长老以下），然后读取变更等级及艾特目标"""
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    is_user, user_info, msg = Immortal.utils().check_user(data)
    if not is_user:
        return Chain(data).text(msg)
    user_id = user_info.user_id

    position_zhang_lao = [k for k, v in Immortal.json_data().sect_config_data().items() if v.get('title', '') == '长老']
    idx_position = int(position_zhang_lao[0]) if len(position_zhang_lao) == 1 else 1
    if user_info.sect_position > idx_position:
        msg = f'你的宗门职位为{Immortal.json_data().sect_config_data()[str(user_info.sect_position)]["title"]}，无权进行职位管理'
        return Chain(data).text(msg)

    give_user = None  # 艾特的时候存到这里
    match = re.match(r'^宗门职位变更\s?(\d)$', data.text_original)
    position_num = match.group(1)

    for target in data.at_target:
        give_user = int(target)
    if give_user:
        if give_user == user_id:
            msg = '无法对自己的职位进行管理.'
            return Chain(data).text(msg)
        else:
            if position_num in list(Immortal.json_data().sect_config_data().keys()):
                give_user = Immortal.sql_manager().get_user_message(give_user)
                if give_user.sect_id == user_info.sect_id and give_user.sect_position > user_info.sect_position:
                    if int(position_num) > user_info.sect_position:
                        Immortal.sql_manager().update_usr_sect(give_user.user_id, give_user.sect_id,
                                                               int(position_num[0]))
                        msg = '<div align="center"><font color="gold">\n\n'
                        msg += f'# 传 {Immortal.json_data().sect_config_data()[str(user_info.sect_position)]["title"]} {user_info.user_name} 法旨\n\n'
                        msg += '</font></div>\n\n'
                        msg += '<font color="gold">\n\n'
                        msg += f'即日起 {give_user.user_name} 为本宗 {Immortal.json_data().sect_config_data()[str(int(position_num[0]))]["title"]}\n\n'
                        msg += '</font>'
                        return Chain(data).markdown(msg, is_dark=True)
                    else:
                        msg = '道友试图变更的职位品阶必须在你品阶之下'
                        return Chain(data).text(msg)
                else:
                    msg = '请确保变更目标道友与你在同一宗门, 且职位品阶在你之下.'
                    return Chain(data).text(msg)
            else:
                msg = '职位品阶数字解析异常, 请输入宗门职位变更帮助, 查看支持的数字解析配置'
                return Chain(data).text(msg)
    else:
        msg = '<div align="center">\n\n# ✨宗门职位变更帮助✨\n\n</div>\n\n'
        msg += f'## 请按照规范进行操作!\n\n例如: `宗门职位变更2@XXX`, 将XXX道友(需在自己管理下的宗门)的变更为{Immortal.json_data().sect_config_data().get("2", {"title": "没有找到2品阶"})["title"]}'
        return Chain(data).markdown(msg, is_dark=True)


# 5.宗门捐献: 建设宗门，提高宗门建设度，每 500000 建设度会提高1级攻击修炼等级上限
@bot.on_message(keywords=re.compile(r'^宗门捐献\s?(\d+)$'), check_prefix=False, level=5)
async def immortal_sect_donate(data: Message):
    """宗门捐献"""
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    is_user, user_info, msg = Immortal.utils().check_user(data)
    if not is_user:
        return Chain(data).text(msg)
    user_id = user_info.user_id
    if not user_info.sect_id:
        msg = '道友还未加入一方宗门.'
        return Chain(data).text(msg)
    match = re.match(r'^宗门捐献\s?(\d+)$', data.text_original)
    donate_num = int(match.group(1))  # 捐献灵石数
    if donate_num:
        if donate_num > user_info.stone:
            msg = f'道友的灵石数量小于欲捐献数量 {donate_num}, 请检查'
            return Chain(data).text(msg)
        else:
            Immortal.sql_manager().update_ls(user_id, donate_num, 2)
            Immortal.sql_manager().donate_update(user_info.sect_id, donate_num)
            Immortal.sql_manager().update_user_sect_contribution(user_id, user_info.sect_contribution + donate_num)
            msg = f'道友捐献灵石 {donate_num} 枚, 增加宗门建设度 {donate_num}, 宗门贡献度增加: {donate_num}点, 蒸蒸日上!'
            return Chain(data).text(msg)
    else:
        msg = '捐献的灵石数量解析异常'
        return Chain(data).text(msg)


# 6.退出宗门: 退出当前宗门
@bot.on_message(keywords=re.compile(r'^退出宗门\s?(\d+)$'), check_prefix=False, level=5)
async def immortal_sect_quit(data: Message):
    """退出宗门"""
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    is_user, user_info, msg = Immortal.utils().check_user(data)
    if not is_user:
        return Chain(data).text(msg)
    user_id = user_info.user_id
    if not user_info.sect_id:
        msg = '道友还未加入一方宗门.'
        return Chain(data).text(msg)
    position_this = [k for k, v in Immortal.json_data().sect_config_data().items() if v.get('title', '') == '宗主']
    owner_position = int(position_this[0]) if len(position_this) == 1 else 0
    if user_info.sect_position != owner_position:
        match = re.match(r'^退出宗门\s?(\d+)$', data.text_original)
        sect_out_id = int(match.group(1))  # 退出宗门的宗门编号
        if sect_out_id:
            if sect_out_id == user_info.sect_id:
                sql_sects = Immortal.sql_manager().get_all_sect_id()
                sects_all = [tup.sect_id for tup in sql_sects]
                if sect_out_id not in sects_all:
                    msg = f'欲退出的宗门编号 {sect_out_id} 似乎有误，未在宗门名录上发现!'
                    return Chain(data).text(msg)
                else:
                    Immortal.sql_manager().update_usr_sect(user_id)
                    sect_info = Immortal.sql_manager().get_sect_info_by_id(sect_out_id)
                    Immortal.sql_manager().update_user_sect_contribution(user_id, 0)
                    msg = f'道友已退出 {sect_info.sect_name}, 今后就是自由散修, 是福是祸, 犹未可知.'
                    return Chain(data).text(msg)
            else:
                msg = f'道友所在宗门编号为 {user_info.sect_id}, 与欲退出的宗门编号 {sect_out_id} 不符'
                return Chain(data).text(msg)
        else:
            msg = '欲退出的宗门编号解析异常'
            return Chain(data).text(msg)
    else:
        msg = '宗主无法直接退出宗门, 如确有需要, 请完成宗主传位后另行尝试.'
        return Chain(data).text(msg)


# 7.踢出宗门: 踢出对应宗门成员, 需要输入正确的账号或at对方
@bot.on_message(keywords=re.compile(r'^踢出宗门\s?(\d+)?$'), check_prefix=False, level=5)
async def immortal_sect_kick(data: Message):
    """踢出宗门"""
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    is_user, user_info, msg = Immortal.utils().check_user(data)
    if not is_user:
        return Chain(data).text(msg)
    user_id = user_info.user_id
    if not user_info.sect_id:
        msg = '道友还未加入一方宗门.'
        return Chain(data).text(msg)
    give_user = None  # 艾特的时候存到这里
    for target in data.at_target:
        give_user = int(target)
    if not give_user:
        match = re.match(r'^踢出宗门\s?(\d+)$', data.text_original)
        give_user = match.group(1)
        if give_user:
            give_user = Immortal.sql_manager().get_user_message(int(give_user))
            if not give_user:
                msg = '修仙界没有此人, 请输入正确账号或正规at!'
                return Chain(data).text(msg)
        else:
            msg = '请输入正确账号或正规at!'
            return Chain(data).text(msg)
    if isinstance(give_user, int):
        give_user = Immortal.sql_manager().get_user_message(give_user)
    if not give_user:
        msg = '修仙界没有此人, 请输入正确账号或正规at!'
        return Chain(data).text(msg)
    if give_user.user_id == user_id:
        msg = '无法对自己的进行踢出操作, 试试退出宗门?'
        return Chain(data).text(msg)
    if give_user.sect_id != user_info.sect_id:
        msg = f'{give_user.user_name}不在你管理的宗门内, 请检查.'
        return Chain(data).text(msg)
    position_zhang_lao = [k for k, v in Immortal.json_data().sect_config_data().items() if
                          v.get('title', '') == '长老']
    idx_position = int(position_zhang_lao[0]) if len(position_zhang_lao) == 1 else 1
    if user_info.sect_position > idx_position:
        msg = f'你的宗门职务为 {Immortal.json_data().sect_config_data()[str(user_info.sect_position)]["title"]}, 只有长老及以上可执行踢出操作.'
        return Chain(data).text(msg)
    if give_user.sect_position <= user_info.sect_position:
        msg = f'{give_user.user_name} 的宗门职务为 {Immortal.json_data().sect_config_data()[str(give_user.sect_position)]["title"]}, 不在你之下, 无权操作.'
        return Chain(data).text(msg)
    sect_info = Immortal.sql_manager().get_sect_info_by_id(user_info.sect_id)
    Immortal.sql_manager().update_usr_sect(give_user.user_id)
    Immortal.sql_manager().update_user_sect_contribution(give_user.user_id, 0)
    msg = '<div align="center"><font color="gold">\n\n'
    msg += f'# 传 {Immortal.json_data().sect_config_data()[str(user_info.sect_position)]["title"]} {user_info.user_name} 法旨\n\n'
    msg += '</font></div>\n\n'
    msg += '<font color="gold">\n\n'
    msg += f'即日起 {give_user.user_name} 被 {sect_info.sect_name} 除名\n\n'
    msg += '</font>'
    return Chain(data).markdown(msg, is_dark=True)


# 8.宗主传位: 宗主可以传位宗门成员
@bot.on_message(keywords=Equal('宗主传位'), check_prefix=False, level=5)
async def immortal_sect_owner_change(data: Message):
    """宗主传位"""
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    # 首先判断是否满足创建宗门的三大条件
    is_user, user_info, msg = Immortal.utils().check_user(data)
    if not is_user:
        return Chain(data).text(msg)
    user_id = user_info.user_id
    if not user_info.sect_id:
        msg = '道友还未加入一方宗门.'
        return Chain(data).text(msg)
    position_this = [k for k, v in Immortal.json_data().sect_config_data().items() if v.get('title', '') == '宗主']
    owner_position = int(position_this[0]) if len(position_this) == 1 else 0
    if user_info.sect_position != owner_position:
        msg = f'只有宗主才能进行传位.'
        return Chain(data).text(msg)
    give_user = None  # 艾特的时候存到这里
    for target in data.at_target:
        give_user = int(target)
    if not give_user:
        msg = '<div align="center">\n\n# ✨宗主传位帮助✨\n\n</div>\n\n'
        msg += f'## 请按照规范进行操作!\n\n例如: `宗主传位@XXX` ,将XXX道友(需在自己管理下的宗门)升为宗主，自己则变为宗主下一等职位'
        return Chain(data).markdown(msg, is_dark=True)
    if give_user == user_id:
        msg = '无法对自己的进行传位操作'
        return Chain(data).text(msg)
    else:
        give_user = Immortal.sql_manager().get_user_message(give_user)
        if not give_user:
            msg = '修仙界没有此人, 请重试!'
            return Chain(data).text(msg)
        if give_user.sect_id != user_info.sect_id:
            msg = f'{give_user.user_name}不在你管理的宗门内, 请检查.'
            return Chain(data).text(msg)
        Immortal.sql_manager().update_usr_sect(give_user.user_id, user_info.sect_id, owner_position)
        Immortal.sql_manager().update_usr_sect(user_info.user_id, user_info.sect_id, owner_position + 1)
        sect_info = Immortal.sql_manager().get_sect_info_by_id(user_info.sect_id)
        msg = '<div align="center"><font color="gold">\n\n'
        msg += f'# 传 老宗主 {user_info.user_name} 法旨\n\n'
        msg += '</font></div>\n\n'
        msg += '<font color="gold">\n\n'
        msg += f'即日起 {give_user.user_name} 继任 {sect_info.sect_name} 宗主\n\n'
        msg += '</font>'
        return Chain(data).markdown(msg, is_dark=True)


# 9.升级攻击修炼: 升级道友的攻击修炼等级,每级修炼等级提升4%攻击力
@bot.on_message(keywords=Equal('升级攻击修炼'), check_prefix=False, level=5)
async def immortal_sect_attack_level_up(data: Message):
    if await tool_is_close(data.instance.appid, 1, 2, 6, data.channel_id):
        return
    is_user, user_info, msg = Immortal.utils().check_user(data)
    if not is_user:
        return Chain(data).text(msg)
    user_id = user_info.user_id
    sect_id = user_info.sect_id
    if sect_id == 0:
        msg = '修炼逆天而行消耗巨大, 请加入宗门再进行修炼!'
        return Chain(data).text(msg)
    sect_materials = Immortal.sql_manager().get_sect_info(sect_id).sect_materials  # 宗门拥有资材
    user_atk_practice = user_info.atk_practice  # 用户攻击修炼等级
    if user_atk_practice == 25:
        msg = '道友的攻击修炼等级已达到最高等级!'
        return Chain(data).text(msg)
    sect_level = Immortal.utils().get_sect_level(sect_id)[0] if Immortal.utils().get_sect_level(sect_id)[0] <= 25 else 25
    sect_position = user_info.sect_position
    if sect_position == 4:
        msg = f'道友所在宗门的职位为: {Immortal.json_data().sect_config_data()[str(sect_position)]["title"]}, 不满足使用资材的条件!'
        return Chain(data).text(msg)
    if user_atk_practice >= sect_level:
        msg = f'道友的攻击修炼等级已达到当前宗门修炼等级的最高等级: {sect_level}, 请捐献灵石提升贡献度吧!'
        return Chain(data).text(msg)
    cost = Immortal.sect_config()['LEVLECOST'][str(user_atk_practice)]
    if user_info.stone < cost:
        msg = f'道友的灵石不够, 还需 {cost - user_info.stone} 灵石!'
        return Chain(data).text(msg)
    if sect_materials < cost * 10:
        msg = f'道友的所处的宗门资材不足, 还需 {cost * 10 - sect_materials} 资材!'
        return Chain(data).text(msg)
    Immortal.sql_manager().update_ls(user_id, cost, 2)
    Immortal.sql_manager().update_sect_materials(sect_id, cost * 10, 2)
    Immortal.sql_manager().update_user_atk_practice(user_id, user_atk_practice + 1)
    msg = f'升级成功, 道友当前攻击修炼等级：{user_atk_practice + 1}, 消耗灵石: {cost} 枚, 消耗宗门资材 {cost * 10} !'
    return Chain(data).text(msg)

