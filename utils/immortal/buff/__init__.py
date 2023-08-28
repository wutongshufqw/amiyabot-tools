from typing import Optional, Union, Tuple

try:
    import ujson as json
except ImportError:
    import json

from ..config import data_path
from ..item import items
from ..sql import DataManager, ImmortalBuff

from .double_exp_cd import DoubleExpCd, double_exp_cd

skill_path = data_path / '功法'
weapon_path = data_path / '装备'


class UserBuffData:
    def __init__(self, user_id: int):
        """用户Buff数据"""
        self.user_id: int = user_id
        self.buff_info: ImmortalBuff = BuffHelper.get_user_buff(self.user_id)

    def get_user_main_buff_data(self) -> Optional[dict]:
        """获取用户主功法数据"""
        return items.get_data_by_item_id(self.buff_info.main_buff)

    def get_user_sec_buff_data(self) -> Optional[dict]:
        """获取用户神通数据"""
        return items.get_data_by_item_id(self.buff_info.sec_buff)

    def get_user_weapon_data(self) -> Optional[dict]:
        """获取用户法器buff数据"""
        return items.get_data_by_item_id(self.buff_info.faqi_buff)

    def get_user_armor_buff_data(self) -> Optional[dict]:
        """获取用户防具buff数据"""
        return items.get_data_by_item_id(self.buff_info.armor_buff)


class BuffHelper:
    @staticmethod
    def get_user_buff(user_id: int) -> ImmortalBuff:
        """获取用户buff信息"""
        buff_info = DataManager.get_user_buff_info(user_id)
        if not buff_info:
            DataManager.initialize_user_buff_info(user_id)
            buff_info = DataManager.get_user_buff_info(user_id)
        return buff_info

    @staticmethod
    def get_main_info_msg(id_: Union[str, int]) -> Tuple[dict, str]:
        main_buff = items.get_data_by_item_id(id_)
        hp_msg = f'提升{round(main_buff["hpbuff"] * 100, 0)}%气血' if main_buff['hpbuff'] != 0 else ''
        mp_msg = f'提升{round(main_buff["mpbuff"] * 100, 0)}%真元' if main_buff['mpbuff'] != 0 else ''
        atk_msg = f'提升{round(main_buff["atkbuff"] * 100, 0)}%攻击力' if main_buff['atkbuff'] != 0 else ''
        rate_msg = f'提升{round(main_buff["ratebuff"] * 100, 0)}%修炼速度' if main_buff['ratebuff'] != 0 else ''
        msg = f'{main_buff["name"]}:{hp_msg},{mp_msg},{atk_msg},{rate_msg}.'
        return main_buff, msg

    @staticmethod
    def get_sec_msg(sec_buff_data: Optional[dict]) -> str:
        msg = None
        if not sec_buff_data:
            msg = '无'
            return msg
        hp_msg = f', 消耗当前血量{int(sec_buff_data["hpcost"] * 100)}%' if sec_buff_data['hpcost'] != 0 else ''
        mp_msg = f', 消耗真元{int(sec_buff_data["mpcost"] * 100)}%' if sec_buff_data['mpcost'] != 0 else ''

        if sec_buff_data['skill_type'] == 1:
            sh_msg = ''
            for value in sec_buff_data['atkvalue']:
                sh_msg += f'{value}倍、'
            if sec_buff_data['turncost'] == 0:
                msg = f'攻击{len(sec_buff_data["atkvalue"])}次, 造成{sh_msg[:-1]}伤害{hp_msg}{mp_msg}, 释放概率: {sec_buff_data["rate"]}%'
            else:
                msg = f'连续攻击{len(sec_buff_data["atkvalue"])}次，造成{sh_msg[:-1]}伤害{hp_msg}{mp_msg}，休息{sec_buff_data["turncost"]}回合，释放概率：{sec_buff_data["rate"]}%'
        elif sec_buff_data['skill_type'] == 2:
            msg = f'持续伤害，造成{sec_buff_data["atkvalue"]}倍攻击力伤害{hp_msg}{mp_msg}，持续{sec_buff_data["turncost"]}回合，释放概率：{sec_buff_data["rate"]}%'
        elif sec_buff_data['skill_type'] == 3:
            if sec_buff_data['bufftype'] == 1:
                msg = f'增强自身，提高{sec_buff_data["buffvalue"]}倍攻击力{hp_msg}{mp_msg}，持续{sec_buff_data["turncost"]}回合，释放概率：{sec_buff_data["rate"]}%'
        elif sec_buff_data['bufftype'] == 2:
            msg = f'"增强自身，提高{sec_buff_data["buffvalue"] * 100}%减伤率{hp_msg}{mp_msg}，持续{sec_buff_data["turncost"]}回合，释放概率：{sec_buff_data["rate"]}%"'
        elif sec_buff_data['skill_type'] == 4:
            msg = f'封印对手{hp_msg}{mp_msg}，持续{sec_buff_data["turncost"]}回合，释放概率：{sec_buff_data["rate"]}%，命中成功率{sec_buff_data["success"]}%'

        return msg


buff_helper = BuffHelper()
