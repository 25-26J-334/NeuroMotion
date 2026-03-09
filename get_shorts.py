import urllib.request
import re
import sys

def get_short_id(query):
    req = urllib.request.Request('https://www.youtube.com/results?search_query=' + query.replace(' ', '+'), headers={'User-Agent': 'Mozilla/5.0'})
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
        vids = re.findall(r'\"videoId\":\"([a-zA-Z0-9_-]{11})\"', html)
        for vid in vids[1:6]:
            print(f"{query}: {vid}")
            return
    except Exception as e:
        print(e)
        
get_short_id('squat form shorts')
get_short_id('squat mistakes shorts')
get_short_id('pushup perfect form shorts')
get_short_id('pushup mistakes shorts')
get_short_id('jumping jacks form shorts')
get_short_id('jumping jacks mistakes shorts')
