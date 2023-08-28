try:
    import ujson as json
except ImportError:
    import json
from pathlib import Path


class DoubleExpCd(object):
    def __init__(self):
        self.dir_path = Path(__file__).parent
        self.data_path = self.dir_path / 'double_exp_cd.json'
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.info = {"double_exp_cd": {}}
            data = json.dumps(self.info, indent=4, ensure_ascii=False)
            with open(self.data_path, 'x', encoding='utf-8') as f:
                f.write(data)
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)

    def find_user(self, user_id: int) -> int:
        """
        匹配词条
        :param user_id:
        """
        user_id = str(user_id)
        try:
            if self.data['double_exp_cd'][user_id] >= 0:
                return self.data['double_exp_cd'][user_id]
        except KeyError:
            self.data['double_exp_cd'][user_id] = 0
            self.__save()
            return self.data['double_exp_cd'][user_id]

    def __save(self):
        """
        :return:保存
        """
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def re_data(self):
        """
        重置数据
        """
        self.data = {"double_exp_cd": {}}
        self.__save()

    def add_user(self, user_id: int) -> bool:
        """
        加入数据
        :param user_id: qq号
        :return: True or False
        """
        user_id = str(user_id)
        if self.find_user(user_id) >= 0:
            self.data["double_exp_cd"][user_id] = self.data["double_exp_cd"][user_id] + 1
            self.__save()
            return True
        return False


double_exp_cd = DoubleExpCd()
