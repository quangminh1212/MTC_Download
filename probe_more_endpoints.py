import requests, json
cid=13071362
bases=['https://android.lonoapp.net/api','https://api.lonoapp.net/api']
paths=[f'/chapters/{cid}', '/chapter_detail', f'/chapter_detail/{cid}', '/contents', f'/contents/{cid}']
paramsets=[{}, {'id':cid}, {'chapter_id':cid}, {'filter[chapter_id]':cid}, {'include':'user,chapter'}, {'id':cid,'include':'user,chapter'}]
s=requests.Session(); s.headers.update({'User-Agent':'MTC/Android','Accept':'application/json'})
for base in bases:
  for path in paths:
    for params in paramsets:
      if path.endswith(str(cid)) and params not in [{}, {'include':'user,chapter'}]: continue
      if path not in ['/chapter_detail','/contents'] and params not in [{}, {'include':'user,chapter'}]: continue
      try:
        r=s.get(base+path,params=params,timeout=15)
        txt=r.text[:250].replace('\n',' ')
        print(r.status_code, r.url, txt)
      except Exception as e: print('ERR',base,path,params,e)
