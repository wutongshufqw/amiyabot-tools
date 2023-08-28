<div align="center">
    <img src="https://img1.imgtp.com/2023/08/23/RyQuE7hW.png" width="180" height="180" alt="ToolLogo">
</div>

<div align="center">

# 小工具合集

✨ AmiyaBot 小工具合集插件，自行编写并移植多个NoneBot2插件 ✨

<p align="center">
    <img alt="license" src="https://img.shields.io/badge/license-MIT-green">
    <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python">
    <img src="https://img.shields.io/badge/amiyabot-1.7.0+-red.svg" alt="AmiyaBot">
    <img alt="version" src="https://img.shields.io/badge/version-1.9.8.2-orange">
    <img alt="commit" src="https://img.shields.io/github/commit-activity/m/wutongshufqw/amiyabot-tools?color=%23ff69b4">
    <img alt="size" src="https://img.shields.io/github/repo-size/wutongshufqw/amiyabot-tools?color=%23ffeb3b">
</p>
</div>

# 🎉 公告栏

1. 1.9.8.0更新：
   - 扫雷修复
     - 修复超大地图的报错问题
     - 拓充扫雷地图大小范围
     - 添加开局提示
     - 界面优化
   - 代码优化
     - 移除大量无效代码
     - 优化部分运行逻辑
     - 修复ai部分的报错
   - Skland++开始测试！（请参阅test.md)
2. 1.9.8.1更新：
   - 新增方舟分类
     - Skland++将移入该功能分类
   - 抽象话插件测试
3. 1.9.8.2更新
    - 修仙插件测试
    - 适配AmiyaBot 1.7.0

- 注意：

  1. 从1.9.7.3开始，插件将使用试验性功能进行新功能开发，待功能基本完善后将会发布正式版本
     - 试验功能可能会伴随着其他功能的Bug修复，因此建议更新，如果你不想使用试验功能，可以关闭试验功能的载入
     - 试验功能不会加入到小工具全局管理中，且只有超级管理员能够使用
  2. `<font color=Orange>`小工具所有功能默认关闭(包括更新后新增的), 请私聊兔兔自行开启 `</font>`
  3. `<font color=Red>`**免责声明：伪造消息功能由管理员开启，该功能默认关闭，由于伪造消息而造成的经济，财产，精神损失的与本插件作者无关** `</font>`
  4. 插件所有功能进行了模块化，你可以自由选择导入不同的模块，未导入的模块将不会加载以节约服务器资源, 详见控制台
     - `<font color=Orange>`注意, 该配置项是从代码层面实现配置项的动态加载, 因此修改后需要重新启动兔兔才会生效,
       此配置项优先级高于小工具全局管理`</font>`
  5. 若字体显示错误请参阅[字体安装](https://github.com/MeetWq/meme-generator/blob/main/docs/install.md)

> ## 配置项说明
>
>> ### 戳一戳回复配置类型说明：
>>
>> - `[pixiv]: 随机一张pixiv图片`
>> - `[poke]: 戳回去`
>> - `[face [id]]:发送一张Emoji表情，id为表情id，注意id前后无方括号`
>> - `[emoji]:发送一张存放在emojiPath中的表情`
>> - `[crazy]: KFC疯狂星期四（仅星期四可以触发）`
>>
>
>> ### 昵称配置类型说明：
>>
>> - `text-文本`
>> - `day-运行天数`
>> - `hour-运行小时`
>> - `minute-运行分钟`
>> - `second-运行秒数`
>> - `reply_time-回复时间`
>> - `reply_name-回复昵称`
>> - `mem_use-内存占用`
>> - `cpu_use-CPU占用`
>> - `diy`
>>   -自定义内容，使用说明：例如，你在自定义中的第一条写了 `import time\nvalue=time.strftime('%H:%M:%S', time.localtime())`
>>   ,那么替换部分应当这样写 `1:value`其中1表示第自定义的第一条, value表示自定义中定义的value属性, 以:分隔,
>>   若前后有文字请使用text类型, 请勿在此填写任何多余内容, 你可以发挥想象, 制作你自己昵称！
>>

# 🎉 特别感谢

- [AmiyaBot](https://github.com/AmiyaBot/Amiya-Bot): 基于 AmiyaBot 框架的 QQ 聊天机器人
- [nonebot-plugin-memes](https://github.com/noneplugin/nonebot-plugin-memes): ✨ Nonebot2 表情包制作插件 ✨
- [nonebot-plugin-remake](https://github.com/noneplugin/nonebot-plugin-remake): 适用于 Nonebot2 的人生重开模拟器
- [Enhance for Skland](https://github.com/LaviniaFalcone/Enhance-for-Skland): 森空岛（非官方）游戏实时状态查询工具
- [nonebot-plugin-oddtext](https://github.com/noneplugin/nonebot-plugin-oddtext): Nonebot2 插件，用于抽象话等文本生成

# 许可证

本项目使用 [MIT](https://choosealicense.com/licenses/mit/) 作为开源许可证

# 仓库

- [amiyabot-tools](https://github.com/wutongshufqw/amiyabot-tools): AmiyaBot 小工具合集插件，自行编写并移植多个NoneBot2插件
