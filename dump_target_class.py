from androguard.misc import AnalyzeAPK
from loguru import logger
logger.remove()

APK=r'C:\Dev\MTC_Download\MTC.apk'
a,d,dx=AnalyzeAPK(APK)
TARGET='Lcom/example/novelfeverx/DownloadAllActivity$4;'
print('search class',TARGET)
for ca in dx.get_classes():
    if ca.name==TARGET:
        print('FOUND CLASS',ca.name)
        methods=ca.get_methods()
        print('method count',len(methods))
        for ma in methods:
            print('METHOD_ANALYSIS',ma)
            try:
                m=ma.get_method()
            except Exception:
                m=getattr(ma,'method',None)
            print('  method_obj',m)
            if m is not None:
                try:
                    print('  name',m.get_name(),'desc',m.get_descriptor())
                except Exception as e:
                    print('  name_err',e)
                try:
                    code=m.get_code()
                    if code:
                        bc=code.get_bc()
                        print('  insns:')
                        for ins in bc.get_instructions():
                            print('   ',hex(ins.get_start_idx()),ins.get_name(),ins.get_output())
                    else:
                        print('  no code')
                except Exception as e:
                    print('  dump_err',e)
