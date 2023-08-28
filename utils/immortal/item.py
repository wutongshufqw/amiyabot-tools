from typing import Union, Optional

try:
    import ujson as json
except ImportError:
    import json

from .config import data_path

skill_path = data_path / '功法'
weapon_path = data_path / '装备'
elixir_path = data_path / '丹药'
immortal_item_path = data_path / '修炼物品'


def read_f(file_path) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_f(data: dict):
    file_path = data_path / 'items.json'
    data = json.dumps(data, ensure_ascii=False, indent=4)
    save_mode = 'w' if file_path.exists() else 'x'
    with open(file_path, save_mode, encoding="utf-8") as f:
        f.write(data)


class ImmortalItem:
    def __init__(self):
        self.main_buff_json_path = skill_path / "主功法.json"
        self.sec_buff_json_path = skill_path / "神通.json"
        self.weapon_json_path = weapon_path / "法器.json"
        self.armor_json_path = weapon_path / "防具.json"
        self.elixir_json_path = elixir_path / "丹药.json"
        self.yaocai_json_path = elixir_path / "药材.json"
        self.mix_elixir_type_json_path = elixir_path / "炼丹丹药.json"
        self.ldl_json_path = elixir_path / "炼丹炉.json"
        self.jlq_json_path = immortal_item_path / "聚灵旗.json"
        self.items = {}
        self.set_item_data(self.get_armor_data(), "防具")
        self.set_item_data(self.get_weapon_data(), "法器")
        self.set_item_data(self.get_main_buff_data(), "功法")
        self.set_item_data(self.get_sec_buff_data(), "神通")
        self.set_item_data(self.get_elixir_data(), "丹药")
        self.set_item_data(self.get_yaocai_data(), "药材")
        self.set_item_data(self.get_mix_elixir_type_data(), "合成丹药")
        self.set_item_data(self.get_ldl_data(), "炼丹炉")
        self.set_item_data(self.get_jlq_data(), "聚灵旗")
        save_f(self.items)

    def set_item_data(self, data: dict, name: str):
        for k, v in data.items():
            if name in ['功法', '神通']:
                v['rank'], v['level'] = v['level'], v['rank']
                v['type'] = '技能'
            self.items[k] = v
            self.items[k].update({'item_type': name})

    def get_armor_data(self) -> dict:
        return read_f(self.armor_json_path)

    def get_weapon_data(self) -> dict:
        return read_f(self.weapon_json_path)

    def get_main_buff_data(self) -> dict:
        return read_f(self.main_buff_json_path)

    def get_sec_buff_data(self) -> dict:
        return read_f(self.sec_buff_json_path)

    def get_elixir_data(self) -> dict:
        return read_f(self.elixir_json_path)

    def get_yaocai_data(self) -> dict:
        return read_f(self.yaocai_json_path)

    def get_mix_elixir_type_data(self) -> dict:
        return read_f(self.mix_elixir_type_json_path)

    def get_ldl_data(self) -> dict:
        return read_f(self.ldl_json_path)

    def get_jlq_data(self) -> dict:
        return read_f(self.jlq_json_path)

    def get_data_by_item_id(self, item_id: Union[str, int]) -> Optional[dict]:
        return self.items.get(str(item_id))


items = ImmortalItem()
