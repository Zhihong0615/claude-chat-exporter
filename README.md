<p align="center"><img src="docs/assets/claude.svg" width="84" alt="Claude icon"></p>

<h1 align="center">Claude Chat Exporter</h1>

<p align="center"><strong>A little archaeology for your Claude chats. 🪦📜</strong><br>
Bring your conversations and Memory back to the page — no shovel required.</p>

<p align="center"><a href="https://claudeexport.duckdns.org/">Try the online tool</a> · <a href="README.zh-CN.md">简体中文</a></p>


**Online tool:** [claudeexport.duckdns.org](https://claudeexport.duckdns.org/) — files are uploaded to the server for conversion (20 MB maximum). For local-only processing, run the application from source as described below.

Convert conversations and Memory present in an official Claude data export into Markdown or searchable PDF, on your own computer. Available for Windows, macOS, and Linux; the interface supports English and Simplified Chinese. This independent project is not affiliated with Anthropic. Your export is the treasure map: only content actually included in it can be recovered.

## Run from source

Install Python 3.10 or later. The first launch creates a virtual environment and downloads the PDF dependency; conversion itself works offline.

- Windows: run `start-windows.bat`.
- macOS: run `start.command` (if necessary, run `chmod +x start.command start.sh` first).
- Linux: run `./start.sh`; Python's `venv` module and a browser are required.

Keep the terminal open and use the address it prints if your browser does not open automatically. To stop, use the button in the interface or close the terminal.

## Export

Select an official chat or Memory ZIP, an outer ZIP containing those ZIPs, or the JSON itself. Each exported Memory file appears as a separately selectable item. Select conversations, Markdown or PDF, with a clean reading copy selected by default. Enable details to include thinking, tool calls, attachment metadata and other available technical content. The counts and conversation list update with this option. A single conversation downloads directly; multiple conversations are packaged as a ZIP. Inputs are limited to 200 MB and expanded data to 300 MB.

Only content actually present in the input can be converted, including any Memory content present in a Memory export. Messages and conversations without content for the selected mode are skipped and counted; short messages are retained. The reading copy uses body text blocks when available and removes known unsupported-tool placeholders; an unrecognised difference in the original text field is kept and labelled instead of discarded. The tool cannot recover missing bodies or attachment files; available attachment metadata may be included. Unknown content types are preserved as structured text when details are enabled. PDF formats common headings, lists, tables and code blocks and supports searchable Chinese text. Complex Markdown, formulas, emoji, and images may render differently; images are not fetched from the internet. Original timestamp strings are retained without conversion.

## Privacy and security

The application binds to a random port on `127.0.0.1`, checks the local session token and request origin, and does not intentionally send chat data to external services. Your browser sends the selected file to the application running on the same machine. The input file is not modified. Installation of dependencies and building packages require network access. **Do not expose the local server to the public internet.** A separate, limited public backend and example reverse proxy configuration are documented in [deploy/README.md](deploy/README.md); online conversion uploads files to the server. Downloaded documents contain private data; store them accordingly.

## Package for a target platform

Build separately on each target OS and architecture: run `scripts/build-windows.bat` on Windows, or `./scripts/build.sh` on macOS/Linux. Keep the resulting `dist/ClaudeChatExporter/` directory together. These scripts use PyInstaller; distribution on macOS may require signing and notarization. Platform binaries and cross-platform verification are not supplied by the source tree.

## Development

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python app.py
```

Distributed under the MIT license. Claude is a trademark of its respective owner.

The interface bundles Source Han Serif and JetBrains Mono under the SIL Open Font License; the respective license texts are in `web/fonts/`. Georgia is used when installed on the viewer's system and is not redistributed by this project.

The PDF renderer embeds Noto Serif SC (a static instance of the Google Fonts family) under the SIL Open Font License; see `pdf_fonts/OFL.txt`.

Claude icon adapted from [Simple Icons](https://github.com/simple-icons/simple-icons/blob/develop/icons/claude.svg); see its [license and trademark disclaimer](https://github.com/simple-icons/simple-icons/blob/develop/DISCLAIMER.md). Claude is a trademark of its respective owner.
