from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urljoin
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor
import json, re, hashlib
from PIL import Image

ROOT = Path(__file__).resolve().parent
for folder in ['originals', 'source-pages', 'generated', 'characters', 'previews']:
    (ROOT / folder).mkdir(exist_ok=True)

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.images=[]; self.links=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='img': self.images.append(a)
        if tag=='a' and 'href' in a: self.links.append(a['href'])

PAGES = {
 'model': 'https://www.theglassonionbeatlesjournal.com/2019/04/beatles-cartoon-model-sheet.html',
 'screens': 'https://oldskool.cartoondatabank.com/B/beatles1965.htm',
 'episodes': 'https://www.thebeatlesonfilm.com/cartoons.html',
 'background': 'https://www.thebeatleshk.com/Cartoons/Background.html',
 'running': 'https://greganimationart.blogspot.com/2024/03/original-production-animation-cel-of_3.html',
 'publicity': 'https://greganimationart.blogspot.com/2024/03/original-modelpublicity-animation-cel-of.html',
}
def get(url):
    with urlopen(Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=30) as r:
        return r.read()
def page(item):
    key,url=item
    try:
        data=get(url); (ROOT/'source-pages'/f'{key}.html').write_bytes(data)
        p=Links(); p.feed(data.decode('utf-8',errors='replace'))
        out={'key':key,'page':url,'images':[{**a,'src':urljoin(url,a.get('src',''))} for a in p.images],
             'image_links':[urljoin(url,u) for u in p.links if re.search(r'\.(?:jpg|jpeg|png|gif)(?:\?|$)',u,re.I)]}
        return out
    except Exception as e: return {'key':key,'page':url,'error':str(e)}
discoveries=list(ThreadPoolExecutor(max_workers=6).map(page,PAGES.items()))
(ROOT/'source-discovery.json').write_text(json.dumps(discoveries,indent=2),encoding='utf-8')
assets=[
 {'id':'group-lineup','url':'https://televisionheaven.co.uk/img/containers/main/the_beatles_cartoon_series.jpg/0ca111083b88771a52466a08e5416aea/the_beatles_cartoon_series.jpg','page':'https://televisionheaven.co.uk/reviews/beatles-the-cartoon-series','kind':'published promotional still','characters':['John','Paul','George','Ringo']},
 {'id':'group-suitcases-cel','url':'https://static.wixstatic.com/media/139349_0bec576601ce4c8295ed01c8d86f6a3d~mv2.jpg','page':'https://www.untitledartgallery.com/post/original-production-animation-cel-of-john-lennon-paul-mccartney-beatles-ringo-star','kind':'production cel photographed on lithographic background','characters':['John','Paul','George','Ringo']},
 {'id':'group-publicity-cel','url':'https://static.wixstatic.com/media/139349_8e8e7d972f83463c9dbde210b020fe25~mv2.jpg','page':'https://www.untitledartgallery.com/post/original-modelpublicity-animation-cel-of-john-lennon-paul-mccartney-george-harrison-ringo-starr-beatles','kind':'model/publicity cel','characters':['John','Paul','George','Ringo']},
 {'id':'ringo-running-cel','url':'https://static.wixstatic.com/media/139349_5b7de2c5016745e9b7cfba6195049c4e~mv2.jpg','page':'https://www.untitledartgallery.com/post/original-production-animation-cel-of-ringo-star-from-the-beatles-1965-67-2','kind':'production cel photographed on lithographic background','characters':['Ringo']},
 {'id':'ringo-dancing-cel','url':'https://static.wixstatic.com/media/139349_dd5c7085faaf4d789459cc58eb4a02e2~mv2.jpg','page':'https://www.untitledartgallery.com/post/original-production-animation-cel-of-ringo-star-from-the-beatles-1965-67-4','kind':'production cel photographed on lithographic background','characters':['Ringo']},
 {'id':'ringo-running-cel-2','url':'https://static.wixstatic.com/media/139349_7246adcb60064d1a82eee8e9f1248a13~mv2.jpg','page':'https://www.untitledartgallery.com/post/original-production-animation-cel-of-ringo-star-from-the-beatles-1965-67','kind':'production cel photographed on lithographic background','characters':['Ringo']},
]
for d in discoveries:
    if d['key']=='model':
        links=[u for u in d.get('image_links',[]) if u.endswith('/lf.jpg')]
        if links: assets.append({'id':'historical-model-sheet','url':links[0],'page':d['page'],'kind':'reproduction of historical model sheet','characters':['John','Paul','George','Ringo']})
    if d['key']=='running':
        links=[u for u in d.get('image_links',[]) if 'blogspot' in u or 'googleusercontent' in u]
        if links: assets.append({'id':'group-running-cel','url':links[0],'page':d['page'],'kind':'production cel photographed on lithographic background','characters':['John','Paul','George','Ringo']})

def download(a):
    try:
        data=get(a['url']); ext='.png' if data.startswith(b'\x89PNG') else '.gif' if data.startswith(b'GIF8') else '.jpg'
        path=ROOT/'originals'/(a['id']+ext); path.write_bytes(data)
        with Image.open(path) as im: a.update(width=im.width,height=im.height,format=im.format)
        a.update(file=str(path.relative_to(ROOT)).replace('\\','/'),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    except Exception as e: a['error']=str(e)
    return a
assets=list(ThreadPoolExecutor(max_workers=6).map(download,assets))
(ROOT/'sources.json').write_text(json.dumps(assets,indent=2),encoding='utf-8')
print(json.dumps({'assets':assets,'pages':[{'key':d['key'],'images':len(d.get('images',[])),'links':len(d.get('image_links',[])),'error':d.get('error')} for d in discoveries]},indent=2))
