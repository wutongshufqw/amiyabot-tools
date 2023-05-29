class NetworkError(Exception):
    pass


class PlatformUnsupportedError(Exception):
    def __init__(self, platform: str):
        self.platform = platform
