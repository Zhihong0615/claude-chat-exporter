<p align="center"><img src="docs/assets/claude.svg" width="84" alt="Claude 图标"></p>

<h1 align="center">Claude 聊天导出工具</h1>

<p align="center"><strong>给 Claude 的聊天记录挖个坟，把对话和记忆好好接回来。🪦📜</strong><br>
不用带铲子，带上你的导出包就行。</p>

<p align="center"><a href="https://claudeexport.duckdns.org/">在线使用</a> · <a href="README.md">English</a></p>

**在线使用：**[claudeexport.duckdns.org](https://claudeexport.duckdns.org/) —— 文件会上传到服务器进行转换，最大 20 MB。如需仅在本机处理，请按照下方说明运行源码。

在本机把 Claude 官方数据导出中的聊天记录和 Memory 转成 Markdown 或 PDF。本工具仅处理官方数据导出中已有内容，不读取桌面应用的本地会话或其他目录。支持 Windows、macOS 和 Linux，界面在浏览器中打开；聊天文件只传给本机运行的服务，不发送到外网。

## 运行

**准备：**安装 Python 3.10 或更新版本，并确认能在终端中运行。首次启动会建立 `.venv` 并从 Python 包仓库安装 PDF 组件；这是安装依赖所需的联网，之后转换聊天无需联网。

- Windows：双击 `start-windows.bat`。如果系统没有 `py` 命令，请先安装 Python 并启用启动器。
- macOS：双击 `start.command`；若系统阻止执行，可在终端运行 `chmod +x start.command start.sh`，然后运行 `./start.command`。
- Linux：在本目录运行 `./start.sh`。系统需要提供 Python 的 `venv` 模块和可用的浏览器。

启动后浏览器会自动打开。如果没有打开，请复制启动窗口显示的**本地地址**到浏览器。保持启动窗口打开；结束时在界面点击“关闭本地服务”，或关闭启动窗口。

> 使用随附源码时首次安装依赖需要网络。制作好独立发行包后，运行该发行包不需要 Python 或联网。

## 如何拿到 Claude 导出文件

1. 在 Claude 网页版进入 **Settings（设置）→ Privacy（隐私）→ Export data（导出数据）**，提交导出请求。
2. 收到邮件后，点击 **Download Data（下载数据）**或邮件中的下载链接，按提示登录 Claude。链接在发送后 24 小时失效；过期后可以重新申请。
3. 如果下载页面按类别列出文件，选择 conversations（对话）下载；如有单独的 memories（记忆），也请下载。两者可分别在本工具中转换；ZIP 和 JSON 均可使用，ZIP 不必提前解压。
4. 在本工具中选择下载的 ZIP 或 JSON，再选择会话并导出 Markdown 或 PDF。请保管好邮件链接，无需上传邮件本身。

在线版会上传文件至服务器转换（最大 20 MB）；本地版在设备上处理（最大 200 MB）。步骤参考 [Claude 官方说明](https://support.anthropic.com/en/articles/9450526-how-can-i-export-my-claude-data)和 [Claude Export Viewer](https://github.com/aiaifei/claude-export-viewer)。

## 使用

1. 从 Claude 官方导出文件中选择聊天或 Memory 的 ZIP 或 JSON。也支持包含这些 ZIP 的外层 ZIP；每个 Memory 文件作为独立条目选择。
2. 选择需要导出的会话。列表只显示有可转换内容的会话，并显示已跳过的空记录数量。
3. 选择 Markdown 或 PDF。单个会话直接下载为文档；多个会话下载为 ZIP，每个会话一份文档。
4. 默认生成便于阅读的正文版本。勾选“包含思考过程、工具调用及附件信息”可查看技术细节及附件元数据，未知类型会作为结构化文本保留。

如果选择的是不包含聊天数据的其他导出包，软件会提示重新选择。输入文件最多 200 MB，聊天数据解压合计最多 300 MB。

## 数据范围

- 本工具只转换**输入文件里已有的内容**。没有可转换内容的消息与会话默认跳过，界面显示跳过数量；无法恢复未导出的正文。
- 开启详细内容时，附件或文件条目会以元数据形式保留；本版本不会从账号、外部链接或本机其他目录自动下载或恢复附件原文件。
- PDF 为可搜索文本，支持中文；复杂 Markdown 排版、公式、表情及图片可能与原界面不完全相同。Markdown 保留正文原有文本，通常更适合后续整理。
- 时间直接保留导出文件中的原始字符串，不做地区或时区换算。
- 程序绑定 `127.0.0.1` 的随机端口，转换完成后将文件通过浏览器下载。不会修改输入压缩包，也不会主动上传聊天。

## 打包为独立应用

需要在**目标系统上分别构建**，不能用一个平台的构建结果冒充另一个平台：

- Windows：运行 `scripts/build-windows.bat`。
- macOS / Linux：运行 `./scripts/build.sh`。

脚本会安装 PyInstaller 并将应用放在 `dist/ClaudeChatExporter/`。整个目录均需保留；运行其中的 `ClaudeChatExporter`（Windows 为 `.exe`）。不同 CPU 架构应分别构建和测试；macOS 发行给他人前可能需要按平台要求签名和公证。本仓库不包含其他平台已验证的二进制包。

## 开发与验证

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python app.py
```

## 许可与安全

本项目使用 MIT 许可证，与 Anthropic 无隶属关系。Claude 是其各自所有者的商标。本地服务的防护针对本机使用，**不能直接暴露到公网**。单独的公网后端及示例反向代理配置见 `deploy/README.md`，在线转换会把文件上传到服务器；下载的文件包含私人数据，请妥善保存。

界面附带的思源宋体（Source Han Serif）和 JetBrains Mono 使用 SIL 开放字体许可证，许可文件位于 `web/fonts/`。Georgia 使用访问设备上已安装的字体，本项目不分发该字体。

短消息不会因为长度被删除；无法识别的正文差异会保留并标注。PDF 支持常见标题、列表、表格和代码块，不会从网络加载图片。

PDF 内嵌 Noto Serif SC 字体，按 SIL Open Font License 分发，许可见 `pdf_fonts/OFL.txt`。

Claude 图标取自 [Simple Icons](https://github.com/simple-icons/simple-icons/blob/develop/icons/claude.svg)，许可及商标说明见其[免责声明](https://github.com/simple-icons/simple-icons/blob/develop/DISCLAIMER.md)。
