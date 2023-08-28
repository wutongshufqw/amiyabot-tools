try:
    import ujson as json
except ImportError:
    import json

from .config import data_path


class JsonData:
    """处理基础配置 JSON数据"""
    def __init__(self):
        """基础配置 文件路径"""
        self.root_json_path = data_path / "灵根.json"
        self.level_rate_json_path = data_path / "突破概率.json"
        self.level_json_path = data_path / "境界.json"
        self.sect_json_path = data_path / "宗门玩法配置.json"
        self.BACKGROUND_FILE = data_path / "image" / "background.png"
        self.BOSS_IMG = data_path / "boss_img"
        self.BANNER_FILE = data_path / "image" / "banner.png"
        self.FONT_FILE = data_path / "font" / "sarasa-mono-sc-regular.ttf"

    def root_data(self) -> dict:
        """获取灵根信息"""
        with open(self.root_json_path, "r", encoding="utf8") as f:
            data = json.load(f)
        return data

    def level_data(self) -> dict:
        """境界数据"""
        with open(self.level_json_path, "r", encoding="utf8") as f:
            data = json.load(f)
        return data

    def sect_config_data(self) -> dict:
        """宗门玩法配置"""
        with open(self.sect_json_path, "r", encoding="utf8") as f:
            data = json.load(f)
        return data

    def level_rate_data(self) -> dict:
        """获取境界突破概率"""
        with open(self.level_rate_json_path, "r", encoding="utf8") as f:
            data = json.load(f)
        return data


json_data = JsonData()
