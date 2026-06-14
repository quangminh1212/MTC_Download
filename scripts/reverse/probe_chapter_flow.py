import json
import requests

BASE='https://android.lonoapp.net/api'
s=requests.Session(); s.headers.update({'User-Agent':'MTC/Android','Accept':'application/json'})
# get chapters for Siêu Dự Bị
chap=s.get(f'{BASE}/chapters',params={'filter[book_id]':105459,'page':1,'limit':1},timeout=20).json()['data'][0]
print('chapter list item:', json.dumps(chap,ensure_ascii=False,indent=2)[:1000])
cid=chap['id']
for url,params in [
    (f'{BASE}/chapters/{cid}',{}),
    (f'{BASE}/chapters/{cid}',{'include':'user,chapter'}),
    (f'{BASE}/chapter_detail',{'id':cid}),
    (f'{BASE}/chapter_detail/{cid}',{}),
]:
    try:
        r=s.get(url,params=params,timeout=20)
        print('\nURL',r.url,'status',r.status_code,'ctype',r.headers.get('content-type'))
        print(r.text[:1200])
    except Exception as e:
        print('ERR',url,params,e)
