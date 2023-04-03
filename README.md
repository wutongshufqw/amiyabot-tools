# 公告栏

- 新增卡池图片更新功能
- 注意：
    1. <font color=Orange>更新前请阅读新增的配置项说明</font>
    2. <font color=Orange>参数之间记得加空格, 指令中的[]仅表示这是一个可变参数，无需输入"[]"哦</font>
    3. <font color=Red>**免责声明：伪造消息功能由管理员开启，该功能默认关闭，由于伪造消息而造成的经济，财产，精神损失的与本插件作者无关**
       </font>

## 用法

### 普通

#### 互动

- 戳一戳兔兔，兔兔会随机回复设置的消息
- 发送`兔兔今天吃什么`, 随机一份菜单
- 管理员发送`兔兔调整AI概率 [概率(0-50)]`即可开启人工智障功能( > _ < )
    - 使用`笑话/歌词/计算/翻译/天气等`指令时，会有特殊回复哦
- 发送`兔兔搜索图片`并附上图片即可
- 发送`兔兔伪造消息`即可激活功能，按照兔兔提示进行即可
    - 管理员发送`兔兔开启消息伪造`即可开启功能
    - 管理员发送`兔兔关闭消息伪造`即可开启功能
- 发送`兔兔[关键词]`可以触发更多功能哦，关键词参照下方列表
    - `每日一言`：字如其名
    - `猜谜`：猜谜语，猜对有奖励哦，回复类型：`我猜xxx`, `提示`, `结束`

#### 游戏

- 发送`兔兔扫雷 (简单/中等/困难)`即可开启扫雷，也可以通过发送`兔兔扫雷 列数x行数 雷数 限时`进行自定义
    - 发送`行[占位符]列`即可打开该格
    - 发送`f 行[占位符]列`即可标记该格
    - 发送`退出`即可结束游戏
    - 将所有非地雷的格子翻开或踩到地雷，游戏结束
- 发送`兔兔五子棋`即可开启五子棋
    - 发送`行[占位符]列`即可落子
    - 下棋方发送`退出`即可结束游戏
    - 将五子连成一线，游戏结束

#### 群管理

- 管理员发送`兔兔修改群名片 [群名片] (@某群成员)`即可修改群名片，若未@任何对象，默认修改兔兔群名片
    - <font color=Orange>注意：需要兔兔有相应权限</font>
- 发送`兔兔修改群头衔 [群头衔] (@某群成员)`即可修改群头衔，若未@任何对象，默认修改自己头衔
    - <font color=Orange>注意：需要兔兔是群主，且该群聊开启了<font color=Red>头衔显示</font></font>
- 管理员回复对应消息并发送`兔兔撤回`即可，只支持群聊
- 新人入群自动发送入群欢迎
    - 管理员发送`兔兔设置欢迎消息 [欢迎消息]` 即可设置欢迎消息
    - 管理员发送`兔兔清除欢迎消息` 即可清除欢迎消息

### 超管

#### 管理功能

- 超级管理员私聊兔兔`兔兔重启`即可重启兔兔
    - <font color=Orange>重启提示需要将该bot设置为随启动开启</font>
- 当有人加兔兔好友时，兔兔会发送消息给配置的账号，请按照提示进行处理
    - 发送`兔兔查看好友申请`可以查看现有好友申请列表
    - 发送`兔兔清空好友申请`可以清空好友申请列表
- 当有人邀请兔兔进群时，兔兔会发送消息给配置的账号，请按照提示进行处理
    - 发送`兔兔查看邀请`可以查看现有群聊邀请列表
    - 发送`兔兔清空邀请`可以清空群聊邀请列表
- 发送`兔兔更新卡池图片`即可更新卡池图片

## 配置项

- 配置文件位于 resource/plugins/tools/config.yaml中
- 具体参数

```yaml
poke: #戳一戳配置
    cd: #戳一戳冷却时间, 单位：秒, -1表示禁用
    replies: #戳一戳回复配置
    #特殊标签： [pixiv]:随机一张pixiv图片；[poke]: 戳回去；[face [id]]:发送一张Emoji表情，id为表情id，注意id前后无方括号
    #详细设置请参考config文件
specialTitle: #群头衔配置
    cd: # 群头衔设置冷却时间，仅对非管理成员生效，单位：秒，默认30分钟
    admin: #是否允许管理员设置群头衔, 能设置所有成员, 默认为FALSE
    guest: #是否允许群成员设置群头衔, 只能设置自己, 默认为FALSE
restart: #重启配置
    - 123456 #注意：参数列表请删除文件中的'[]'，并使用 '-'，参考poke中的replies
    - 654321 #配置可以重启的用户列表默认为空，注意请使用数字而非字符串，不带引号的那种
operator: #管理好友，群聊请求的QQ账号，注意请使用数字
sauceNAO: #sauceNAO配置
    api_key: #api_key: 前往 https://saucenao.com/user.php 注册后，去 https://saucenao.com/user.php?page=search-api 即可获取
    proxy: #http(s)代理，形如 host:port，可以通过代理软件获取，方便配置独立的代理，不影响其他插件，可以为null
```

- config.yaml实时更新，无需重启bot

[GitHub仓库地址](https://github.com/wutongshufqw/amiyabot-tools)

| 版本  |     变更      |
|:---:|:-----------:|
| 0.2 |    戳一戳功能    |
| 0.3 |   修改群名片功能   |
| 0.4 |   修改群头衔功能   |
| 0.5 |   兔兔重启功能    |
| 0.6 |  通过好友请求功能   |
| 0.7 |   撤回群消息功能   |
| 0.8 |   今日菜单功能    |
| 0.9 | 添加好友与重启功能迭代 |
| 1.0 |  新增人工智障功能   |
| 1.1 | sauceNAO搜图  |
| 1.2 |    扫雷小游戏    |
| 1.3 |   伪造消息功能    |
| 1.4 |  通过群聊邀请功能   |
| 1.5 |   五子棋小游戏    |
| 1.6 |  更新卡池图片功能   |
