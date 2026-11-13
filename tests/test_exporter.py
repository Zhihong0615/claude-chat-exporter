import io
import json
import unittest
import zipfile
from unittest.mock import patch
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from exporter import ExportError, load_export, describe, to_markdown, to_pdf, make_output, safe_name

EXAMPLE=[{'uuid':'one','name':'示例 / 讨论','created_at':'2026-01-01T00:00:00Z','chat_messages':[
    {'sender':'human','text':'你好，世界','content':[{'type':'text','text':'你好，世界'}]},
    {'sender':'assistant','text':'','content':[{'type':'text','text':'你好！'},{'type':'tool_use','name':'calculate','input':{'x':1}},{'type':'tool_result','name':'calculate','content':[{'type':'text','text':'结果是 1'}]}]},
    {'sender':'human','text':'','content':[],'files':[{'file_name':'report.pdf'}]},
    {'sender':'assistant','content':[{'type':'future_block','value':42}]},
]}]
def archive(entries):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for name,body in entries.items(): z.writestr(name,body)
    return out.getvalue()
class ExporterTests(unittest.TestCase):
    def test_json_and_zip_and_nested_dedup(self):
        raw=json.dumps(EXAMPLE,ensure_ascii=False).encode()
        self.assertEqual(len(load_export(raw)),1)
        self.assertEqual(len(load_export(archive({'a/conversations.json':raw}))),1)
        outer=archive({'a.zip':archive({'conversations.json':raw}),'b.zip':archive({'conversations.json':raw})})
        self.assertEqual(len(load_export(outer)),1)
    def test_fails_for_wrong_files(self):
        with self.assertRaises(ExportError):load_export(archive({'users.json':'[]'}))
        with self.assertRaises(ExportError):load_export(b'{bad')
        with self.assertRaises(ExportError):load_export(b'[]')
    def test_archive_limits(self):
        raw=json.dumps(EXAMPLE,ensure_ascii=False).encode()
        with patch('exporter.MAX_FILES', 1):
            with self.assertRaises(ExportError): load_export(archive({'a.txt':'a','conversations.json':raw}))
        with patch('exporter.MAX_EXPANDED', 10):
            with self.assertRaises(ExportError): load_export(archive({'conversations.json':raw}))
        with patch('exporter.MAX_DEPTH', 0):
            with self.assertRaises(ExportError): load_export(archive({'inner.zip':archive({'conversations.json':raw})}))
    def test_original_text_and_unknown_content_preserved(self):
        row={'chat_messages':[{'text':'Original variant', 'content':[{'type':'text','text':'Block variant'},{'type':'new_type','payload':'kept'}]}]}
        md=to_markdown(row,lang='en')
        self.assertIn('Original variant',md)
        self.assertIn('Block variant',md)
        self.assertIn('kept',md)
    def test_memory_json_zip_and_mixed_export(self):
        memory={'account_uuid':'do-not-export','memory_files':[{'path':'memory.md','content':'Remember this synthetic detail','updated_at':'2026-01-01'}]}
        raw=json.dumps(memory).encode()
        for payload in (raw, archive({'random-id.json':raw}), archive({'memory.zip':archive({'id.json':raw}),'chats.zip':archive({'conversations.json':json.dumps(EXAMPLE).encode()})})):
            rows=load_export(payload)
            row=next(c for c in rows if c['name'].startswith('Memory:'))
            md=to_markdown(row,lang='en')
            self.assertIn('Remember this synthetic detail',md)
            self.assertIn('memory.md',md)
            self.assertNotIn('do-not-export',md)
    def test_text_dedup_details_and_missing(self):
        md=to_markdown(EXAMPLE[0])
        self.assertEqual(md.count('你好，世界'),1)
        self.assertIn('工具调用: calculate',md);self.assertIn('结果是 1',md)
        self.assertNotIn('正文未包含',md)
        self.assertIn('report.pdf',md);self.assertIn('future_block',md)
        self.assertNotIn('工具调用: calculate',to_markdown(EXAMPLE[0],False))
        summary=describe(EXAMPLE + [{'name':'空会话','chat_messages':[{'text':'','content':[]}]}])
        self.assertEqual(summary['excluded_messages'],1)
        self.assertEqual(summary['excluded_conversations'],1)
        self.assertEqual(summary['conversations'][0]['messages'],4)
    def test_safe_names_and_batch(self):
        self.assertNotIn('/',safe_name('a/../b',0))
        self.assertNotEqual(safe_name('CON',0),'001_CON')
        data,name,mime=make_output(EXAMPLE,[0],'md')
        self.assertTrue(name.endswith('.md'));self.assertIn('你好',data.decode());self.assertEqual(mime,'text/markdown; charset=utf-8')
        copies=EXAMPLE+[dict(EXAMPLE[0],uuid='two')]
        data,name,mime=make_output(copies,[0,1],'md')
        self.assertEqual(mime,'application/zip')
        with zipfile.ZipFile(io.BytesIO(data)) as z:self.assertEqual(len([n for n in z.namelist() if n.endswith('.md')]),2)
        for invalid in ([],[0,0],[-1],[2],[True]):
            with self.assertRaises(ExportError):make_output(EXAMPLE,invalid,'md')
    def test_english_document_and_empty_filter(self):
        row=dict(EXAMPLE[0], name='')
        md=to_markdown(row,lang='en')
        self.assertIn('# Untitled conversation',md)
        self.assertIn('## User',md)
        self.assertIn('Tool call: calculate',md)
        self.assertNotIn('## 用户',md)
        data,name,_=make_output([row],[0],'md',lang='en')
        self.assertIn('Untitled conversation',name)
        self.assertIn('report.pdf',data.decode())

    def test_pdf(self):
        data=to_pdf(to_markdown(EXAMPLE[0]),'示例')
        self.assertTrue(data.startswith(b'%PDF-'))
        self.assertIn(b'%%EOF',data[-40:])

    def test_clean_mode_keeps_body_and_preserves_unrecognised_difference(self):
        placeholder='```\nThis block is not supported on your current device yet.\n```'
        row={'chat_messages':[
            {'sender':'assistant','text':placeholder+'\n\n正文', 'content':[{'type':'tool_use','input':{'q':'hidden'}},{'type':'text','text':'正文'}]},
            {'sender':'human','text':'好'},
            {'sender':'assistant','text':'Different original text', 'content':[{'type':'text','text':'Block text'}]},
            {'sender':'human','attachments':[{'file_name':'only.pdf'}]},
            {'sender':'human','text':''},
        ]}
        md=to_markdown(row,False,'en')
        self.assertEqual(md.count('正文'),1)
        self.assertNotIn('not supported',md)
        self.assertNotIn('only.pdf',md)
        for text in ('好', 'Different original text', 'Block text'): self.assertIn(text,md)
        self.assertIn('only.pdf',to_markdown(row,True,'en'))
        result=describe([row,{'chat_messages':[{'attachments':[{'file_name':'x'}]}]}],False)
        self.assertEqual((result['total_messages'],result['excluded_messages'],result['excluded_conversations']),(3,3,1))
        self.assertEqual(describe([row],True)['total_messages'],4)

    def test_pdf_renders_complex_and_long_content(self):
        md='# A 中英文 title\n\n## Claude\n\n**bold** and [link](https://example.org)\n\n'
        md+='- First item\n- 第二项\n\n| Column | 列 |\n| --- | --- |\n| alpha | 数据 |\n\n'
        md+='```python\n' + ('    print("中文")\n' * 250) + '```\n\nAfter the code.'
        data=to_pdf(md,'Example')
        self.assertTrue(data.startswith(b'%PDF-'))
        self.assertIn(b'%%EOF',data[-40:])
if __name__=='__main__':unittest.main()
