"""Extract unretouched reference frames from a documented public episode copy."""
from pathlib import Path
from urllib.request import urlopen,Request
from urllib.parse import quote
import argparse,json,subprocess,sys

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('mode',choices=['download','extract'])
args=parser.parse_args()
cache=ROOT/'source-videos';cache.mkdir(exist_ok=True)
identifier='the-beatles-cartoon_2023'
filename="The Beatles S01E01 - A Hard Day's Night I Want To Hold Your Hand.mp4"
url='https://archive.org/download/'+identifier+'/'+quote(filename)
video=cache/'s01e01.mp4'
if args.mode=='download':
    request=Request(url,headers={'User-Agent':'Mozilla/5.0'})
    with urlopen(request,timeout=90) as response,video.open('wb') as out:
        while chunk:=response.read(1024*1024):out.write(chunk)
    (cache/'episode.json').write_text(json.dumps({'identifier':identifier,'filename':filename,'download_url':url,'page':'https://archive.org/details/'+identifier,'local_file':str(video.relative_to(ROOT))},indent=2),encoding='utf-8')
    print(json.dumps({'downloaded_bytes':video.stat().st_size,'file':str(video)}))
else:
    sys.path.insert(0,str(ROOT/'.tools'))
    import imageio_ffmpeg
    output=ROOT/'frame-candidates';output.mkdir(exist_ok=True)
    # Select decoded original frames and record their actual presentation timestamps.
    cmd=[imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','info','-i',str(video),'-vf',r'select=isnan(prev_selected_t)+gte(t-prev_selected_t\,8),showinfo','-fps_mode','vfr','-start_number','0',str(output/'s01e01-%03d.png')]
    result=subprocess.run(cmd,check=True,capture_output=True,text=True)
    import re
    times=[float(t) for t in re.findall(r'\bn:\s*\d+\s+pts:\s*\d+\s+pts_time:([\d.]+)',result.stderr)]
    candidates=[{'file':f's01e01-{i:03d}.png','seconds':t} for i,t in enumerate(times)]
    (output/'timestamps.json').write_text(json.dumps(candidates,indent=2),encoding='utf-8')
    print('Extracted',len(list(output.glob('s01e01-*.png'))),'candidate frames at eight-second intervals.')
