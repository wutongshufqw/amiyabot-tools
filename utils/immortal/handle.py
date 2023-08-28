import random
from datetime import datetime
from typing import Tuple, List, Union, Dict, Optional

from .config import data_path, ImmortalConfig
from .data_source import json_data
from .sql import DataManager


class ImmortalJsonData:
    def __init__(self):
        self.root_json_path = data_path / '灵根.json'
        self.level_json_path = data_path / '突破概率.json'

    @staticmethod
    def get_linggen():
        """获取灵根信息"""
        data = json_data.root_data()
        rate_dict = {}
        for i, v in data.items():
            rate_dict[i] = v['type_rate']
        linggen = OtherSet.calculated(rate_dict)
        if data[linggen].get('type_flag'):
            flag = random.choice(data[linggen]['type_flag'])
            root = random.sample(data[linggen]['type_list'], flag)
            msg = ''
            for j in root:
                if j == root[-1]:
                    msg += j
                    break
                msg += (j + '、')

            return msg + '属性灵根', linggen
        else:
            root = random.choice(data[linggen]['type_list'])
            return root, linggen


class OtherSet(ImmortalConfig):
    def __init__(self):
        super().__init__()

    @staticmethod
    def calculated(rate: dict) -> str:
        """
        根据概率计算，轮盘型
        :rate:格式{"数据名":"获取几率"}
        :return: 数据名
        """
        get_list = []  # 概率区间存放

        n = 1
        for name, value in rate.items():  # 生成数据区间
            value_rate = int(value)
            list_rate = [_i for _i in range(n, value_rate + n)]
            get_list.append(list_rate)
            n += value_rate

        now_n = n - 1
        get_random = random.randint(1, now_n)  # 抽取随机数

        index_num = None
        for list_r in get_list:
            if get_random in list_r:  # 判断随机在那个区间
                index_num = get_list.index(list_r)
                break

        return list(rate.keys())[index_num] if index_num else ''

    def set_closing_type(self, level: str) -> float:
        list_all = len(self.level) - 1
        now_index = self.level.index(level)
        if now_index == list_all:
            need_exp = 0.001
        else:
            is_up_data_level = self.level[now_index + 1]
            need_exp = DataManager.get_level_power(is_up_data_level)
        return need_exp

    @staticmethod
    def date_diff(now_time: datetime, old_time: datetime) -> int:
        """计算时间差"""
        diff_time = now_time - old_time
        day = diff_time.days
        sec = diff_time.seconds
        return day * 24 * 60 * 60 + sec

    @staticmethod
    def send_hp_mp(user_id: int, hp: int, mp: int) -> Tuple[List[str], List[int]]:
        user_msg = DataManager.get_user_message(user_id)
        max_hp = int(user_msg.exp / 2)
        max_mp = int(user_msg.exp)

        msg = []
        hp_mp = []

        if user_msg.hp < max_hp:
            if user_msg.hp + hp < max_hp:
                new_hp = user_msg.hp + hp
                msg.append(f'回复气血: {hp}')
            else:
                new_hp = max_hp
                msg.append(f'气血已回满!')
        else:
            new_hp = user_msg.hp
            msg.append('')

        if user_msg.mp < max_mp:
            if user_msg.mp + mp < max_mp:
                new_mp = user_msg.mp + mp
                msg.append(f'回复真元: {mp}')
            else:
                new_mp = max_mp
                msg.append(f'真元已回满!')
        else:
            new_mp = user_msg.mp
            msg.append('')

        hp_mp.append(new_hp)
        hp_mp.append(new_mp)
        hp_mp.append(user_msg.exp)

        return msg, hp_mp

    def get_type(self, user_exp: int, rate: int, user_level: str) -> Union[str, List[str]]:
        list_all = len(self.level) - 1
        now_index = self.level.index(user_level)
        if now_index == list_all:
            return '道友已是最高境界，无法突破!'

        is_up_data_level = self.level[now_index + 1]
        need_exp = DataManager.get_level_power(is_up_data_level)

        # 判断修为是否足够突破
        if user_exp < need_exp:
            return f'道友的修为不足以突破! 距离下次突破需要{need_exp - user_exp}修为! 突破境界为: {is_up_data_level}'

        success_rate = True if random.randint(1, 100) < rate else False

        if success_rate:
            return [self.level[now_index + 1]]
        else:
            return '失败'

    @staticmethod
    def get_power_rate(mind: int, other: int) -> Union[str, int]:
        power_rate = mind / (mind + other)
        if power_rate >= 0.8:
            return '道友偷窃小辈实属天道所不齿!'
        elif power_rate <= 0.05:
            return '道友请不要不自量力!'
        else:
            return int(power_rate * 100)

    @staticmethod
    def player_fight(player_1: Dict[str, Union[int, str]], player_2: Dict[str, Union[int, str]]) -> Tuple[
        List[Dict[str, Union[int, str]]], Optional[str]]:
        """
        回合制战斗
        type_in : 1 为完整返回战斗过程（未加）
        2：只返回战斗结果
        数据示例：
        {"道号": None, "气血": None, "攻击": None, "真元": None, '会心':None}
        """
        play_list = []
        suc = None
        if player_1['气血'] <= 0:
            player_1['气血'] = 1
        if player_2['气血'] <= 0:
            player_2['气血'] = 1
        while True:
            player_1_attack = int(round(random.uniform(0.95, 1.05), 2) * player_1['攻击'])
            if random.randint(0, 100) <= player_1['会心']:
                player_1_attack = int(player_1_attack * player_1['爆伤'])
                msg_1 = '{} 发起会心一击, 造成了 {} 伤害'
            else:
                msg_1 = '{} 发起攻击, 造成了 {} 伤害'

            player_2_attack = int(round(random.uniform(0.95, 1.05), 2) * player_2['攻击'])
            if random.randint(0, 100) <= player_2['会心']:
                player_2_attack = int(player_2_attack * player_2['爆伤'])
                msg_2 = '{} 发起会心一击, 造成了 {} 伤害'
            else:
                msg_2 = '{} 发起攻击, 造成了 {} 伤害'

            player_1_harm: int = int(player_1_attack * (1 - player_2['防御']))
            player_2_harm: int = int(player_2_attack * (1 - player_1['防御']))

            play_list.append({
                'user_id': player_1['user_id'],
                'nickname': player_1['道号'],
                'msg': msg_1.format(player_1['道号'], player_1_harm)
            })
            player_2['气血'] -= player_1_harm
            play_list.append({
                'user_id': player_2['user_id'],
                'nickname': player_2['道号'],
                'msg': f'{player_2["道号"]} 剩余血量: {player_2["气血"]}'
            })
            DataManager.update_user_hp_mp(player_2['user_id'], player_2['气血'], player_2['真元'])
            if player_2['气血'] <= 0:
                play_list.append({
                    'user_id': player_1['user_id'],
                    'nickname': player_1['道号'],
                    'msg': f'{player_1["道号"]} 胜利!'
                })
                suc = player_1["道号"]
                DataManager.update_user_hp_mp(player_2['user_id'], 1, player_2['真元'])
                break

            play_list.append({
                'user_id': player_2['user_id'],
                'nickname': player_2['道号'],
                'msg': msg_2.format(player_2['道号'], player_2_harm)
            })
            player_1['气血'] -= player_2_harm
            play_list.append({
                'user_id': player_1['user_id'],
                'nickname': player_1['道号'],
                'msg': f'{player_1["道号"]} 剩余血量: {player_1["气血"]}'
            })
            DataManager.update_user_hp_mp(player_1['user_id'], player_1['气血'], player_1['真元'])
            if player_1['气血'] <= 0:
                play_list.append({
                    'user_id': player_2['user_id'],
                    'nickname': player_2['道号'],
                    'msg': f'{player_2["道号"]} 胜利!'
                })
                suc = player_2["道号"]
                DataManager.update_user_hp_mp(player_1['user_id'], 1, player_1['真元'])
                break
            if player_1['气血'] <= 0 or player_2['气血'] <= 0:
                play_list.append({
                    'user_id': player_1['user_id'],
                    'nickname': player_1['道号'],
                    'msg': '逻辑错误:('
                })
                break
        return play_list, suc


immortal_json_data = ImmortalJsonData()
other_set = OtherSet()
