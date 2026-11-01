from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageFont
import json, math
ROOT=Path(__file__).resolve().parent
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
sources=json.loads((ROOT/'sources.json').read_text())
valid=[a for a in sources if a.get('file')]
W,H=480,370
sheet=Image.new('RGB',(W*3,H*math.ceil(len(valid)/3)), '#f2f0ea')
d=ImageDraw.Draw(sheet)
for i,a in enumerate(valid):
    im=Image.open(ROOT/a['file']).convert('RGB'); im.thumbnail((W-24,H-70))
    x=(i%3)*W;y=(i//3)*H
    sheet.paste(im,(x+(W-im.width)//2,y+8+(H-70-im.height)//2))
    d.text((x+12,y+H-56),a['id'],font=font,fill='#171717')
    d.text((x+12,y+H-30),f"{a['width']} x {a['height']} | original pixels",font=small,fill='#555555')
sheet.save(ROOT/'previews'/'originals-contact-sheet.jpg',quality=91)
print(ROOT/'previews'/'originals-contact-sheet.jpg')
