#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests, json, sys, time

email=sys.argv[1]
password=sys.argv[2]
base='https://android.lonoapp.net/api'
s=requests.Session(); s.headers.update({'User-Agent':'MTC/Android','Accept':'application/json','Content-Type':'application/json'})
login=s.post(base+'/auth/login', json={'email':email,'password':password,'device_name':'OpenClaw Windows'}, timeout=30)
print('login',login.status_code)
print(login.text[:500])
login.raise_for_status()
j=login.json()
token=j['data']['token']
s.headers.update({'Authorization':f'Bearer {token}'})

param_cases=[None,{}, {'limit':5}, {'page':1}, {'page':1,'limit':5}, {'page':1,'limit':20}, {'book_id':143452}, {'filter[book_id]':143452}]
for p in param_cases:
    time.sleep(1)
    r=s.get(base+'/bookmarks', params=p, timeout=30)
    print('\nPARAMS',p,'STATUS',r.status_code,'URL',r.url)
    txt=r.text
    print(txt[:1200].replace('\n',' '))
    try:
        jj=r.json();
        d=jj.get('data') if isinstance(jj,dict) else None
        print('data_type',type(d).__name__,'data_len',len(d) if isinstance(d,list) else 'na','keys',list(jj.keys()) if isinstance(jj,dict) else 'na')
    except Exception as e:
        print('json_err',e)
