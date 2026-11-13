"""Offline Claude export reader and Markdown/PDF renderer."""
from __future__ import annotations

import hashlib
import io
import json
import re
import unicodedata
import zipfile
from pathlib import PurePosixPath
from typing import Any

MAX_INPUT = 200 * 1024 * 1024
MAX_EXPANDED = 300 * 1024 * 1024
MAX_FILES = 5000
MAX_DEPTH = 2

LABELS = {
    'zh': {'citations':'引用信息', 'thinking':'思考内容（导出数据中存在）', 'unavailable':'（该内容未随导出提供）', 'tool_call':'工具调用', 'tool_result':'工具结果', 'untitled':'未命名', 'injected':'附加提示内容', 'other':'其他内容', 'attachments':'附件信息', 'files':'文件信息', 'metadata':'原始导出中的元数据', 'original':'原始 text 字段（与分块内容不同）', 'unnamed_chat':'未命名对话', 'created':'创建时间', 'updated':'更新时间', 'id':'会话 ID', 'summary':'摘要', 'user':'用户', 'assistant':'Claude', 'system':'系统', 'unknown':'未知角色', 'empty':'按当前选项没有可导出的消息内容。', 'manifest':'文件来自所选数据包。没有可转换内容的消息与会话已跳过；附件只包含导出中提供的元数据，原始文件不会自动恢复。'},
    'en': {'citations':'Citations', 'thinking':'Thinking (included in export)', 'unavailable':'(This content was not included in the export.)', 'tool_call':'Tool call', 'tool_result':'Tool result', 'untitled':'Unnamed', 'injected':'Injected prompt', 'other':'Other content', 'attachments':'Attachment information', 'files':'File information', 'metadata':'metadata from the original export', 'original':'Original text field (differs from content blocks)', 'unnamed_chat':'Untitled conversation', 'created':'Created', 'updated':'Updated', 'id':'Conversation ID', 'summary':'Summary', 'user':'User', 'assistant':'Claude', 'system':'System', 'unknown':'Unknown role', 'empty':'No message content can be exported with these options.', 'manifest':'Files come from the selected export. Empty messages and conversations were skipped. Attachment metadata is included when available; missing original files cannot be recovered.'},
}

def _labels(lang: str) -> dict:
    return LABELS['en' if lang == 'en' else 'zh']

class ExportError(ValueError):
    pass

def _conversation_list(obj: Any) -> list[dict] | None:
    if isinstance(obj, dict):
        for key in ('conversations', 'chats'):
            if isinstance(obj.get(key), list):
                obj = obj[key]
                break
    if not isinstance(obj, list) or not obj:
        return None
    rows = [x for x in obj if isinstance(x, dict)]
    if not rows or not any(isinstance(x.get('chat_messages'), list) for x in rows):
        return None
    return [x for x in rows if isinstance(x.get('chat_messages'), list)]

def _memory_list(obj: Any) -> list[dict] | None:
    """Represent each exported memory file as an independently selectable document."""
    if not isinstance(obj, dict) or not isinstance(obj.get('memory_files'), list):
        return None
    return [
        {'name': 'Memory: ' + str(m.get('path') or 'memory'),
         'updated_at': m.get('updated_at') or '',
         'chat_messages': [{'sender': 'system', 'text': m.get('content') or ''}]}
        for m in obj['memory_files'] if isinstance(m, dict)
    ]

def _export_rows(obj: Any) -> list[dict] | None:
    rows = _conversation_list(obj)
    return rows if rows is not None else _memory_list(obj)

def _decode_json(data: bytes, label: str) -> Any:
    try:
        return json.loads(data.decode('utf-8-sig'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExportError(f'无法读取 JSON：{label}') from exc

def load_export(data: bytes, filename: str = '') -> list[dict]:
    if not data or len(data) > MAX_INPUT:
        raise ExportError('文件为空或超过 200 MB 限制。')
    if zipfile.is_zipfile(io.BytesIO(data)):
        found: list[dict] = []
        budget = [0, 0]
        def visit(blob: bytes, depth: int) -> None:
            if depth > MAX_DEPTH:
                raise ExportError('压缩包嵌套层数过多。')
            try:
                with zipfile.ZipFile(io.BytesIO(blob)) as z:
                    entries = z.infolist()
                    budget[0] += len(entries)
                    if budget[0] > MAX_FILES:
                        raise ExportError('压缩包包含过多文件。')
                    for entry in entries:
                        if entry.is_dir() or '__MACOSX' in PurePosixPath(entry.filename).parts:
                            continue
                        leaf = PurePosixPath(entry.filename).name.lower()
                        if not leaf.endswith(('.json', '.zip')):
                            continue
                        budget[1] += entry.file_size
                        if budget[1] > MAX_EXPANDED:
                            raise ExportError('聊天数据解压后超过 300 MB 限制。')
                        if entry.flag_bits & 1:
                            raise ExportError('暂不支持加密压缩包。')
                        if entry.file_size > 10 * 1024 * 1024 and entry.file_size > 1000 * max(entry.compress_size, 1):
                            raise ExportError('压缩包的压缩比例异常。')
                        payload = z.read(entry)
                        if leaf.endswith('.zip'):
                            if zipfile.is_zipfile(io.BytesIO(payload)):
                                visit(payload, depth + 1)
                        else:
                            try:
                                rows = _export_rows(_decode_json(payload, leaf))
                            except ExportError:
                                if leaf == 'conversations.json': raise
                                continue
                            if rows is None and leaf == 'conversations.json':
                                raise ExportError('conversations.json 的结构无法识别。')
                            if rows: found.extend(rows)
            except (zipfile.BadZipFile, RuntimeError, OSError) as exc:
                raise ExportError('压缩包损坏或无法读取。') from exc
        visit(data, 0)
        if not found:
            raise ExportError('没有找到可用的聊天或 Memory 数据。请选择对应的官方导出文件。')
    else:
        found = _export_rows(_decode_json(data, filename or '输入文件')) or []
        if not found:
            raise ExportError('未找到可识别的聊天或 Memory 数据。')
    # A re-packaged archive may contain the same conversations more than once.
    dedup, seen = [], set()
    for row in found:
        uid = str(row.get('uuid') or '').strip()
        key = ('id', uid) if uid else ('content', hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True).encode()).hexdigest())
        if key not in seen:
            dedup.append(row); seen.add(key)
    return dedup

def _printable(value: Any) -> str:
    if value is None: return ''
    if isinstance(value, str): return value
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)

def _fenced(value: Any, lang: str = '') -> str:
    text = _printable(value).strip()
    n = max([len(x) for x in re.findall(r'`+', text)] or [0]) + 1
    fence = '`' * max(3, n)
    return f'{fence}{lang}\n{text}\n{fence}'

def _blocks(message: dict, include_details: bool = True, lang: str = 'zh') -> tuple[list[str], bool]:
    """Return pieces and whether a normal chat text exists, without duplicating text."""
    L = _labels(lang)
    pieces: list[str] = []
    content = message.get('content')
    blocks = content if isinstance(content, list) else []
    normal = [str(b.get('text', '')) for b in blocks if isinstance(b, dict) and b.get('type') == 'text' and isinstance(b.get('text'), str) and b.get('text').strip()]
    fallback = message.get('text') if isinstance(message.get('text'), str) else ''
    has_text = bool(normal or fallback.strip())
    # The text blocks are the conversation body. The parallel text field can
    # contain tool-call placeholders mixed into the same body; keep it only in
    # the detailed export when it differs, so the reading version is not noisy.
    if not include_details:
        if not normal:
            return ([fallback.strip()] if fallback.strip() else []), has_text
        clean = [text.strip() for text in normal]
        remainder = fallback.strip()
        if remainder:
            for text in normal:
                remainder = remainder.replace(text.strip(), '', 1)
            remainder = remainder.replace('```\nThis block is not supported on your current device yet.\n```', '').strip()
            if remainder:
                # An unrecognised difference could be real body text. Preserve the
                # complete field and label it rather than guessing it is noise.
                clean.append('**' + L['original'] + '**\n\n' + fallback.strip())
        return clean, has_text
    used_text = False
    for b in blocks:
        if not isinstance(b, dict):
            if include_details: pieces.append('**' + L['other'] + '**\n\n' + _fenced(b, 'json'))
            continue
        typ = b.get('type', 'unknown')
        if typ == 'text':
            text = b.get('text')
            if isinstance(text, str) and text.strip():
                pieces.append(text.strip()); used_text = True
            if include_details and b.get('citations'):
                pieces.append('**' + L['citations'] + '**\n\n' + _fenced(b['citations'], 'json'))
        elif include_details:
            if typ == 'thinking':
                value = b.get('thinking') or b.get('summaries')
                pieces.append('**' + L['thinking'] + '**\n\n' + (_printable(value).strip() if value else L['unavailable']))
            elif typ == 'tool_use':
                pieces.append('**' + L['tool_call'] + ': ' + str(b.get('name') or L['untitled']) + '**\n\n' + _fenced(b.get('input', {}), 'json'))
            elif typ == 'tool_result':
                pieces.append('**' + L['tool_result'] + ': ' + str(b.get('name') or L['untitled']) + '**\n\n' + _fenced(b.get('content') or b.get('structured_content') or b.get('message') or {}, 'json'))
            elif typ == 'injected_prompt_block':
                pieces.append('**' + L['injected'] + '**\n\n' + _fenced(b.get('prompt', '')))
            else:
                pieces.append('**' + L['other'] + ': ' + str(typ) + '**\n\n' + _fenced(b, 'json'))
    if not used_text and fallback.strip():
        pieces.insert(0, fallback.strip())
    elif used_text and fallback.strip() and fallback.strip() not in '\n'.join(normal):
        pieces.append('**' + L['original'] + '**\n\n' + fallback.strip())
    if include_details:
        for key, label in (('attachments', L['attachments']), ('files', L['files'])):
            value = message.get(key)
            if isinstance(value, list) and value:
                pieces.append('**' + label + ' (' + L['metadata'] + ')**\n\n' + _fenced(value, 'json'))
    return pieces, has_text

def _exportable(message: dict, include_details: bool = True) -> bool:
    if isinstance(message.get('text'), str) and message['text'].strip(): return True
    if include_details and any(isinstance(message.get(k), list) and message[k] for k in ('attachments', 'files')): return True
    blocks = message.get('content')
    if not isinstance(blocks, list): return False
    for b in blocks:
        if not isinstance(b, dict):
            if include_details and b is not None: return True
            continue
        if b.get('type') == 'text' and isinstance(b.get('text'), str) and b['text'].strip(): return True
        if include_details and b.get('type') != 'text' and any(v for k, v in b.items() if k not in ('type', 'name')): return True
    return False

def describe(conversations: list[dict], include_details: bool = True) -> dict:
    rows = []
    skipped_messages = 0
    for i, c in enumerate(conversations):
        ms = [m for m in c.get('chat_messages', []) if isinstance(m, dict)]
        keep = sum(_exportable(m, include_details) for m in ms)
        skipped_messages += len(ms) - keep
        if not keep: continue
        rows.append({'index': i, 'name': str(c.get('name') or '未命名对话'), 'created_at': str(c.get('created_at') or ''), 'updated_at': str(c.get('updated_at') or ''), 'messages': keep, 'missing_text': len(ms) - keep})
    return {'conversations': rows, 'total_messages': sum(x['messages'] for x in rows), 'excluded_messages': skipped_messages, 'excluded_conversations': len(conversations) - len(rows)}

def to_markdown(conversation: dict, include_details: bool = True, lang: str = 'zh') -> str:
    L = _labels(lang)
    title = str(conversation.get('name') or L['unnamed_chat']).replace('\r', ' ').replace('\n', ' ')
    output = [f'# {title}', '']
    if conversation.get('created_at'): output += [f"{L['created']}: {conversation['created_at']}", '']
    if conversation.get('updated_at'): output += [f"{L['updated']}: {conversation['updated_at']}", '']
    if conversation.get('uuid'): output += [f"{L['id']}: {conversation['uuid']}", '']
    summary = conversation.get('summary')
    if isinstance(summary, str) and summary.strip(): output += ['## ' + L['summary'], '', summary.strip(), '']
    messages = [m for m in conversation.get('chat_messages', []) if isinstance(m, dict) and _exportable(m, include_details)]
    if not messages: output += ['> ' + L['empty'], '']
    for message in messages:
        if not isinstance(message, dict):
            output += ['## 未知消息', '', _fenced(message, 'json'), '']; continue
        who = {'human':L['user'], 'user':L['user'], 'assistant':L['assistant'], 'system':L['system']}.get(str(message.get('sender', '')).lower(), str(message.get('sender') or L['unknown']))
        output += ['---', '', '## ' + who, '']
        if message.get('created_at'): output += [f"{'Time' if lang == 'en' else '时间'}: {message['created_at']}", '']
        pieces, _ = _blocks(message, include_details, lang)
        output += ['\n\n'.join(pieces), '']
    return '\n'.join(output).rstrip() + '\n'

def safe_name(value: str, index: int, lang: str = 'zh') -> str:
    value = unicodedata.normalize('NFC', str(value or _labels(lang)['unnamed_chat']))
    value = re.sub(r'[\x00-\x1f<>:"/\\|?*]', '_', value).strip(' .')
    if not value: value = _labels(lang)['unnamed_chat']
    if value.upper() in {'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),*(f'LPT{i}' for i in range(1,10))}: value = '_' + value
    return f'{index + 1:03d}_{value[:75]}'

def to_pdf(markdown: str, title: str) -> bytes:
    try:
        from pdf_renderer import render_pdf
    except ImportError as exc:
        raise ExportError('PDF 组件尚未安装。请按 README 安装依赖。') from exc
    return render_pdf(markdown, title)


def make_output(conversations: list[dict], indices: list[int], fmt: str, include_details: bool = True, lang: str = 'zh') -> tuple[bytes,str,str]:
    if fmt not in ('md','pdf'): raise ExportError('请选择 Markdown 或 PDF。')
    if not indices or any(not isinstance(i,int) or isinstance(i,bool) for i in indices) or len(set(indices))!=len(indices) or any(i<0 or i>=len(conversations) or not any(isinstance(m,dict) and _exportable(m,include_details) for m in conversations[i].get('chat_messages',[])) for i in indices):
        raise ExportError('请选择至少一个有效会话。')
    files=[]
    for i in indices:
        c=conversations[i]; name=safe_name(c.get('name') or '',i,lang); md=to_markdown(c,include_details,lang)
        content=md.encode('utf-8') if fmt=='md' else to_pdf(md, str(c.get('name') or '未命名对话'))
        files.append((name+'.'+fmt,content))
    if len(files)==1:
        name,body=files[0];return body,name,'text/markdown; charset=utf-8' if fmt=='md' else 'application/pdf'
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,body in files:z.writestr(name,body)
        z.writestr('README.txt', _labels(lang)['manifest']+'\n')
    return out.getvalue(),'claude-conversations.zip','application/zip'
