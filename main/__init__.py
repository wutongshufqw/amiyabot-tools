from .main import *
config_ = bot.get_config('functions')
log.info('小工具模块加载中...')
if config_.get('default', False):
    from .default import *
    log.info('互动模块加载完毕')
if config_.get('emoji', False) and emoji_installed:
    from .emoji import *
    log.info('表情包模块加载完毕')
if config_.get('game', False):
    from .game import *
    log.info('游戏模块加载完毕')
if config_.get('group', False):
    from .group import *
    log.info('群管理模块加载完毕')
if config_.get('admin', False):
    from .admin import *
    log.info('管理员模块加载完毕')
log.info('小工具模块加载完毕')
