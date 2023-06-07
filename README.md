## 公告栏

- 1.9.6更新：

  1. 提供刷新群名片功能
  2. 1.9.6.1更新：
     - Mirai支持
  3. 1.9.6.2更新：
     - 新增回复更新

- 注意：

  1. <font color=Orange>小工具所有功能默认关闭(包括更新后新增的), 请私聊兔兔自行开启</font>
  2. <font color=Red>**免责声明：伪造消息功能由管理员开启，该功能默认关闭，由于伪造消息而造成的经济，财产，精神损失的与本插件作者无关**</font>
  3. 插件所有功能进行了模块化，你可以自由选择导入不同的模块，未导入的模块将不会加载以节约服务器资源, 详见控制台
     - <font color=Orange>注意, 该配置项是从代码层面实现配置项的动态加载, 因此修改后需要重新启动兔兔才会生效, 此配置项优先级高于小工具全局管理</font>
  4. 若字体显示错误请参阅[字体安装](https://github.com/MeetWq/meme-generator/blob/main/docs/install.md)

## 配置项

- 配置项的一些参考

```yaml
poke: #戳一戳配置
    replies: #戳一戳回复配置
    #特殊标签：
    # [pixiv]:随机一张pixiv图片；
    # [poke]: 戳回去；
    # [face [id]]:发送一张Emoji表情，id为表情id，注意id前后无方括号
    # [emoji]:发送一张存放在emojiPath中的表情
    # [crazy]: KFC疯狂星期四（仅星期四可以触发）
```

[GitHub仓库地址](https://github.com/wutongshufqw/amiyabot-tools)
