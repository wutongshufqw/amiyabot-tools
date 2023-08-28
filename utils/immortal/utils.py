from typing import Union, Tuple

from amiyabot import Message, TencentBotInstance

from .sect import sect_config
from .sql import DataManager


class ImmortalUtils:
    @staticmethod
    def check_user(data: Message):
        """
        判断用户信息是否存在
        :返回参数:
          * `is_user: 是否存在
          * `user_info: 用户
          * `msg: 消息体
        """
        is_user = False
        user_id = int(data.user_id)
        user_info = DataManager.get_user_message(user_id)
        if user_info:
            is_user = True
            msg = ''
        else:
            msg = '修仙界没有道友的信息，请输入 [我要修仙] 加入!'
        return is_user, user_info, msg

    @staticmethod
    def number_to(num: Union[int, float]) -> str:
        """
        递归实现，精确为最大单位值 + 小数点后一位
        :param num:
        :return:
        """
        def astrologize(num_: Union[int, float], level: int) -> Tuple[float, int]:
            if level >= 2:
                return num_, level
            elif num_ >= 10000:
                num_ /= 10000
                level += 1
                return astrologize(num_, level)
            else:
                return num_, level

        units = ['', '万', '亿']
        num, level = astrologize(num, 0)
        if level > len(units):
            level -= 1
        return f'{num:.1f}{units[level]}'

    @staticmethod
    def check_user_type(user_id: int, need_type: int) -> Tuple[bool, str]:
        """
        :说明: `check_user_type`
        > 匹配用户状态，返回是否状态一致
        :返回参数:
          * `is_type: 是否一致
          * `msg: 消息体
        """
        is_type = False
        msg = ''
        user_cd_message = DataManager.get_user_cd(user_id)
        if user_cd_message:
            user_type = user_cd_message.type
        else:
            user_type = 0

        if user_type == need_type:
            is_type = True
        else:
            if user_type == 1:
                msg = "道友现在在闭关呢，小心走火入魔！"
            elif user_type == 2:
                msg = "道友现在在做悬赏令呢，小心走火入魔！"
            elif user_type == 3:
                msg = "道友现在正在秘境中，分身乏术！"
            elif user_type == 0:
                msg = "道友现在什么都没干呢~"
        return is_type, msg

    @staticmethod
    def get_sect_level(sect_id: int) -> Tuple[int, int]:
        sect = DataManager.get_sect_info(sect_id)
        return divmod(sect.sect_scale, sect_config['等级建设度'])


immortal_utils = ImmortalUtils()
