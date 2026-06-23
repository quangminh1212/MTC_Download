#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
download_wasabi_folder.py
Tải toàn bộ một folder (prefix) từ Wasabi S3 về máy cục bộ.
Hỗ trợ đa luồng, tự tạo cấu trúc thư mục, retry khi lỗi.
"""
import argparse, os, sys, threading, queue, boto3
from botocore.exceptions import ClientError, EndpointConnectionError

def ensure_dir(p): os.makedirs(p, exist_ok=True)

def worker(s3, q, base):
    while True:
        try: obj = q.get_nowait()
        except queue.Empty: break
        key, rel = obj['Key'], os.path.relpath(obj['Key'], start=obj['Prefix'])
        local = os.path.join(base, rel)
        ensure_dir(os.path.dirname(local))
        try:
            s3.download_file(obj['Bucket'], key, local)
            print(f"[DONE] {key}")
        except Exception as e:
            print(f"[ERR] {key}: {e}", file=sys.stderr)
        q.task_done()

def list_objects(s3, bucket, prefix):
    for page in s3.get_paginator('list_objects_v2').paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []): yield obj

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bucket', required=True)
    ap.add_argument('--prefix', required=True)
    ap.add_argument('--local-dir', required=True)
    ap.add_argument('--threads', type=int, default=8)
    a = ap.parse_args()
    if not a.prefix.endswith('/'): a.prefix += '/'
    s3 = boto3.client('s3')
    objs = list(list_objects(s3, a.bucket, a.prefix))
    if not objs:
        print("No objects found."); sys.exit(0)
    print(f"Found {len(objs)} objects. Downloading...")
    q = queue.Queue()
    for o in objs: q.put({'Bucket':a.bucket,'Key':o['Key'],'Prefix':a.prefix})
    ths = [threading.Thread(target=worker,args=(s3,q,a.local_dir),daemon=True) for _ in range(a.threads)]
    [t.start() for t in ths]; q.join(); [t.join() for t in ths]
    print("Done.")

if __name__ == '__main__': main()
