from pathlib import Path

from core import log
from .download_data import download_data


try:
    download_data()
except Exception as e:
    log.error(f'修仙数据下载失败: {e}')


from .buff import UserBuffData, DoubleExpCd, BuffHelper, double_exp_cd, buff_helper
from .config import ImmortalConfig, immortal_config
from .data_source import JsonData, json_data
from .handle import ImmortalJsonData, OtherSet, immortal_json_data, other_set
from .item import ImmortalItem, items
from .sect import sect_config
from .sql import DataManager, ImpartManager, sql_manager, impart_manager
from .utils import ImmortalUtils, immortal_utils


class Immortal:
    @staticmethod
    def get_config() -> ImmortalConfig:
        return immortal_config

    @staticmethod
    def new_json_data() -> ImmortalJsonData:
        return immortal_json_data

    @staticmethod
    def sql_manager() -> DataManager:
        return sql_manager

    @staticmethod
    def utils() -> ImmortalUtils:
        return immortal_utils

    @staticmethod
    def json_data() -> JsonData:
        return json_data

    @staticmethod
    def other_set() -> OtherSet:
        return other_set

    @staticmethod
    def buff_data(user_id: int) -> UserBuffData:
        return UserBuffData(user_id)

    @staticmethod
    def buff_helper() -> BuffHelper:
        return buff_helper

    @staticmethod
    def impart_data() -> ImpartManager:
        return impart_manager

    @staticmethod
    def double_exp_cd() -> DoubleExpCd:
        return double_exp_cd

    @staticmethod
    def help() -> str:
        help_path = Path(__file__).parent / 'readme' / 'help.md'
        with open(help_path, 'r', encoding='utf8') as f:
            help_ = f.read()
        return help_

    @staticmethod
    def items() -> ImmortalItem:
        return items

    @staticmethod
    def work_help() -> str:
        work_path = Path(__file__).parent / 'readme' / 'work.md'
        with open(work_path, 'r', encoding='utf8') as f:
            work = f.read()
        return work

    @staticmethod
    def alchemy_help() -> str:
        alchemy_path = Path(__file__).parent / 'readme' / 'alchemy.md'
        with open(alchemy_path, 'r', encoding='utf8') as f:
            alchemy = f.read()
        return alchemy

    @staticmethod
    def sect_help() -> str:
        sect_path = Path(__file__).parent / 'readme' / 'sect.md'
        with open(sect_path, 'r', encoding='utf8') as f:
            sect = f.read()
        return sect

    @staticmethod
    def sect_config() -> dict:
        return sect_config
