from androguard.misc import AnalyzeAPK
from loguru import logger
logger.remove()

APK=r'C:\Dev\MTC_Download\MTC.apk'
needles=['decryptContent','https://android.lonoapp.net/api/chapters/','KEY_APP_KEY','"iv":"','","mac"','X-Signature','/setting?sign=','getChapterDetailsEncrypt']

a,d,dx=AnalyzeAPK(APK)
for needle in needles:
    print('\n===',needle,'===')
    found=False
    for s in dx.get_strings():
        val=s.get_value()
        if needle in val:
            found=True
            print('STRING',repr(val))
            xrefs=list(s.get_xref_from())
            print('xref_count',len(xrefs))
            for xr in xrefs[:60]:
                try:
                    m=xr[1]
                    print(' from',m.get_class_name(),m.get_name(),m.get_descriptor())
                except Exception as e:
                    print(' from?',xr,e)
    if not found:
        print('NO STRING')
