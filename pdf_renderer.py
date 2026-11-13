"""Readable, offline PDF rendering of exported Markdown; no remote assets are loaded."""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path
import textwrap
from html import escape
from urllib.parse import urlsplit

from markdown_it import MarkdownIt
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (HRFlowable, Paragraph, SimpleDocTemplate, Spacer,
                               Table, TableStyle, XPreformatted)

FONT = 'NotoSerifSC'
FONT_PATH = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / 'pdf_fonts' / 'NotoSerifSC.ttf'
if FONT not in pdfmetrics.getRegisteredFontNames():
    pdfmetrics.registerFont(TTFont(FONT, str(FONT_PATH)))
pdfmetrics.registerFontFamily(FONT, normal=FONT, bold=FONT, italic=FONT, boldItalic=FONT)


def _clean(value: str) -> str:
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', value)


def _inline(children) -> str:
    result = []
    links = []
    for t in children or []:
        typ = t.type
        if typ in ('text', 'html_inline'):
            result.append(escape(_clean(t.content)))
        elif typ == 'code_inline':
            result.append('<font color="#86543e">' + escape(_clean(t.content)) + '</font>')
        elif typ in ('softbreak', 'hardbreak'):
            result.append('<br/>')
        elif typ in ('strong_open', 'em_open'):
            result.append('<b>' if typ == 'strong_open' else '<i>')
        elif typ in ('strong_close', 'em_close'):
            result.append('</b>' if typ == 'strong_close' else '</i>')
        elif typ == 'link_open':
            url = t.attrGet('href') or ''
            good = urlsplit(url).scheme.lower() in ('https', 'http', 'mailto')
            links.append(good)
            if good:
                result.append('<link href="' + escape(url, quote=True) + '" color="#86543e">')
        elif typ == 'link_close':
            if links and links.pop(): result.append('</link>')
        elif typ == 'image':
            result.append(escape(_clean(t.content or '[image]')))
    return ''.join(result)


def render_pdf(markdown: str, title: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=55, rightMargin=55,
                            topMargin=58, bottomMargin=56, title=_clean(title))
    base = dict(fontName=FONT, textColor=colors.HexColor('#25231f'),
                leading=18, fontSize=11, spaceAfter=9, alignment=TA_LEFT,
                wordWrap='CJK', splitLongWords=1, allowWidows=0, allowOrphans=0)
    styles = {
        'body': ParagraphStyle('Body', **base),
        'h1': ParagraphStyle('Title', parent=ParagraphStyle('Base', **base), fontSize=21, leading=29, spaceBefore=4, spaceAfter=18, textColor=colors.HexColor('#322c26'), keepWithNext=True),
        'h2': ParagraphStyle('Message', parent=ParagraphStyle('Base2', **base), fontSize=15, leading=22, spaceBefore=13, spaceAfter=10, textColor=colors.HexColor('#955d43'), keepWithNext=True),
        'h3': ParagraphStyle('Heading', parent=ParagraphStyle('Base3', **base), fontSize=12.5, leading=19, spaceBefore=9, spaceAfter=6, keepWithNext=True),
        'small': ParagraphStyle('Table', parent=ParagraphStyle('Base4', **base), fontSize=9.5, leading=15, spaceAfter=0),
        'code': ParagraphStyle('Code', parent=ParagraphStyle('Base5', **base), fontSize=9, leading=14, leftIndent=10, rightIndent=8, backColor=colors.HexColor('#f3f0eb'), spaceBefore=3, spaceAfter=12),
    }
    tokens = MarkdownIt('commonmark', {'html': False}).enable('table').parse(_clean(markdown))
    story = []
    depth = 0
    lists = []
    bullet = None
    quote = 0
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t.type in ('bullet_list_open', 'ordered_list_open'):
            depth += 1
            lists.append([t.type == 'ordered_list_open', int(t.attrGet('start') or 1)])
        elif t.type in ('bullet_list_close', 'ordered_list_close'):
            depth = max(0, depth - 1)
            if lists: lists.pop()
        elif t.type == 'list_item_open':
            if lists and lists[-1][0]:
                bullet = str(lists[-1][1]) + '.'
                lists[-1][1] += 1
            else: bullet = '-'
        elif t.type == 'blockquote_open': quote += 1
        elif t.type == 'blockquote_close': quote = max(0, quote - 1)
        elif t.type in ('heading_open', 'paragraph_open'):
            inline = tokens[i + 1] if i + 1 < len(tokens) and tokens[i + 1].type == 'inline' else None
            if inline:
                level = int(t.tag[1]) if t.type == 'heading_open' else 0
                is_role = level == 2 and inline.content.strip() in {'用户', 'Claude', '系统', 'User', 'System'}
                style = styles['h1' if level == 1 else 'h2' if is_role else 'h3' if level else 'body']
                indent = max(0, depth * 17 + quote * 14)
                if indent:
                    style = ParagraphStyle('Indented', parent=style, leftIndent=indent, firstLineIndent=-12 if bullet else 0)
                content = _inline(inline.children) or '&#160;'
                if bullet:
                    content = escape(bullet) + ' ' + content
                    bullet = None
                story.append(Paragraph(content, style))
                i += 1
        elif t.type in ('fence', 'code_block'):
            # Wrap long source lines without losing text or overflowing the page.
            lines = []
            for line in _clean(t.content).expandtabs(4).splitlines():
                lines.extend(textwrap.wrap(line, width=50, replace_whitespace=False,
                                           drop_whitespace=False, break_long_words=True,
                                           break_on_hyphens=False) or [''])
            story.append(XPreformatted(escape('\n'.join(lines)), styles['code']))
        elif t.type == 'hr':
            story.extend([Spacer(1, 5), HRFlowable(width='100%', thickness=.5, color=colors.HexColor('#ded8cf')), Spacer(1, 6)])
        elif t.type == 'table_open':
            table_rows, row = [], []
            i += 1
            while i < len(tokens) and tokens[i].type != 'table_close':
                item = tokens[i]
                if item.type == 'tr_open': row = []
                elif item.type == 'inline': row.append(_inline(item.children))
                elif item.type == 'tr_close' and row: table_rows.append(row)
                i += 1
            if table_rows:
                columns = max(map(len, table_rows))
                # Extremely wide/long tables are written as readable paragraphs;
                # ordinary tables keep their columns and may span pages.
                if columns > 6 or any(len(cell) > max(100, 1000 // columns) for row in table_rows for cell in row):
                    for row in table_rows:
                        story.append(Paragraph(' · '.join(row), styles['body']))
                else:
                    rows = [[Paragraph(cell or '&#160;', styles['small']) for cell in row] +
                            [Paragraph('&#160;', styles['small'])] * (columns - len(row)) for row in table_rows]
                    table = Table(rows, colWidths=[doc.width / columns] * columns, repeatRows=1, hAlign='LEFT')
                    table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1ede6')),
                                               ('GRID', (0, 0), (-1, -1), .4, colors.HexColor('#d9d2c9')),
                                               ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                               ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6)]))
                    story.extend([table, Spacer(1, 10)])
        i += 1
    if not story: story.append(Paragraph(' ', styles['body']))
    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont(FONT, 9)
        canvas.setFillColor(colors.HexColor('#77716a'))
        canvas.drawRightString(A4[0] - 55, 30, str(document.page))
        canvas.restoreState()
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()
