import zipfile
from pathlib import Path


def unzip_file(oriPath, goalPath):
    """
    解决解压zip包时的中文乱码问题
    :param oriPath: 压缩文件的地址
    :param goalPath: 解压后存放的的目标位置
    :return: None
    """
    with zipfile.ZipFile(oriPath, 'r') as zf:
        # 解压到指定目录,首先创建一个解压目录
        if not Path(goalPath).exists():
            Path(goalPath).mkdir()
        for old_name in zf.namelist():
            # 获取文件大小，目的是区分文件夹还是文件，如果是空文件应该不好用。
            file_size = zf.getinfo(old_name).file_size
            # 由于源码遇到中文是cp437方式，所以解码成gbk，windows即可正常
            new_name = Path(old_name.encode('cp437').decode('gbk'))
            # 拼接文件的保存路径
            new_name = Path(goalPath).joinpath(new_name)
            # 判断是文件夹还是文件
            if file_size > 0:
                # 文件直接写入
                with open(new_name, 'wb') as f:
                    f.write(zf.read(old_name))
            else:
                # 文件夹创建
                new_name.mkdir(parents=True, exist_ok=True)


if Path(__file__).parent.joinpath('./resource').exists():
    if Path(__file__).parent.joinpath('./resource.zip').exists():
        # 删除压缩包
        Path(__file__).parent.joinpath('./resource.zip').unlink()
else:
    # 解压资源包
    unzip_file(Path(__file__).parent.joinpath('./resource.zip'), Path(__file__).parent)
    # 删除压缩包
    Path(__file__).parent.joinpath('./resource.zip').unlink()
