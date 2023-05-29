from .main import *
config_ = bot.get_config('functions')
log.info('小工具模块加载中...')
if config_.get('default', False):
    from .default import *
    log.info('互动模块加载完毕')
if config_.get('emoji', False):
    try:
        from .emoji import *
        # noinspection PyUnresolvedReferences
        from .emoji.config import UserConfig
        if UserConfig.memes_check_resources_on_startup():
            # noinspection PyUnresolvedReferences
            from meme_generator.download import check_resources
            log.info('正在检查资源文件...')
            asyncio.create_task(check_resources())
        log.info('表情包模块加载完毕')
    except ImportError:
        log.warning('表情包模块加载失败')
if config_.get('game', False):
    from .game import *
    log.info('游戏模块加载完毕')
if config_.get('group', False):
    from .group import *
    log.info('群管理模块加载完毕')
if config_.get('admin', False):
    from .admin import *
    log.info('管理员模块加载完毕')
log.info('小工具模块加载完成')
