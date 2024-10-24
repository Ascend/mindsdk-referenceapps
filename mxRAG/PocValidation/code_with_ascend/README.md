<h1 align="center">code with ascend</h1>

## 与code语言模型对话

点击侧边栏与大模型进行对话，询问和你的代码相关的问题

## 轻松理解你的代码

选中代码后通过右键或者'cmd+O'(MacOS)/'ctrl+O'(Windows)让大模型理解并解释你的代码

## 生成代码测试用例

选中代码后通过右键或者'cmd+L'(MacOS)/'ctrl+L'(Windows)让大模型生产专属于你的代码的测试用例

## 修正你的代码

选中代码后通过右键或者'cmd+I'(MacOS)/'ctrl+I'(Windows)让大模型修正代码，使你的代码更加简洁和规范

## 自动补全

在设置中开启自动补全功能，使用'tab'(MacOS)/'tab'(Windows)跟随你书写代码的脚步自动帮助你补全的代码

## 快速入门

修改[package.json](package.json)中的"engines"字段中的"vscode"为自己vscode版本

在code_with_ascend目录下执行

使用以下命令下载依赖：
```
npm install
```
编译
```
npm run compile
```

### 启动调试插件

在code with ascend设置中填写关于你使用的大模型的url和模型名称，成功后即可开始使用插件

### 设置url和模型名称
启动调试插件后，点击vscode Settings->Extensions->Code With Ascend Configuration设置对接的大模型url和名称

### 支持功能
1.侧边栏可以使用聊天窗口问答
2.选中代码,右键菜单Explain your code(ctrl+o)
3.选中代码,右键菜单Generate test cases(ctrl+L)
4.选中代码,右键菜单Rewrite your code(ctrl+I)
5.代码自动提示补全

## 环境依赖

| 软件     | 版本要求     |
|--------|----------|
| node   | >18.20.3 |
| npm    | >10.7.0  |
| vscode | >1.81.2  |