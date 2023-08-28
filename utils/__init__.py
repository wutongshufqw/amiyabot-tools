from .utils import *

resource_path = Path(__file__).parent.joinpath('./resource.zip')

# 判断是否存在资源包
if resource_path.exists():
    # 解压资源包
    unzip_file(resource_path, Path(__file__).parent)
    # 删除压缩包
    resource_path.unlink()

from .oddtext import OddText
from .bottle import Bottle
from .caiyun import Caiyun
from .remake import Life, Talent, PerAgeProperty, PerAgeResult, Summary, save_jpg, draw_life
from .sauceNAO import get_saucenao
from .skland import SklandPlus
from .sql import SQLHelper
from .tarot import Tarot
from .waifu_lab import Waifu
from .zhconv import convert
try:
    from .immortal import Immortal
except ImportError as e:
    log.warning(f'加载Immortal模块失败: {e}')
