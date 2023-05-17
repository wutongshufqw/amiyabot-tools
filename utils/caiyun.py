import json
from typing import List

from amiyabot.network.httpRequests import http_requests
from core import log

model_list = {
    "1": {"name": "小梦0号", "id": "60094a2a9661080dc490f75a"},
    "2": {"name": "小梦1号", "id": "601ac4c9bd931db756e22da6"},
    "3": {"name": "纯爱小梦", "id": "601f92f60c9aaf5f28a6f908"},
    "4": {"name": "言情小梦", "id": "601f936f0c9aaf5f28a6f90a"},
    "5": {"name": "玄幻小梦", "id": "60211134902769d45689bf75"},
}


class CaiyunError(Exception):
    pass


class NetworkError(CaiyunError):
    pass


class AccountError(CaiyunError):
    pass


class ContentError(CaiyunError):
    pass


async def post(url, data):
    resp = None
    for i in range(3):
        resp = await http_requests.post(url, data, timeout=60)
        if resp:
            break
        else:
            log.warning(f'请求 {url} 失败，重试第{i}次')
    if not resp:
        log.error(f'请求 {url} 失败，返回码 {resp.status_code}')
        raise NetworkError('『ERROR』网络出现错误了...')
    result = json.loads(resp)
    if result['status'] == 0:
        return result
    elif result['status'] == -1:
        raise AccountError('『ERROR』账号不存在，请更换apikey！')
    elif result['status'] == -5:
        raise ContentError(
            f'『WARNING』存在不和谐内容\n'
            f'类型：{result["data"]["label"]}\n'
            f'剩余血量：{result["data"]["total_count"] - result["data"]["shut_count"]}'
        )
    elif result['status'] == -6:
        raise AccountError('『ERROR』账号已被封禁，请更换apikey！')
    else:
        raise CaiyunError(f'『ERROR』未知错误\n错误信息：{result["msg"]}')


class Caiyun:
    @staticmethod
    def model_list() -> dict:
        global model_list
        return model_list

    def __init__(self, apikey: str, model: str = "1"):
        self.model: str = model
        self.token: str = apikey
        self.nid: str = ""
        self.branchId: str = ""
        self.nodeId: str = ""
        self.nodeIds: List[str] = []
        self.last_result: str = ""
        self.content: str = ""
        self.contents: List[str] = []

    async def next(self):
        try:
            if not self.nid:
                await self.novel_save()
            await self.add_node()
            await self.novel_ai()
            return ''
        except CaiyunError as e:
            log.error('『ERROR』')
            return str(e)
        except Exception:
            log.error('『ERROR』')
            return '未知错误'

    async def novel_save(self):
        url = f'https://if.caiyunai.com/v2/novel/{self.token}/novel_save'
        params = {'content': self.content, 'title': '', 'ostype': ''}
        result = await post(url, params)
        data = result['data']
        self.nid = data['nid']
        self.branchId = data['novel']['branchid']
        self.nodeId = data['novel']['firstnode']
        self.nodeIds = [self.nodeId]

    async def add_node(self):
        url = f'https://if.caiyunai.com/v2/novel/{self.token}/add_node'
        params = {
            'nodeids': self.nodeIds,
            'choose': self.nodeId,
            'nid': self.nid,
            'value': self.content,
            'ostype': '',
            'lang': 'zh'
        }
        await post(url, params)
        self.last_result += self.content

    async def novel_ai(self):
        global model_list
        url = f'https://if.caiyunai.com/v2/novel/{self.token}/novel_ai'
        params = {
            'nid': self.nid,
            'content': self.content,
            'uid': self.token,
            'mid': model_list[self.model]['id'],
            'title': '',
            'ostype': '',
            'status': 'http',
            'lang': 'zh',
            'branchid': self.branchId,
            'lastnode': self.nodeId,
        }
        result = await post(url, params)
        nodes = result['data']['nodes']
        self.nodeIds = [node['nodeid'] for node in nodes]
        self.contents = [node['content'] for node in nodes]

    def select(self, num: int):
        self.nodeId = self.nodeIds[num]
        self.content = self.content + self.contents[num]
