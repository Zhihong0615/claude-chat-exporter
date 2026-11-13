'use strict';
const $ = id => document.getElementById(id);
let token = new URLSearchParams(location.hash.slice(1)).get('token') || '';
let publicMode = false, initializing = true;
const dict={
 en:{eyebrow:'LOCAL EXPORTER',title:'Claude Chat Exporter',subtitle:'Turn your official export into readable documents.',language:'Language',local:'Processed locally',choose:'Choose a chat or Memory export',support:'Chat or Memory ZIP / JSON',drop:'Click to choose a file, or drop it here',max:'Processed on this device · 200 MB max',select:'Select conversations',all:'Select all',search:'Search titles',format:'Choose a format',mdDesc:'Editable and easy to archive',pdfDesc:'Ready to read and share',details:'Include thinking, tool calls and attachment metadata',detailsHelp:'Off by default for a cleaner reading copy. Turn on to include technical details and entries without chat text.',zipHelp:'Multiple conversations are downloaded as a ZIP',export:'Export documents',footer:'No sign-in · No chat uploads · Original file unchanged',stop:'Stop local service',reading:'Reading file…',ready:'File loaded. Select conversations to export.',none:'No conversations with exportable content were found.',skipped:(c,m)=>`Skipped ${c} conversations and ${m} messages with no content for the current option. Enable details to include technical and attachment-only entries.`,skippedFull:(c,m)=>`Skipped ${c} conversations and ${m} messages without exportable content.`,stats:(c,m)=>`${c} conversations · ${m} exportable messages`,count:(n,total)=>`${n} / ${total} selected`,selected:n=>`${n} conversations selected`,message:n=>`${n} exportable messages`,skippedShort:n=>`${n} skipped`,noMatch:'No matching conversations',pdfWait:'Generating PDF. Large exports may take a moment…',mdWait:'Generating Markdown…',done:'Your file is ready. Check your browser downloads.',failed:'Conversion failed. Check the file and try again.',stopped:'The local service has stopped. You can close this page.',stopError:'The service may already be stopped.',noToken:'Missing local session. Please restart the app.',untitled:'Untitled conversation',badArchive:'Could not find readable conversations or Memory. Choose an official export ZIP or JSON.',tooLarge:'The file is empty, too large, or could not be read.',pdfMissing:'The PDF component is not installed. See the README.'},
 zh:{eyebrow:'本地导出',title:'Claude 聊天导出',subtitle:'把官方导出包转换成方便阅读和保存的文档。',language:'语言',local:'仅在本机处理',choose:'选择聊天或 Memory 导出文件',support:'支持聊天或 Memory 的 ZIP / JSON',drop:'点击选择文件，或将文件拖到这里',max:'文件仅在本机转换，最大 200 MB',select:'选择要导出的会话',all:'全选',search:'搜索会话标题',format:'选择输出格式',mdDesc:'可编辑，适合归档或再次整理',pdfDesc:'适合阅读和分享',details:'包含思考过程、工具调用及附件信息',detailsHelp:'默认关闭，以便阅读正文；开启后可查看技术细节和只有附加信息的记录。',zipHelp:'多个会话将打包为 ZIP 下载',export:'导出文档',footer:'无需登录 · 不上传聊天数据 · 输入文件不会被修改',stop:'关闭本地服务',reading:'正在读取文件…',ready:'读取完成。请选择需要导出的会话。',none:'没有找到有内容的会话。',skipped:(c,m)=>`当前选项跳过 ${c} 个无可导出内容的会话和 ${m} 条消息；开启详细内容可查看只有技术信息或附件信息的记录。`,skippedFull:(c,m)=>`已跳过 ${c} 个没有可导出内容的会话和 ${m} 条消息。`,stats:(c,m)=>`${c} 个会话 · ${m} 条可导出消息`,count:(n,total)=>`已选择 ${n} / ${total}`,selected:n=>`已选择 ${n} 个会话`,message:n=>`${n} 条可导出消息`,skippedShort:n=>`${n} 条已跳过`,noMatch:'没有匹配的会话',pdfWait:'正在生成 PDF，会话较多时可能需要一些时间…',mdWait:'正在生成 Markdown…',done:'已生成文件，请在浏览器下载记录中查看。',failed:'转换失败，请检查文件并重试。',stopped:'本地服务已关闭，可以关闭此页面。',stopError:'服务可能已关闭。',noToken:'缺少本地会话信息，请重新运行软件。',untitled:'未命名对话',badArchive:'没有找到可读取的聊天或 Memory。请选择官方导出 ZIP 或 JSON。',tooLarge:'文件为空、过大或无法读取。',pdfMissing:'PDF 组件尚未安装，请查看使用说明。'}
};
Object.assign(dict.en, {tagline:'Locked out, lost touch, or just saving a copy? Dig through your Claude export and bring your conversations and memories back.', disclaimerLabel:'PLEASE READ', disclaimerTitle:'Disclaimer & privacy', disclaimerIntro:'Please review how this tool handles your data before continuing.', disclaimerPrivacyTitle:'Privacy', disclaimerPrivacy:'Your selected file is processed on this device and is not uploaded by this application.', disclaimerIndependent:'This is an independent project and is not affiliated with Anthropic or Claude.', disclaimerScope:'Only content present in your export can be converted; missing messages and attachment files cannot be recovered. Check the output before relying on it.', disclaimerResponsibility:'The software is provided as is. You are responsible for safeguarding the files you export.', disclaimerContinue:'I understand and continue', disclaimerLink:'Disclaimer'});
Object.assign(dict.zh, {tagline:'被封号、走散了，还是只想留个备份？来给 Claude 掘个坟，把导出包里的对话和记忆挖出来。', disclaimerLabel:'使用前请阅读', disclaimerTitle:'免责声明与隐私提示', disclaimerIntro:'继续使用前，请了解本工具如何处理你的数据。', disclaimerPrivacyTitle:'数据隐私', disclaimerPrivacy:'你选择的文件仅在本机处理，本程序不会将聊天文件上传到外网。', disclaimerIndependent:'这是独立项目，与 Anthropic 和 Claude 没有隶属关系。', disclaimerScope:'只能转换导出文件中已有的内容，无法恢复缺失的消息或附件原文件；请核对转换结果。', disclaimerResponsibility:'本软件按现状提供，请自行妥善保管导出的文件。', disclaimerContinue:'我已了解，继续使用', disclaimerLink:'免责声明'});
Object.assign(dict.en, {
 guideTitle:'How do I get my Claude export?',
 guideRequestTitle:'Request an export', guideRequest:'In Claude on the web, open Settings → Privacy → Export data and submit the request.',
 guideEmailTitle:'Open the email', guideEmail:'When the export is ready, open Claude’s email and choose Download Data or its download link. Sign in to Claude if prompted.',
 guideDownloadTitle:'Download your files', guideDownload:'If the download page lists data categories, save the conversations file and, if available, the separate memories file. ZIP or JSON works; convert each file here in turn.',
 guideConvertTitle:'Choose a file below', guideConvert:'Choose the downloaded ZIP or JSON below, select conversations, then export as Markdown or PDF. No need to unzip first.',
 guideExpiry:'The email link expires after 24 hours; request a new export if it expires. Keep the link private and do not upload the email itself.', guideOfficial:'Official export instructions ↗',
 busyRetry:'The service is busy or you made requests too quickly. Please wait a moment and try again.'
});
Object.assign(dict.zh, {
 guideTitle:'还没有导出文件？查看获取步骤',
 guideRequestTitle:'在 Claude 中申请导出', guideRequest:'在 Claude 网页版打开 Settings（设置）→ Privacy（隐私）→ Export data（导出数据），提交导出请求。',
 guideEmailTitle:'打开导出邮件', guideEmail:'导出准备好后，打开 Claude 发来的邮件，点击 Download Data（下载数据）或邮件中的下载链接；如果页面提示，请先登录 Claude。',
 guideDownloadTitle:'保存下载文件', guideDownload:'如果下载页面按类别列出文件，选择 conversations（对话）下载；如有单独的 memories（记忆），也请下载。ZIP 或 JSON 都可以，分别在这里转换。',
 guideConvertTitle:'在下方选择文件', guideConvert:'在下方选择下载的 ZIP 或 JSON，选择会话，再导出 Markdown 或 PDF；ZIP 不用提前解压。',
 guideExpiry:'邮件下载链接在发送后 24 小时失效；过期后可重新申请导出。请妥善保管链接，无需上传邮件本身。', guideOfficial:'查看官方导出说明 ↗',
 busyRetry:'服务繁忙或操作过快，请稍等片刻后重试。'
});
let lang=navigator.language.toLowerCase().startsWith('zh')?'zh':'en';
const fileInput=$('file'),drop=$('drop'),fileStatus=$('file-status'),exportStatus=$('export-status');
let file=null,rows=[],selected=new Set(),busy=false,summary=null;
function tr(k,...args){const v=dict[lang][k];return typeof v==='function'?v(...args):v}
function status(el,msg,error=false){el.textContent=msg;el.classList.toggle('error',error)}
function setBusy(flag){busy=flag;$('export').disabled=flag||selected.size===0;fileInput.disabled=flag;$('details').disabled=flag;$('stop').disabled=flag}
function updateCount(){const n=selected.size;$('selected-count').textContent=tr('count',n,rows.length);$('export-count').textContent=tr('selected',n);$('select-all').checked=n===rows.length&&n>0;$('select-all').indeterminate=n>0&&n<rows.length;$('export').disabled=busy||n===0}
function renderList(){const list=$('list');list.replaceChildren();const search=$('search').value.trim().toLocaleLowerCase();let count=0;for(const row of rows){const name=row.name==='未命名对话'?tr('untitled'):row.name;if(search&&!name.toLocaleLowerCase().includes(search))continue;count++;const label=document.createElement('label');label.className='chat';const check=document.createElement('input');check.type='checkbox';check.checked=selected.has(row.index);check.addEventListener('change',()=>{check.checked?selected.add(row.index):selected.delete(row.index);updateCount()});const content=document.createElement('div');const title=document.createElement('div');title.className='title';title.textContent=name;const meta=document.createElement('div');meta.className='meta';meta.textContent=tr('message',row.messages)+(row.created_at?' · '+row.created_at:'');if(row.missing_text){const miss=document.createElement('span');miss.className='missing';miss.textContent=' · '+tr('skippedShort',row.missing_text);meta.append(miss)}content.append(title,meta);label.append(check,content);list.append(label)}if(!count){const empty=document.createElement('div');empty.className='chat meta';empty.textContent=tr('noMatch');list.append(empty)}}
function updateSummary(){if(!summary)return;const current=$('details').checked?summary.with_details:summary;$('stats').textContent=tr('stats',rows.length,current.total_messages);const warn=$('warning');if(current.excluded_messages||current.excluded_conversations){warn.textContent=tr($('details').checked?'skippedFull':'skipped',current.excluded_conversations,current.excluded_messages);warn.classList.remove('hidden')}else{warn.textContent='';warn.classList.add('hidden')}}
function applyDetailsMode(){if(!summary)return;const allSelected=rows.length===0||selected.size===rows.length;rows=($('details').checked?summary.with_details:summary).conversations;selected=new Set(rows.filter(r=>allSelected||selected.has(r.index)).map(r=>r.index));updateSummary();renderList();updateCount();status(fileStatus,rows.length?tr('ready'):tr('none'),!rows.length)}
function applyLanguage(){document.documentElement.lang=lang==='zh'?'zh-CN':'en';document.title=tr('title');$('language').value=lang;$('disclaimer-language').value=lang;document.querySelectorAll('[data-i18n]').forEach(el=>el.textContent=tr(el.dataset.i18n));document.querySelectorAll('[data-i18n-placeholder]').forEach(el=>{el.placeholder=tr(el.dataset.i18nPlaceholder);el.setAttribute('aria-label',tr(el.dataset.i18nPlaceholder))});if(!file)$('filename').textContent=tr('max');if(!token&&!initializing)status(fileStatus,tr('noToken'),true);else if(file)status(fileStatus,rows.length?tr('ready'):tr('none'),!rows.length);else if(token&&[dict.en.noToken,dict.zh.noToken].includes(fileStatus.textContent))status(fileStatus,'');updateSummary();renderList();updateCount()}
async function errorMessage(response){if(response.status===429||response.status===503)return tr('busyRetry');try{const x=await response.json();if(lang==='zh')return x.error||tr('failed');const msg=x.error||'';if(/PDF/.test(msg))return tr('pdfMissing');if(/200 MB|300 MB|文件为空/.test(msg))return tr('tooLarge');if(/JSON|压缩包|聊天数据|ZIP/.test(msg))return tr('badArchive');return tr('failed')}catch{return tr('failed')}}
async function sendFile(path, body, extra={}){
 const request=()=>fetch(path,{method:'POST',headers:{'X-Session-Token':token,'Content-Type':'application/octet-stream',...extra},body});
 let response=await request();
 // A service restart rotates the public token. A 403 is rejected before any
 // conversion starts, so it is safe to refresh the token and retry once.
 if(publicMode&&response.status===403){
  try{const r=await fetch('/api/session',{cache:'no-store'});if(r.ok){const session=await r.json();if(session.mode==='public'&&session.token){token=session.token;response=await request()}}}catch{}
 }
 return response;
}
async function choose(next){if(!next||busy)return;fileInput.value='';file=null;rows=[];summary=null;selected.clear();$('selection').classList.add('hidden');$('options').classList.add('hidden');$('filename').textContent=next.name;status(fileStatus,tr('reading'));status(exportStatus,'');setBusy(true);try{const res=await sendFile('/api/inspect',next);if(!res.ok)throw new Error(await errorMessage(res));summary=await res.json();file=next;rows=($('details').checked?summary.with_details:summary).conversations;selected=new Set(rows.map(r=>r.index));updateSummary();$('search').value='';renderList();$('selection').classList.remove('hidden');$('options').classList.remove('hidden');status(fileStatus,rows.length?tr('ready'):tr('none'),!rows.length);updateCount()}catch(err){status(fileStatus,err.message||tr('failed'),true)}finally{setBusy(false);updateCount()}}
function changeLanguage(value){lang=value==='zh'?'zh':'en';applyLanguage()}
$('language').addEventListener('change',e=>changeLanguage(e.target.value));
$('disclaimer-language').addEventListener('change',e=>changeLanguage(e.target.value));
$('disclaimer-continue').addEventListener('click',()=>$('disclaimer').close());
$('disclaimer-reopen').addEventListener('click',()=>$('disclaimer').showModal());fileInput.addEventListener('change',()=>choose(fileInput.files[0]));for(const name of ['dragenter','dragover'])drop.addEventListener(name,e=>{e.preventDefault();drop.classList.add('dragging')});for(const name of ['dragleave','drop'])drop.addEventListener(name,e=>{e.preventDefault();drop.classList.remove('dragging')});drop.addEventListener('drop',e=>choose(e.dataTransfer.files[0]));$('search').addEventListener('input',renderList);$('details').addEventListener('change',applyDetailsMode);$('select-all').addEventListener('change',e=>{selected=e.target.checked?new Set(rows.map(r=>r.index)):new Set();renderList();updateCount()});
$('export').addEventListener('click',async()=>{if(!file||!selected.size||busy)return;const format=document.querySelector('input[name="format"]:checked').value;setBusy(true);status(exportStatus,tr(format==='pdf'?'pdfWait':'mdWait'));try{const res=await sendFile('/api/export',file,{'X-Selected':JSON.stringify([...selected].sort((a,b)=>a-b)),'X-Format':format,'X-Details':$('details').checked?'1':'0','X-Language':lang});if(!res.ok)throw new Error(await errorMessage(res));const blob=await res.blob();const objectURL=URL.createObjectURL(blob);const a=document.createElement('a');a.href=objectURL;let name=res.headers.get('X-Output-Name');try{name=decodeURIComponent(name||'')}catch{name=''}a.download=name||`claude-export.${format}`;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(objectURL),60000);status(exportStatus,tr('done'))}catch(err){status(exportStatus,err.message||tr('failed'),true)}finally{setBusy(false)}});
$('stop').addEventListener('click',async()=>{try{await fetch('/api/shutdown',{method:'POST',headers:{'X-Session-Token':token}});document.body.replaceChildren(Object.assign(document.createElement('main'),{textContent:tr('stopped')}))}catch{status(exportStatus,tr('stopError'),true)}});
function setPublicMode(){
 publicMode=true;
 Object.assign(dict.en,{noToken:'The service is temporarily unavailable. Please reload the page.',disclaimerPrivacy:'Your file is uploaded over HTTPS to this server for conversion. Only upload sensitive chats or Memory if you trust this service.',eyebrow:'ONLINE EXPORTER',subtitle:'Files are uploaded to this server for conversion.',local:'Processed on the server',max:'Uploaded to the server · 20 MB max',footer:'Your file is uploaded over HTTPS to this server for conversion. Only use a service you trust.'});
 Object.assign(dict.zh,{noToken:'服务暂时不可用，请刷新页面重试。',disclaimerPrivacy:'你选择的文件会通过 HTTPS 上传到本服务器进行转换。聊天和 Memory 可能包含敏感信息；请仅在信任本服务时上传。',eyebrow:'在线导出',subtitle:'文件将上传到此服务器进行转换。',local:'在服务器上处理',max:'文件将上传至服务器，最大 20 MB',footer:'文件将通过 HTTPS 上传到此服务器进行转换，请确认你信任本服务。'});
 $('stop').hidden=true;$('source-link').hidden=false;
}
async function initialize(){
 if(!['127.0.0.1','localhost','::1','[::1]'].includes(location.hostname)){setPublicMode();token='';}
 if(!token){
  fileInput.disabled=true;
  applyLanguage();
  try{
   const response=await fetch('/api/session',{cache:'no-store'});
   if(!response.ok)throw new Error('session');
   const session=await response.json();
   if(session.mode!=='public'||!session.token)throw new Error('session');
   token=session.token;setPublicMode();
  }catch{}
 }
 if(token)fileInput.disabled=false;
 initializing=false;
 applyLanguage();
 $('disclaimer').showModal();
}
initialize();
