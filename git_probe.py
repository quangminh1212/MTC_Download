import subprocess, os, json
repo=r'C:\Dev\MTC'
cmd=['git','status','--porcelain=v1','-uall','--']
r=subprocess.run(cmd,cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
print('return',r.returncode)
print('stdout bytes',len(r.stdout))
print(r.stdout[:500].decode('utf-8','replace'))
print('stderr',r.stderr.decode('utf-8','replace'))
