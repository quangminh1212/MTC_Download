import subprocess, pathlib, re, json, sys, os
root=pathlib.Path(r'C:\Dev\MTC_Continune')
out=subprocess.check_output(['git','-C',str(root),'status','--porcelain=v1','-z'])
entries=out.decode('utf-8','surrogateescape').split('\0')
folders=[]
for e in entries:
    if not e or len(e)<4:
        continue
    name=re.split(r'[\\/]', e[3:])[0].strip('"')
    if name and not name.startswith('.') and name not in folders:
        folders.append(name)
results=[]
for idx, name in enumerate(folders, 1):
    folder=root/name
    if not folder.exists():
        results.append({'folder':name,'status':'missing_folder'})
        continue
    try:
        subprocess.check_output(['git','-C',str(root),'add','--',name], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as ex:
        results.append({'folder':name,'status':'add_error','detail':ex.output.decode('utf-8','replace')[:500]})
        continue
    diff_out=subprocess.check_output(['git','-C',str(root),'diff','--cached','--name-only','--',name]).decode('utf-8','replace')
    if not diff_out.strip():
        results.append({'folder':name,'status':'nothing_staged'})
        continue
    commit=subprocess.run(['git','-C',str(root),'commit','-m',name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if commit.returncode!=0:
        subprocess.run(['git','-C',str(root),'reset','HEAD','--',name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        detail=(commit.stderr or commit.stdout).decode('utf-8','replace')[-500:]
        results.append({'folder':name,'status':'commit_failed','detail':detail})
        continue
    head=subprocess.check_output(['git','-C',str(root),'log','--format=%h','-1']).decode().strip()
    results.append({'folder':name,'status':'committed','commit':head})
    print(f'[{idx}/{len(folders)}] committed {head}', flush=True)
summary={
    'total':len(folders),
    'committed':sum(1 for r in results if r['status']=='committed'),
    'nothing_staged':sum(1 for r in results if r['status']=='nothing_staged'),
    'errors':[r for r in results if r['status'] not in {'committed','nothing_staged'}]
}
out_path=pathlib.Path(r'c:\Dev\MTC_Download\logs\bulk_folder_commit_results.json')
out_path.write_text(json.dumps({'summary':summary,'results':results}, ensure_ascii=False, indent=2), encoding='utf-8')
print('SUMMARY ' + json.dumps({'total':summary['total'],'committed':summary['committed'],'nothing_staged':summary['nothing_staged'],'error_count':len(summary['errors'])}, ensure_ascii=True))
if summary['errors']:
    sys.exit(2)
