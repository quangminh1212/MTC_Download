from androguard.misc import AnalyzeAPK
from loguru import logger
logger.remove()

APK=r'C:\Dev\MTC_Download\MTC.apk'
a,d,dx=AnalyzeAPK(APK)
TARGET='Lcom/example/novelfeverx/DownloadAllActivity$4;'

for ca in dx.get_classes():
    if ca.name==TARGET:
        for ma in ca.get_methods():
            m=ma.get_method()
            print('\nMETHOD',m.get_name(),m.get_descriptor())
            code=m.get_code()
            if not code:
                print('  no code'); continue
            bc=code.get_bc()
            for ins in bc.get_instructions():
                opname=ins.get_name()
                out=ins.get_output()
                # focus on const-string/invoke/new-instance/return
                if ('const-string' in opname) or ('invoke-' in opname) or opname.startswith('new-') or opname.startswith('return') or opname.startswith('if-'):
                    print(' ',opname,'|',out)
