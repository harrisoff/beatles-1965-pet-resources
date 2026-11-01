from pathlib import Path
from urllib.request import Request, urlopen
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import json, hashlib

ROOT=Path(__file__).resolve().parent
sources=json.loads((ROOT/'sources.json').read_text())
items=[
 ('screenshot-tv-gag','https://static.next-episode.net/tv-shows-images/huge/the-beatles-1965.jpg','https://next-episode.net/the-beatles-1965','published series still; exact episode unconfirmed'),
 ('screenshot-performance','https://m.media-amazon.com/images/M/MV5BNWQyY2VlNTEtZDIzOS00OWNlLWFkOTYtZjRiNDA1YjgyNWQ2XkEyXkFqcGc%40._V1_.jpg','https://www.imdb.com/title/tt0058790/','series performance still; exact episode unconfirmed'),
 ('screenshot-help-magic','https://m.media-amazon.com/images/M/MV5BYzc5OTdiMjUtMjEwNC00NzRlLTg3ODktOThkMjE2NDJiYzVlXkEyXkFqcGc%40._V1_.jpg','https://www.imdb.com/title/tt1248409/','episode still: Help! / We Can Work It Out'),
 ('screenshot-penny-lane','https://m.media-amazon.com/images/M/MV5BYTAwODI0NjYtNGZhZS00MDFjLTliYTQtMjg2ZTU5NWUzMjdjXkEyXkFqcGc%40._V1_.jpg','https://www.imdb.com/title/tt0058790/','series still showing Penny Lane sign; episode attribution unconfirmed'),
 ('screenshot-head-portraits','https://m.media-amazon.com/images/M/MV5BYzRjM2I2MDQtNDNkNy00ZTI0LWJmM2EtMGQ0YmE2Y2MzY2Q0XkEyXkFqcGc%40._V1_.jpg','https://www.imdb.com/title/tt0058790/','published series portrait frame; exact episode unconfirmed'),
 ('screenshot-thoughtful-lineup','https://images.squarespace-cdn.com/content/v1/5fbc4a62c2150e62cfcb09aa/1758481702697-V4H5G96BEDI943CE2MFY/maxresdefault%2B%2841%29.jpg?format=1500w','https://www.cultureslate.com/editorials/the-beatles-animated-series-retrospective','published series frame; exact episode unconfirmed'),
 ('screenshot-raised-arms','https://images.squarespace-cdn.com/content/v1/5fbc4a62c2150e62cfcb09aa/917ee248-fe94-4cbe-861d-353fbe698f2c/sddefault.png','https://www.cultureslate.com/editorials/the-beatles-animated-series-retrospective','published series frame; exact episode unconfirmed'),
]
discovery=json.loads((ROOT/'source-discovery.json').read_text())
screenpage=next(d for d in discovery if d['key']=='screens')
for a in screenpage['images']:
    if '/01pics/beatles' in a['src']:
        items.append(('screenshot-archive-'+a['src'].rsplit('/',1)[1].split('.')[0],a['src'],screenpage['page'],'low-resolution series still; archival reference only'))

def download(x):
    ident,url,page,kind=x
    a={'id':ident,'url':url,'page':page,'kind':kind,'characters':['John','Paul','George','Ringo']}
    try:
        with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=25) as r: data=r.read()
        ext='.png' if data.startswith(b'\x89PNG') else '.jpg'
        file=ROOT/'originals'/(ident+ext);file.write_bytes(data)
        with Image.open(file) as im:a.update(width=im.width,height=im.height,format=im.format)
        a.update(file=str(file.relative_to(ROOT)).replace('\\','/'),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    except Exception as e:a['error']=str(e)
    return a
added=list(ThreadPoolExecutor(max_workers=6).map(download,items))
sources+=added
(ROOT/'sources.json').write_text(json.dumps(sources,indent=2),encoding='utf-8')
for a in added:print(a['id'],a.get('width'),a.get('height'),a.get('error','OK'))
