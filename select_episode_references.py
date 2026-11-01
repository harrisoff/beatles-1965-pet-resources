"""Preserve selected original episode frames and timestamped source records."""
from pathlib import Path
from PIL import Image
import json,shutil,hashlib
ROOT=Path(__file__).resolve().parent
selection={
16:(['Paul','John','Ringo'],'Paul、John 与 Ringo · 演奏与脸型对照'),
20:(['Paul'],'Paul · 四分之三脸型与短鼻'),
22:(['John'],'John · 正面偏转与宽下颌'),
23:(['John'],'John · 右向四分之三视角'),
31:(['John'],'John · 左向四分之三视角'),
44:(['Paul'],'Paul · 正面演奏特写'),
55:(['Paul'],'Paul · 全身与手势'),
56:(['Paul'],'Paul · 正面五官比例'),
57:(['Ringo'],'Ringo · 左向四分之三特写'),
67:(['Ringo'],'Ringo · 右向演奏与鼻子轮廓'),
69:(['Paul','John','George'],'Paul、John、George · 三人演奏对照'),
77:(['Paul'],'Paul · 四分之三特写与手势'),
78:(['Paul'],'Paul · 正面说话表情'),
82:(['Paul'],'Paul · 另一四分之三视角'),
93:(['George'],'George · 左向四分之三与长脸'),
97:(['George'],'George · 左向说话与演奏'),
108:(['John'],'John · 正面脸部大特写'),
109:(['John','Paul'],'John 与 Paul · 正面和四分之三对照'),
114:(['Ringo'],'Ringo · 正面偏转与水滴形大鼻子'),
116:(['Ringo','George'],'Ringo 与 George · 相向侧脸对照'),
117:(['George'],'George · 左向侧面全身'),
120:(['Paul'],'Paul · 潜水头盔内四分之三脸型'),
123:(['John'],'John · 潜水头盔内右向脸型'),
124:(['George'],'George · 俯视侧脸局部'),
128:(['George','John'],'George 与 John · 四分之三轮廓对照'),
130:(['Ringo'],'Ringo · 正面脸部特写'),
135:(['Ringo'],'Ringo · 左向纯侧面'),
137:(['Ringo'],'Ringo · 右向纯侧面'),
}
times=json.loads((ROOT/'frame-candidates'/'timestamps.json').read_text())
episode=json.loads((ROOT/'source-videos'/'episode.json').read_text())
sources=json.loads((ROOT/'sources.json').read_text(encoding='utf-8'))
sources=[a for a in sources if not a['id'].startswith('episode-s01e01-')]
for i,(characters,title) in selection.items():
    a=times[i];source=ROOT/'frame-candidates'/a['file'];dest=ROOT/'originals'/a['file']
    shutil.copyfile(source,dest)
    with Image.open(dest) as im:width,height=im.size
    t=a['seconds'];stamp=f'{int(t)//60:02d}:{t%60:06.3f}'
    sources.append({'id':f'episode-s01e01-{i:03d}','url':episode['download_url'],'page':episode['page'],'kind':'Unretouched decoded original episode frame; no resizing, repainting or AI enhancement','characters':characters,'width':width,'height':height,'format':'PNG','file':'originals/'+dest.name,'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'title_zh':title+' · '+stamp,'type_zh':'原片逐帧截图','priority':1,'generated':False,'episode':'S01E01: A Hard Day\'s Night / I Want To Hold Your Hand','timestamp_seconds':t,'timestamp_display':stamp,'source_filename':episode['filename'],'quality_note':'保留640×478解码画面；片源时间点 '+stamp+'，未放大、锐化或重绘。视角为目测分类，非精确相机测量。'})
(ROOT/'sources.json').write_text(json.dumps(sources,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('Added',len(selection),'original episode stills. Total sources:',len(sources))
