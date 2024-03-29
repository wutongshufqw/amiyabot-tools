
## 用法

### 注意：

1. <font color=Orange>小工具所有功能默认关闭(包括更新后新增的), 请私聊兔兔自行开启</font>
2. <font color=Red>**免责声明：伪造消息功能由管理员开启，该功能默认关闭，由于伪造消息而造成的经济，财产，精神损失的与本插件作者无关**</font>
3. 插件所有功能进行了模块化，你可以自由选择导入不同的模块，未导入的模块将不会加载以节约服务器资源, 详见控制台
   - <font color=Orange>注意, 该配置项是从代码层面实现配置项的动态加载, 因此修改后需要重新启动兔兔才会生效, 此配置项优先级高于小工具全局管理</font>
4. 若字体显示错误请参阅[字体安装](https://github.com/MeetWq/meme-generator/blob/main/docs/install.md)

### 基础

- 所有指令中的[]表示可变参数，()表示可选参数
- 超级管理员发送 `兔兔小工具全局管理` 即可进入小工具全局管理
- 管理员发送 `兔兔小工具管理` 即可进入小工具群管理
    - 所有功能默认关闭，需要管理员手动开启
    - 只有全局开启的功能才可以在群聊中进行管理
    - 超级管理功能在群聊中不可管理
- 发送 `兔兔更新小工具`，即可实现插件重载，需要amiyabot>=1.5.1

### 普通

#### 互动

- 戳一戳兔兔，兔兔会随机回复设置的消息
- 发送 `兔兔今天吃什么` , 随机一份菜单
- 管理员发送 `兔兔调整AI概率 [概率(0-50)]` 即可开启人工智障功能( > _ < )
    - 使用 `笑话/歌词/计算/翻译/天气等` 指令时，会有特殊回复哦
- 发送 `兔兔搜索图片` 并附上图片即可
- 发送 `兔兔伪造消息` 即可开始，按照兔兔提示进行即可，本功能默认关闭
    - 管理员发送 `兔兔开启消息伪造` 即可在本群开启功能
    - 管理员发送 `兔兔关闭消息伪造` 即可在本群关闭功能
- 发送 `兔兔[关键词]` 可以触发更多功能哦，关键词参照下方列表
    - `每日一言` ：字如其名
    - `猜谜` ：猜谜语，猜对有奖励哦，回复类型：`我猜xxx` , `提示 `, `结束`
- 发送 `兔兔抽奖` 可以在群聊中进行一次抽奖，详细配置参见配置项
- 发送 `兔兔头像表情包帮助` 可以查看头像表情包的用法( > _ < )本功能仅支持GOCQHttp适配器
    - 发送 `兔兔禁用/启用表情 [关键词列表(空格隔开)]` 可以禁用/启用群聊中用户自己的某些表情包关键词识别
    - 发送 `兔兔全局禁用/启用表情 [关键词列表(空格隔开)]` 可以禁用/启用整个群聊中的某些表情包关键词识别(仅管理员可用)
    - 开启/关闭本群所有表情包识别请对 `兔兔小工具管理` 中的 `合成表情` 进行操作(仅管理员可用)
    - ps: 表情包key可以发送 `兔兔表情详情+关键词` 查看
- 发送 `群友老婆/qylp` 娶一位群友老婆
- 发送 `(Lab)头像生成` 并按照提示进行即可
- 发送 `彩云小梦` 并按照提示进行即可

#### 游戏

- 发送 `兔兔扫雷 (简单/中等/困难)` 即可开启扫雷，也可以通过发送 `兔兔扫雷 列数x行数 雷数 限时` 进行自定义
    - 发送 `行[占位符]列` 即可打开该格
    - 发送 `f 行[占位符]列` 即可标记该格
    - 发送 `提示` 可以在开始前翻开一个没有雷的格子
    - 发送 `退出` 即可结束游戏
    - 将所有非地雷的格子翻开或踩到地雷，游戏结束
    - 自定义的大小限制为 3x3 ~ 100x100
- 发送 `兔兔五子棋` 即可开启五子棋
    - 发送 `行[占位符]列` 即可落子
    - 下棋方发送 `退出` 即可结束游戏
    - 将五子连成一线, 获得1积分
- 漂流瓶（支持文字和多张图片）
    - 发送 `兔兔扔漂流瓶 (匿名/不匿) [内容]` : 请注意文明用语
        - 例如 `兔兔扔漂流瓶 匿名 [内容]` 、 `兔兔扔漂流瓶 [内容]` 都会匿名丢出漂流瓶，默认为匿名
        - 例如 `兔兔扔漂流瓶 不匿 [内容]` 则会让拾到该漂流瓶的用户知道你的昵称
    - 发送 `兔兔捡漂流瓶`捡一个漂流瓶
    - 发送 `兔兔删除漂流瓶 [漂流瓶ID]` : 让这个漂流瓶永远消失（群管理员也可以）
    - 发送 `兔兔删除所有漂流瓶` ：删除所有漂流瓶（仅限超管）
    - 发送 `兔兔查看漂流瓶 [漂流瓶ID]` ：查看指定漂流瓶（仅限超管）
    - 漂流瓶审核请按照兔兔的提示完成
    - ps: 可以通过发送 `兔兔不通过所有漂流瓶` 删除所有未审核的漂流瓶
- 发送 `塔罗牌/塔罗牌占卜` 即可进行塔罗牌占卜
- 发送 `兔兔remake/人生重开/人生重启` 即可启动人生重开模拟器

#### 群管理

- 管理员发送 `兔兔修改群名片 [群名片] (@某群成员)` 即可修改群名片，若未@任何对象，默认修改兔兔群名片
    - <font color=Orange>注意：需要兔兔有相应权限</font>
- 发送 `兔兔修改群头衔 [群头衔] (@某群成员)` 即可修改群头衔，若未@任何对象，默认修改自己头衔
    - <font color=Orange>注意：需要兔兔是群主，且该群聊开启了<font color=Red>头衔显示</font></font>
- 管理员回复对应消息并发送 `兔兔撤回` 即可，只支持群聊
- 新人入群自动发送入群欢迎
    - 管理员发送 `兔兔设置欢迎消息 [欢迎消息]` 即可设置欢迎消息
    - 管理员发送 `兔兔清除欢迎消息` 即可清除欢迎消息
- 群成员退群自动发送退群消息
    - 管理员发送 `兔兔设置退群消息 [退群消息]` 即可设置退群消息, 使用 `{info}` 代表退群成员详细信息
    - 管理员发送 `兔兔清除退群消息` 即可清除退群消息
- 群聊中发送 `兔兔退群` 并 `@兔兔` 即可让兔兔退群

#### 方舟
- Skland++
  - 发送 `兔兔设置凭证` 绑定账号
  - 发送 `兔兔方舟数据` 查询当前游戏内数据

### 超管

#### 实用功能

- 小工具超管发送 `兔兔重启` 即可重启兔兔
    - <font color=Orange>重启提示需要将该bot设置为随启动开启</font>
- 当有人加兔兔好友时，兔兔会发送消息给配置的账号，请按照提示进行处理
    - 发送 `兔兔查看好友申请` 可以查看现有好友申请列表
    - 发送 `兔兔清空好友申请` 可以清空好友申请列表
- 当有人邀请兔兔进群时，兔兔会发送消息给配置的账号，请按照提示进行处理
    - 发送 `兔兔查看邀请` 可以查看现有群聊邀请列表
    - 发送 `兔兔清空邀请` 可以清空群聊邀请列表
- 发送 `更新资源` 即可同步更新卡池图片
- 兔兔被禁言后自动退群（功能要手动开启）
- 刷新群名片，请参阅控制台
- 群聊人数限制，请参阅控制台
