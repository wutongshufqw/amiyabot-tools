from core import log

from .main import *
config_ = bot.get_config('functions')
log.info('小工具模块加载中...')
if config_.get('default', False):
    try:
        from .default import *
        log.info('互动模块加载完毕')
    except ImportError:
        log.warning('互动模块加载失败')
if config_.get('emoji', False):
    try:
        from .emoji import *
        log.info('表情包模块加载完毕')
    except ImportError as e:
        print(e)
        log.warning('表情包模块加载失败')
if config_.get('game', False):
    try:
        from .game import *
        log.info('游戏模块加载完毕')
    except ImportError as e:
        print(e)
        log.warning('游戏模块加载失败')
if config_.get('group', False):
    try:
        from .group import *
        log.info('群应用模块加载完毕')
    except ImportError as e:
        print(e)
        log.warning('群应用模块加载失败')
if config_.get('admin', False):
    try:
        from .admin import *
        log.info('管理员模块加载完毕')
    except ImportError as e:
        print(e)
        log.warning('管理员模块加载失败')
if config_.get('test', False):
    try:
        from .admin import *
        log.info('试验性功能加载完毕')
    except ImportError as e:
        print(e)
        log.warning('试验性功能加载失败')
log.info('小工具模块加载完成')
