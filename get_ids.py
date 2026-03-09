import urllib.request
import re

def get_vid(query):
    req = urllib.request.Request('https://www.youtube.com/results?search_query=' + query.replace(' ','+'), headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req).read().decode('utf-8')
    vids = re.findall(r'\"videoId\":\"([a-zA-Z0-9_-]{11})\"', html)
    return vids[1] if len(vids) > 1 else vids[0]

print("Squat Correct:", get_vid('squat form short'))
print("Squat Mistake:", get_vid('squat mistakes short'))
print("Pushup Correct:", get_vid('pushup form short'))
print("Pushup Mistake:", get_vid('pushup mistakes short'))
print("Jump Correct:", get_vid('jumping jacks form short'))
print("Jump Mistake:", get_vid('jumping jacks mistakes short'))
