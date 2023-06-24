from pathlib import Path

from .utils import unzip_file, run_async

if Path(__file__).parent.joinpath('./resource').exists():
    if Path(__file__).parent.joinpath('./resource.zip').exists():
        # 删除压缩包
        Path(__file__).parent.joinpath('./resource.zip').unlink()
else:
    # 解压资源包
    unzip_file(Path(__file__).parent.joinpath('./resource.zip'), Path(__file__).parent)
    # 删除压缩包
    Path(__file__).parent.joinpath('./resource.zip').unlink()


from .sauceNAO import get_saucenao
from .zhconv import convert
from .sql import SQLHelper
from .waifu_lab import Waifu
from .caiyun import Caiyun
from .bottle import Bottle
from .tarot import Tarot
