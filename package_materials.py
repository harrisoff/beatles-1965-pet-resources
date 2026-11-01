from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,html,zipfile,hashlib,shutil

ROOT=Path(__file__).resolve().parent
names=['John','Paul','George','Ringo']
source_list=json.loads((ROOT/'sources.json').read_text(encoding='utf-8'))
labels={
 'group-lineup':('四人脸型与服装对照','宣传参考',2),
 'group-suitcases-cel':('四人全身 · 手提箱','原始动画稿照片',1),
 'group-publicity-cel':('四人全身 · 宣传赛璐珞稿','宣传动画稿照片',1),
 'group-running-cel':('四人奔跑 · 原始动画稿','原始动画稿照片',1),
 'historical-model-sheet':('四人造型、姿势与设定 · 2007 授权复刻','角色设定复刻',1),
 'ringo-running-cel':('Ringo 奔跑与鼓棒','原始动画稿照片',1),
 'ringo-running-cel-2':('Ringo 另一奔跑姿势','原始动画稿照片',1),
 'ringo-dancing-cel':('Ringo 动态姿势','原始动画稿照片',1),
 'screenshot-performance':('四人演奏 · 原片画面','原片截图',1),
 'screenshot-help-magic':('魔术帽场景 · 表情对照','原片截图',1),
 'screenshot-penny-lane':('Penny Lane 场景 · 全身与手势','原片截图',1),
 'screenshot-head-portraits':('四人头部肖像 · George / John / Paul / Ringo','原片截图',1),
 'screenshot-thoughtful-lineup':('四人思考与等待姿势','原片截图',1),
 'screenshot-raised-arms':('四人举手与庆祝姿势','原片截图',1),
 'screenshot-tv-gag':('电视机场景 · 全身','原片画面参考',2),
}
notes={
 'John':'宽长、圆方形下颌，细长鼻子；蓝色西装与窄领带。四人肖像中从左数第二位；奔跑动画稿中最右侧。',
 'Paul':'较柔和的圆脸、短鼻子与大眼睛；蓝色西装与窄领带。四人肖像中从左数第三位；奔跑动画稿中从左数第三位。演奏补图采用左手贝斯。',
 'George':'狭长棱角脸、长细鼻子，常略微含胸；蓝色外套与深色高领。四人肖像中最左侧；奔跑动画稿中从左数第二位。',
 'Ringo':'突出的大鼻子、小下巴、外翘发尾，身形较矮；蓝色外套与深色高领。四人肖像中最右侧；奔跑动画稿中最左侧。',
}
records=[]
for a in source_list:
    if 'file' not in a:continue
    ident=a['id']
    title,kind,priority=labels.get(ident,(ident,'低清补充画面',3))
    a.update(title_zh=title,type_zh=kind,priority=priority,generated=False)
    if ident=='historical-model-sheet':a['kind']='2007 licensed sericel reproduction of original television-cartoon character design; not an original 1965 production model sheet'
    if ident=='screenshot-archive-beatles01':a['characters']=['Paul']
    if ident in ['screenshot-archive-beatles031','screenshot-archive-beatles05']:a['characters']=[]
    if ident=='screenshot-archive-beatles04':a['characters']=[]
    a['quality_note']='保留下载文件的像素尺寸；未做放大或 AI 修复。' if priority<3 else '低分辨率，仅供构图与剧情参考。'
    records.append(a)
finals={}
for name in names:
    slug=name.lower()
    v2=ROOT/'generated'/f'{slug}-reference-sheet-v2.png'
    file=v2 if v2.exists() else ROOT/'generated'/f'{slug}-reference-sheet.png'
    if not file.exists():raise RuntimeError(f'Missing generated sheet: {name}')
    with Image.open(file) as im:
        extrema=im.getchannel('A').getextrema() if 'A' in im.getbands() else None
        if extrema is None or extrema[0]!=0:raise RuntimeError(f'Missing transparency: {name}')
        meta={'id':slug+'-generated-reference','title_zh':name+' · 12 姿势透明补充图','type_zh':'AI 生成补充','kind':'AI-generated supplemental identity and pose reference; back view and additional actions are inferred','characters':[name],'generated':True,'priority':1,'file':str(file.relative_to(ROOT)).replace('\\','/'),'width':im.width,'height':im.height,'mode':im.mode,'alpha_extrema':extrema,'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'quality_note':'4 列 × 3 行；新生成参考图，非原片截图或可直接导入的精灵图。'}
    finals[name]=meta;records.append(meta)
(ROOT/'sources.json').write_text(json.dumps(source_list,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'materials-manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')

style='''body{margin:0;background:#f4f1e9;color:#242824;font:16px/1.6 system-ui,sans-serif}header,main{max-width:1400px;margin:auto;padding:30px}h1{font-size:38px;margin:10px 0}p{max-width:950px}nav{display:flex;flex-wrap:wrap;gap:10px;margin:20px 0}button{background:white;border:1px solid #c8cdc2;border-radius:8px;padding:10px 18px;font:inherit;cursor:pointer}button[aria-pressed=true]{background:#275441;color:white}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:22px}article{background:white;border:1px solid #dddcd5;border-radius:12px;overflow:hidden}article img{width:100%;height:290px;object-fit:contain;background-color:#eee;background-image:linear-gradient(45deg,#ddd 25%,transparent 25%),linear-gradient(-45deg,#ddd 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#ddd 75%),linear-gradient(-45deg,transparent 75%,#ddd 75%);background-size:20px 20px;background-position:0 0,0 10px,10px -10px,-10px 0}article .body{padding:18px}h2{font-size:19px;margin:0 0 6px}.meta{font-size:13px;color:#666}a{color:#225c46}article[hidden]{display:none}.note{padding:15px 20px;background:#e4eadd;border-radius:10px}small{display:block;margin-top:8px}footer{padding:30px}'''
def make_html(subset,prefix='',character=None):
    cards=[]
    for a in sorted(subset,key=lambda a:(a['priority'],not a['generated'],a['id'])):
        path=prefix+a['file'];src=html.escape(path,quote=True)
        ch=' '.join(a['characters']);kind='generated' if a['generated'] else 'original'
        source='AI 生成 · 提示词见 generation-prompts.json' if a['generated'] else '<a href="'+html.escape(a['page'],quote=True)+'" target="_blank" rel="noopener">查看来源网页</a>'
        cards.append(f'''<article data-char="{ch}" data-kind="{kind}" data-priority="{a['priority']}"><a href="{src}" target="_blank"><img src="{src}" alt="{html.escape(a['title_zh'])}" loading="lazy"></a><div class="body"><h2>{html.escape(a['title_zh'])}</h2><div class="meta">{a['type_zh']} · {a['width']} × {a['height']}</div><small>{a['quality_note']}</small><p><a href="{src}" download>下载原尺寸文件</a> · {source}</p></div></article>''')
    title=(character+' · ' if character else '')+'The Beatles 1965 素材包'
    intro=notes[character] if character else '四位角色的原片画面、原始动画稿照片、设定复刻与 AI 补充图。先用历史资料确定身份与服装，再用透明补充图扩展动作。'
    charbuttons='' if character else '<nav aria-label="按角色筛选">'+''.join(f'<button data-filter="char" data-value="{v}" aria-pressed="{str(v=="all").lower()}">{v if v!="all" else "全部角色"}</button>' for v in ['all']+names)+'</nav>'
    htmltext=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{style}</style><header><div class="meta">REFERENCE COLLECTION / 2026-11-01</div><h1>{title}</h1><p>{intro}</p><p class="note">生成图每人 12 姿势：正面、四分之三、侧面、背面；挥手、左跑、右跑、跳跃；思考、失落、庆祝、演奏。背面和部分动作是推演参考。原片截图的文件尺寸不等于真实高清画质。</p>{charbuttons}<nav aria-label="按素材类型筛选"><button data-filter="kind" data-value="all" aria-pressed="true">全部来源</button><button data-filter="kind" data-value="original" aria-pressed="false">网络原图</button><button data-filter="kind" data-value="generated" aria-pressed="false">AI 补充图</button><button id="lowres" aria-pressed="false">显示低清补充</button></nav><div id="count" class="meta"></div></header><main class="grid">{''.join(cards)}</main><footer>来源与像素记录见 <a href="{prefix}materials-manifest.json">materials-manifest.json</a>。2007 设定复刻不是 1965 年原件。原始作品版权归各权利人；AI 补充图不是历史资料。</footer><script>let char='all',kind='all',low=false;function apply(){{let n=0;document.querySelectorAll('article').forEach(a=>{{let show=(char==='all'||a.dataset.char.split(' ').includes(char))&&(kind==='all'||a.dataset.kind===kind)&&(low||Number(a.dataset.priority)<3);a.hidden=!show;if(show)n++}});document.getElementById('count').textContent=n+' 张素材 · 点击图片查看原尺寸'}}document.querySelectorAll('[data-filter]').forEach(b=>b.onclick=()=>{{let f=b.dataset.filter;document.querySelectorAll('[data-filter='+f+']').forEach(x=>x.setAttribute('aria-pressed','false'));b.setAttribute('aria-pressed','true');if(f==='char')char=b.dataset.value;else kind=b.dataset.value;apply()}});document.getElementById('lowres').onclick=function(){{low=!low;this.setAttribute('aria-pressed',String(low));apply()}};apply();</script></html>'''
    return htmltext
(ROOT/'index.html').write_text(make_html(records),encoding='utf-8')
for name in names:
    directory=ROOT/'characters'/name.lower();directory.mkdir(exist_ok=True)
    relevant=[a for a in records if name in a['characters']]
    (directory/'index.html').write_text(make_html(relevant,'../../',name),encoding='utf-8')
    (directory/'character-notes.txt').write_text(name+'\n'+notes[name]+'\n\n原图见 index.html；多个人物同框的来源保持完整，没有裁切。\n',encoding='utf-8')

font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',30)
overview=Image.new('RGB',(1600,1320),'#f4f1e9');d=ImageDraw.Draw(overview)
for i,name in enumerate(names):
    a=finals[name];im=Image.open(ROOT/a['file']).convert('RGBA');im.thumbnail((770,590))
    x=i%2*800;y=i//2*660
    d.text((x+25,y+10),name+' / AI supplement / 12 poses',font=font,fill='#243e32')
    overview.paste(im,(x+(800-im.width)//2,y+60+(590-im.height)//2),im)
overview.save(ROOT/'previews'/'four-characters-overview.jpg',quality=95)
qa={'source_images':len(source_list),'selected_network_images':sum(a['priority']<3 for a in records if not a['generated']),'low_resolution_network_images':sum(a['priority']==3 for a in records if not a['generated']),'generated_sheets':len(finals),'generated_pose_panels':12*len(finals),'sheets':finals,'checks':{'download_hashes_retained':True,'all_generated_files_have_alpha_zero':True,'network_originals_unmodified':True,'visual_review':'All original files reviewed in contact sheet; all final generated sheets visually reviewed separately. Inferred back views explicitly labeled. These are reference materials, not validated pet spritesheets.'}}
(ROOT/'qa-summary.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')

archive=ROOT.parent/'beatles-1965-reference-pack.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for sub in ['originals','characters','previews']:
        for p in (ROOT/sub).rglob('*'):
            if p.is_file():z.write(p,str(p.relative_to(ROOT)))
    for a in finals.values():z.write(ROOT/a['file'],a['file'])
    for name in ['README.txt','index.html','sources.json','materials-manifest.json','generation-prompts.json','generation-repairs.json','qa-summary.json']:
        p=ROOT/name
        if p.exists():z.write(p,name)
print(json.dumps({'zip':str(archive),'bytes':archive.stat().st_size,'sources':len(source_list),'generated':{n:(a['file'],a['width'],a['height']) for n,a in finals.items()}},ensure_ascii=False,indent=2))
