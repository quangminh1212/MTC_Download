src = open('brute_key4.py','r',encoding='utf-8').read()

old_line = next(l for l in src.splitlines() if "LIBAPP = r'" in l)

flutter_path = r'C:\Dev\MTC_Download\libflutter_extracted\libflutter.so'
bak_path     = r'C:\Dev\MTC_Download\libflutter_extracted\libapp.so.bak'

f = src.replace(old_line, f"LIBAPP = r'{flutter_path}'")
b = src.replace(old_line, f"LIBAPP = r'{bak_path}'")

open('brute_flutter.py','w',encoding='utf-8').write(f)
open('brute_bak.py','w',encoding='utf-8').write(b)

print('OK')
for name, script in [('flutter', f), ('bak', b)]:
    line = next(l for l in script.splitlines() if 'LIBAPP' in l)
    print(f'  {name}: {line.strip()}')
