from androguard.misc import AnalyzeAPK
from loguru import logger
logger.remove()

APK=r'C:\Dev\MTC_Download\MTC.apk'
a,d,dx=AnalyzeAPK(APK)
TARGET='Lcom/example/novelfeverx/DownloadAllActivity$4;'
for ca in dx.get_classes():
    if ca.name!=TARGET:
        continue
    for ma in ca.get_methods():
        m=ma.get_method()
        if m.get_name()!='decryptContent':
            continue
        print('METHOD',m)
        code=m.get_code(); bc=code.get_bc()
        idx=0
        for ins in bc.get_instructions():
            print(f'{idx:03d}', ins.get_name(), '|', ins.get_output())
            idx+=1
