import random
from datetime import datetime
from typing import Tuple, Optional, Iterable, Union

from amiyabot.database import (
    AutoField,
    Case,
    DateTimeField,
    IntegerField,
    TextField,
    fn,
    table
)

from .config import immortal_config
from .data_source import json_data
from .database import ImmortalBaseModel


@table
class ImmortalUser(ImmortalBaseModel):
    """修仙用户表"""
    id: int = AutoField()  # id
    user_id: int = TextField()  # 用户id
    stone: int = IntegerField(default=0)  # 灵石
    root: str = TextField(null=True)  # 灵根
    root_type: str = TextField(null=True)  # 灵根类型
    level: str = TextField(null=True)  # 境界
    power: int = IntegerField(default=0)  # 战力
    create_time: datetime = DateTimeField(null=True)  # 创建时间
    is_sign: int = IntegerField(default=0)  # 是否签到
    exp: int = IntegerField(default=0)  # 经验
    user_name: str = TextField(null=True, default=None)  # 道号
    level_up_cd: datetime = DateTimeField(null=True, default=None)  # 境界升级cd
    level_up_rate: int = IntegerField(default=0)  # 境界升级概率
    sect_id: int = IntegerField(default=0)  # 门派id
    sect_position: int = IntegerField(default=0)  # 门派职位
    hp: int = IntegerField(default=0)  # 生命
    mp: int = IntegerField(default=0)  # 法力
    atk: int = IntegerField(default=0)  # 攻击
    atk_practice: int = IntegerField(default=0)  # 攻击修炼
    sect_task: int = IntegerField(default=0)  # 门派任务
    sect_contribution: int = IntegerField(default=0)  # 门派贡献
    sect_elixir_get: int = IntegerField(default=0)  # 门派丹药获取
    blessed_spot_flag: int = IntegerField(default=0)  # 福地标记
    blessed_spot_name: str = IntegerField(default=0)  # 福地名字


@table
class ImmortalImpart(ImmortalBaseModel):
    """功法表"""
    id: int = AutoField()  # id
    user_id: int = TextField(default=0)  # 用户id
    impart_hp_per: int = IntegerField(default=0)  # 生命加成
    impart_atk_per: int = IntegerField(default=0)  # 攻击加成
    impart_mp_per: int = IntegerField(default=0)  # 法力加成
    impart_exp_up: int = IntegerField(default=0)  # 经验加成
    boss_atk: int = IntegerField(default=0)  # boss攻击加成
    impart_know_per: int = IntegerField(default=0)  # 会心加成
    impart_burst_per: int = IntegerField(default=0)  # 爆伤加成
    impart_mix_per: int = IntegerField(default=0)  # 混元加成
    impart_reap_per: int = IntegerField(default=0)  # 收获加成
    impart_double_exp: int = IntegerField(default=0)  # 双修经验
    stone_num: int = IntegerField(default=0)  # 灵石数量
    exp_day: int = IntegerField(default=0)  # 经验加成天数
    wish: int = IntegerField(default=0)  # 许愿次数


@table
class ImmortalBuff(ImmortalBaseModel):
    """buff表"""
    id: int = AutoField()  # id
    user_id: int = TextField(default=0)  # 用户id
    main_buff: int = IntegerField(default=0)  # 主功法
    sec_buff: int = IntegerField(default=0)  # 神通
    faqi_buff: int = IntegerField(default=0)  # 法器buff
    fabao_buff: int = IntegerField(default=0)  # 法宝buff
    fabao_weapon: int = IntegerField(default=0)  # 法宝武器
    sub_buff: int = IntegerField(default=0)  # 辅助buff
    armor_buff: int = IntegerField(default=0)  # 防具buff
    atk_buff: int = IntegerField(default=0)  # 攻击buff
    blessed_spot: int = IntegerField(default=0)  # 福地buff


@table
class ImmortalSect(ImmortalBaseModel):
    """宗门表"""
    sect_id: int = AutoField()  # 宗门id
    sect_name: str = TextField()  # 宗门名字
    sect_owner: int = TextField(null=True)  # 宗门拥有者
    sect_scale: int = IntegerField()  # 宗门规模
    sect_used_stone: int = IntegerField(null=True)  # 宗门消耗灵石
    sect_fairyland: int = IntegerField(null=True)  # 宗门福地
    sect_materials: int = IntegerField(default=0)  # 宗门资材
    main_buff: int = IntegerField(default=0)  # 宗门主buff
    sec_buff: int = IntegerField(default=0)  # 宗门副buff
    elixir_room_level: int = IntegerField(default=0)  # 丹房等级


@table
class ImmortalUserCD(ImmortalBaseModel):
    """用户操作CD"""
    id: int = AutoField()  # id
    user_id: int = TextField()  # 用户id
    type: int = IntegerField(default=0)  # 状态
    create_time: datetime = DateTimeField(null=True)  # 创建时间
    scheduled_time: datetime = DateTimeField(null=True)  # 预定时间


@table
class ImmortalUserBack(ImmortalBaseModel):
    """用户背包信息"""
    id: int = AutoField()  # id
    user_id: int = TextField()  # 用户id
    goods_id: int = IntegerField()  # 物品id
    goods_name: str = TextField(null=True)  # 物品名字
    goods_type: str = TextField(null=True)  # 物品类型
    goods_num: int = IntegerField(null=True)  # 物品数量
    create_time: datetime = DateTimeField(default=datetime.now())  # 创建时间
    update_time: datetime = DateTimeField(default=datetime.now())  # 更新时间
    remake: str = TextField(null=True)  # 备注
    day_num: int = IntegerField(default=0)  # 日使用量
    all_num: int = IntegerField(default=0)  # 总使用量
    action_time: datetime = DateTimeField(null=True)  # 操作时间
    state: int = IntegerField(default=0)  # 状态
    bind_num: int = IntegerField(default=0)  # 绑定数量


class DataManager:
    @staticmethod
    def create_user(user_id: int, root: str, root_type: str, power: int, create_time: datetime, user_name: str) -> bool:
        """创建用户"""
        user = ImmortalUser.get_or_none(ImmortalUser.user_id == user_id)
        if user:
            return False
        else:
            ImmortalUser.create(
                user_id=user_id,
                root=root,
                root_type=root_type,
                level='江湖好手',
                power=power,
                create_time=create_time,
                user_name=user_name
            )
            return True

    @staticmethod
    def get_root_rate(name: str) -> float:
        """获取灵根倍率"""
        data = json_data.root_data()
        return data[name]['type_speeds']

    @staticmethod
    def get_user_message(user_id: int) -> ImmortalUser:
        """根据USER_ID获取用户信息,不获取功法加成"""
        return ImmortalUser.get_or_none(ImmortalUser.user_id == user_id)

    @staticmethod
    def get_user_real_info(user_id: int):
        """根据USER_ID获取用户信息,获取功法加成"""
        user_info = ImmortalUser.get_or_none(ImmortalUser.user_id == user_id)
        return final_user_data(user_info)

    @staticmethod
    def get_user_buff_info(user_id: int) -> ImmortalBuff:
        """获取用户buff信息"""
        return ImmortalBuff.get_or_none(ImmortalBuff.user_id == user_id)

    @staticmethod
    def initialize_user_buff_info(user_id: int):
        """初始化用户buff信息"""
        ImmortalBuff.create(user_id=user_id)

    @staticmethod
    def get_exp_rank(user_id: int) -> int:
        """修为排行榜"""
        rank = (
            ImmortalUser
            .select(
                ImmortalUser.user_id,
                ImmortalUser.exp,
                fn.dense_rank().over(order_by=[ImmortalUser.exp.desc()]).alias('rank')
            )
        )
        for i in rank:
            if i.user_id == user_id:
                return i.rank
        return 0

    @staticmethod
    def get_stone_rank(user_id: int) -> int:
        """灵石排行"""
        rank = (
            ImmortalUser
            .select(
                ImmortalUser.user_id,
                ImmortalUser.stone,
                fn.dense_rank().over(order_by=[ImmortalUser.stone.desc()]).alias('rank')
            )
        )
        for i in rank:
            if i.user_id == user_id:
                return i.rank
        return 0

    @staticmethod
    def get_sect_info(sect_id: int) -> ImmortalSect:
        """
        通过宗门编号获取宗门信息
        :param sect_id: 宗门编号
        :return:
        """
        return ImmortalSect.get_or_none(ImmortalSect.sect_id == sect_id)

    @staticmethod
    def get_level_power(name: str) -> int:
        """获取境界倍率|exp"""
        data = json_data.level_data()
        return data[name]['power']

    @staticmethod
    def sign_reset():
        """重置签到状态"""
        ImmortalUser.update(is_sign=0).execute()

    @staticmethod
    def get_sign(user_id) -> str:
        """获取用户签到信息"""
        sign = DataManager.get_user_message(user_id)
        if not sign:
            return '修仙界没有你的足迹，输入 [我要修仙] 加入修仙世界吧！'
        elif sign.is_sign == 1:
            return '贪心的人是不会有好运的！'
        else:
            ls = random.randint(immortal_config.sign_in_lingshi_lower_limit,
                                immortal_config.sign_in_lingshi_upper_limit)
            sign.is_sign = 1
            sign.stone += ls
            sign.save()
            return f'签到成功，获得{ls}块灵石！'

    @staticmethod
    def remake(lg: str, lg_type: str, user_id: int) -> Tuple[bool, Optional[int]]:
        """洗灵根"""
        # 查灵石
        user = DataManager.get_user_message(user_id)
        if user.stone > immortal_config.remake:
            user.root = lg
            user.root_type = lg_type
            user.stone -= immortal_config.remake
            user.save()
            power = DataManager.update_power2(user_id)
            return True, power
        else:
            return False, None

    @staticmethod
    def update_power2(user_id: int) -> int:
        """更新战力"""
        user_message = DataManager.get_user_message(user_id)
        level = json_data.level_data()
        root = json_data.root_data()
        if user_message.exp == 0:
            user_message.power = 100 * root[user_message.root_type]['type_speeds']
        else:
            user_message.power = int(
                user_message.exp * level[user_message.level]['spend'] * root[user_message.root_type]['type_speeds'])
        user_message.save()
        return user_message.power

    @staticmethod
    def rename(user_id: int, user_name: str) -> str:
        """更新用户道号"""
        user = ImmortalUser.get_or_none(ImmortalUser.user_name == user_name)
        if user:
            return '已存在该道号！'
        else:
            user = DataManager.get_user_message(user_id)
            user.user_name = user_name
            user.save()
            return '道友的道号更新成功拉~'

    @staticmethod
    def get_user_cd(user_id: int) -> Optional[ImmortalUserCD]:
        """
        获取用户操作CD
        :param user_id: qq
        """
        result = ImmortalUserCD.get_or_none(ImmortalUserCD.user_id == user_id)
        if result:
            return result
        else:
            DataManager.insert_user_cd(user_id)
            return None

    @staticmethod
    def insert_user_cd(user_id: int) -> None:
        """
        添加用户至CD表
        :param user_id: qq
        :return:
        """
        ImmortalUserCD.create(user_id=user_id)

    @staticmethod
    def in_closing(user_id: int, the_type: int) -> None:
        """
        更新用户操作CD
        :param user_id: qq
        :param the_type: 0:无状态  1:闭关中  2:历练中
        :return:
        """
        now = None
        if the_type == 1:
            now = datetime.now()
        elif the_type == 0:
            now = datetime.fromtimestamp(0)
        elif the_type == 2:
            now = datetime.now()
        ImmortalUserCD.update(type=the_type, create_time=now).where(ImmortalUserCD.user_id == user_id).execute()

    @staticmethod
    def update_exp(user_id: int, user_get_exp_max: int) -> None:
        """增加修为"""
        user = DataManager.get_user_message(user_id)
        user.exp += user_get_exp_max
        user.save()

    @staticmethod
    def update_user_attribute(user_id: int, hp: int, mp: int, atk: int) -> None:
        """更新用户HP,MP,ATK信息"""
        user = DataManager.get_user_message(user_id)
        user.hp = hp
        user.mp = mp
        user.atk = atk
        user.save()

    @staticmethod
    def update_ls(user_id: int, price: int, key: int) -> None:
        """更新灵石  1为增加，2为减少"""
        user = DataManager.get_user_message(user_id)
        if key == 1:
            user.stone += price
        elif key == 2:
            user.stone -= price
        user.save()

    @staticmethod
    def update_level_rate(user_id: int, rate: int) -> None:
        """更新突破成功率"""
        user = DataManager.get_user_message(user_id)
        user.level_up_rate = rate
        user.save()

    @staticmethod
    def update_user_hp(user_id: int) -> None:
        """重置用户状态信息"""
        user = DataManager.get_user_message(user_id)
        user.hp = int(user.exp / 2)
        user.mp = user.exp
        user.atk = int(user.exp / 10)
        user.save()

    @staticmethod
    def get_back_msg(user_id: int) -> Iterable[ImmortalUserBack]:
        """获取用户背包信息"""
        return ImmortalUserBack.select().where(ImmortalUserBack.user_id == user_id)

    @staticmethod
    def update_level_cd(user_id: int) -> None:
        """更新破镜CD"""
        user = DataManager.get_user_message(user_id)
        user.level_up_cd = datetime.now()
        user.save()

    @staticmethod
    def update_minus_exp(user_id: int, exp: int) -> None:
        """减少修为"""
        user = DataManager.get_user_message(user_id)
        user.exp -= exp
        user.save()

    @staticmethod
    def update_user_hp_mp(user_id: int, hp: int, mp: int) -> None:
        """更新用户HP,MP信息"""
        user = DataManager.get_user_message(user_id)
        user.hp = hp
        user.mp = mp
        user.save()

    @staticmethod
    def update_level(user_id: int, level_name: str) -> None:
        """更新境界"""
        user = DataManager.get_user_message(user_id)
        user.level = level_name
        user.save()

    @staticmethod
    def update_back_minus(user_id: int, goods_id: int, num: int = 1, use_key: int = 0) -> bool:
        """
        使用物品
        :num 减少数量  默认1
        :use_key 是否使用，丹药使用才传 默认0
        """
        back = DataManager.get_item_by_good_id_and_user_id(user_id, goods_id)
        if back.goods_type == '丹药' and use_key == 1:  # 丹药要判断耐药性、日使用上限
            if back.bind_num >= 1:
                bind_num = back.bind_num - num  # 优先使用绑定物品
            else:
                bind_num = back.bind_num
            day_num = back.day_num + num
            all_num = back.all_num + num
        else:
            bind_num = back.bind_num
            day_num = back.day_num
            all_num = back.all_num
        goods_num = back.goods_num - num
        now_time = datetime.now()
        if goods_num < 0:
            return False
        else:
            back.update_time = now_time
            back.action_time = now_time
            back.goods_num = goods_num
            back.day_num = day_num
            back.all_num = all_num
            back.bind_num = bind_num
            back.save()
            return True

    @staticmethod
    def get_item_by_good_id_and_user_id(user_id, goods_id) -> ImmortalUserBack:
        """根据物品id、用户id获取物品信息"""
        return ImmortalUserBack.get_or_none(ImmortalUserBack.user_id == user_id, ImmortalUserBack.goods_id == goods_id)

    @staticmethod
    def get_user_message2(user_name: str) -> ImmortalUser:
        """根据user_name获取用户信息"""
        return ImmortalUser.get_or_none(ImmortalUser.user_name == user_name)

    @staticmethod
    def realm_top() -> Iterable[ImmortalUser]:
        """境界排行榜"""
        level_as_num = tuple()
        levels = json_data.level_data()
        for key, value in levels.items():
            level_as_num += ((key, value['value']),)
        level_as_num = Case(ImmortalUser.level, level_as_num, ImmortalUser.level)
        rank = (
            ImmortalUser
            .select(ImmortalUser.user_name, ImmortalUser.level, ImmortalUser.exp)
            .where(ImmortalUser.user_name.is_null(False))
            .order_by(level_as_num.asc(), ImmortalUser.exp.desc())
            .limit(10)
        )
        return rank

    @staticmethod
    def stone_top() -> Iterable[ImmortalUser]:
        rank = (
            ImmortalUser
            .select(ImmortalUser.user_name, ImmortalUser.stone)
            .where(ImmortalUser.user_name.is_null(False))
            .order_by(ImmortalUser.stone.desc())
            .limit(10)
        )
        return rank

    @staticmethod
    def power_top() -> Iterable[ImmortalUser]:
        """战力排行榜"""
        rank = (
            ImmortalUser
            .select(ImmortalUser.user_name, ImmortalUser.power)
            .where(ImmortalUser.user_name.is_null(False))
            .order_by(ImmortalUser.power.desc())
            .limit(10)
        )
        return rank

    @staticmethod
    def scale_top() -> Iterable[ImmortalSect]:
        """
        宗门建设度排行榜
        :return:
        """
        rank = (
            ImmortalSect
            .select(ImmortalSect.sect_id, ImmortalSect.sect_name, ImmortalSect.sect_scale)
            .where(ImmortalSect.sect_owner.is_null(False))
            .order_by(ImmortalSect.sect_scale.desc())
        )
        return rank

    @staticmethod
    def update_ls_all(give_stone_num: int) -> None:
        """所有用户增加灵石"""
        ImmortalUser.update(stone=ImmortalUser.stone + give_stone_num).execute()

    @staticmethod
    def restate(user_id: Optional[int] = None) -> None:
        """重置用户状态"""
        if user_id:
            user = DataManager.get_user_message(user_id)
            user.hp = int(user.exp / 2)
            user.mp = user.exp
            user.atk = int(user.exp / 10)
            user.save()
        else:
            ImmortalUser.update(hp=ImmortalUser.exp / 2, mp=ImmortalUser.exp, atk=ImmortalUser.exp / 10).execute()

    @staticmethod
    def restate_break(user_id: Optional[int] = None) -> None:
        """重置用户状态"""
        if user_id:
            user = DataManager.get_user_message(user_id)
            user.level_up_cd = datetime.fromtimestamp(0)
            user.save()
        else:
            ImmortalUser.update(level_up_cd=datetime.fromtimestamp(0)).execute()

    @staticmethod
    def get_all_sects_id_scale() -> Iterable[ImmortalSect]:
        """
        获取所有宗门信息
        :return
        :result[0] = sect_id
        :result[1] = 建设度 sect_scale,
        :result[2] = 丹房等级 elixir_room_level
        """
        result = (
            ImmortalSect
            .select(ImmortalSect.sect_id, ImmortalSect.sect_scale, ImmortalSect.elixir_room_level)
            .where(ImmortalSect.sect_owner.is_null(False))
            .order_by(ImmortalSect.sect_scale.desc())
        )
        return result

    @staticmethod
    def update_sect_materials(sect_id: int, sect_materials: int, key: int) -> None:
        """更新资材  1为增加,2为减少"""
        sect = DataManager.get_sect_info(sect_id)
        if key == 1:
            sect.sect_materials += sect_materials
        elif key == 2:
            sect.sect_materials -= sect_materials
        sect.save()

    @staticmethod
    def sect_task_reset() -> None:
        """重置宗门任务次数"""
        ImmortalUser.update(sect_task=0).execute()

    @staticmethod
    def sect_elixir_get_num_reset() -> None:
        """重置宗门丹药领取次数"""
        ImmortalUser.update(sect_elixir_get=0).execute()

    @staticmethod
    def create_sect(user_id: int, sect_name: str) -> None:
        """
       创建宗门
       :param user_id:qq
       :param sect_name:宗门名称
       :return:
       """
        ImmortalSect.create(
            sect_name=sect_name,
            sect_owner=user_id,
            sect_scale=0,
            sect_used_stone=0
        )

    @staticmethod
    def get_sect_info_by_qq(user_id: int) -> ImmortalSect:
        """
        通过用户qq获取宗门信息
        :param user_id:
        :return:
        """
        return ImmortalSect.get_or_none(ImmortalSect.sect_owner == user_id)

    @staticmethod
    def update_usr_sect(
        user_id: int, user_sect_id: int = 0, user_sect_position: int = 0
    ) -> None:
        """
        更新用户信息表的宗门信息字段
        :param user_id:
        :param user_sect_id:
        :param user_sect_position:
        :return:
        """
        user = DataManager.get_user_message(user_id)
        user.sect_id = user_sect_id
        user.sect_position = user_sect_position
        user.save()

    @staticmethod
    def get_all_sect_id() -> Iterable[ImmortalSect]:
        """
        获取所有宗门id
        :return:
        """
        return ImmortalSect.select(ImmortalSect.sect_id)

    @staticmethod
    def get_sect_info_by_id(sect_id: int) -> ImmortalSect:
        """
        通过宗门id获取宗门信息
        :param sect_id:
        :return:
        """
        return ImmortalSect.get_or_none(ImmortalSect.sect_id == sect_id)

    @staticmethod
    def donate_update(sect_id: int, stone_num: int) -> None:
        """宗门捐献更新建设度及可用灵石"""
        sect = DataManager.get_sect_info(sect_id)
        sect.sect_scale += stone_num
        sect.sect_used_stone += stone_num
        sect.save()

    @staticmethod
    def update_user_sect_contribution(user_id: int, sect_contribution: int) -> None:
        """更新用户宗门贡献度"""
        user = DataManager.get_user_message(user_id)
        user.sect_contribution = sect_contribution
        user.save()

    @staticmethod
    def update_user_atk_practice(user_id: int, atk_practice: int) -> None:
        """更新用户攻击修炼等级"""
        user = DataManager.get_user_message(user_id)
        user.atk_practice = atk_practice
        user.save()


class ImpartManager:
    @staticmethod
    def create_user(user_id: int) -> None:
        """在数据库中创建用户并初始化"""
        if not ImmortalImpart.get_or_none(ImmortalImpart.user_id == user_id):
            ImmortalImpart.create(user_id=user_id)

    @staticmethod
    def get_user_message(user_id: int) -> ImmortalImpart:
        """根据USER_ID获取用户impart_buff信息"""
        return ImmortalImpart.get_or_none(ImmortalImpart.user_id == user_id)

    @staticmethod
    def leave_harm_time(user_id: int) -> Union[int, str]:
        from .buff import UserBuffData
        hp_speed = 25
        user_msg = DataManager.get_user_message(user_id)  # 用户信息
        level = user_msg.level  # 境界
        level_rate = DataManager.get_root_rate(user_msg.root_type)  # 灵根倍率
        realm_rate = json_data.level_data()[level]['spend']  # 境界倍率
        main_buff_data = UserBuffData(user_id).get_user_main_buff_data()  # 主buff信息
        main_buff_rate_buff = main_buff_data['ratebuff'] if main_buff_data else 0  # 功法修炼倍率
        try:
            time = int((user_msg.exp / 10 - user_msg.hp) / (
                    immortal_config.closing_exp * level_rate * realm_rate * (1 + main_buff_rate_buff) * hp_speed))
        except ZeroDivisionError:
            time = '∞'
        return time


def final_user_data(user_data: ImmortalUser) -> ImmortalUser:
    from .buff import UserBuffData
    from .item import items
    """传入用户当前信息、buff信息,返回最终信息"""

    ImpartManager.create_user(user_data.user_id)  # 若用户不存在，则创建功法信息
    impart_data = ImpartManager.get_user_message(user_data.user_id)
    impart_hp_per = impart_data.impart_hp_per if impart_data else 0
    impart_mp_per = impart_data.impart_mp_per if impart_data else 0
    impart_atk_per = impart_data.impart_atk_per if impart_data else 0

    user_buff_data = UserBuffData(user_data.user_id)
    user_buff_info = UserBuffData(user_data.user_id).buff_info
    if user_buff_info.faqi_buff == 0:
        weapon_atk_buff = 0
    else:
        weapon_info = items.get_data_by_item_id(user_buff_info.faqi_buff)
        weapon_atk_buff = weapon_info['atk_buff']
    main_buff_data = user_buff_data.get_user_main_buff_data()
    main_hp_buff = main_buff_data['hpbuff'] if main_buff_data else 0
    main_mp_buff = main_buff_data['mpbuff'] if main_buff_data else 0
    main_atk_buff = main_buff_data['atkbuff'] if main_buff_data else 0

    user_data.hp = int(user_data.hp * (1 + main_hp_buff + impart_hp_per))
    user_data.mp = int(user_data.mp * (1 + main_mp_buff + impart_mp_per))
    user_data.atk = int(
        (user_data.atk * (user_data.atk_practice * 0.04 + 1) * (1 + main_atk_buff) * (1 + weapon_atk_buff)) * (
            1 + impart_atk_per)) + int(user_buff_info.atk_buff)
    return user_data


sql_manager = DataManager()
impart_manager = ImpartManager()
