from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,math
ROOT=Path(__file__).resolve().parent
data=json.loads((ROOT/'frame-candidates'/'timestamps.json').read_text())
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
for start in range(0,len(data),30):
    batch=data[start:start+30]
    sheet=Image.new('RGB',(1600,6*270),'#edeae4');d=ImageDraw.Draw(sheet)
    for k,a in enumerate(batch):
        im=Image.open(ROOT/'frame-candidates'/a['file']).convert('RGB');im.thumbnail((310,233))
        x=k%5*320;y=k//5*270
        sheet.paste(im,(x+(320-im.width)//2,y+4))
        t=a['seconds'];d.text((x+6,y+240),f"{start+k:03d} | {int(t)//60:02d}:{t%60:05.2f}",font=font,fill='#101010')
    file=ROOT/'frame-candidates'/f'contact-{start//30:02d}.jpg';sheet.save(file,quality=94)
    print(file.name)
