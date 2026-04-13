import sys
sys.argv = ['brute_key4.py', r'C:\Dev\MTC_Download\libflutter_extracted\libflutter.so']
exec(open('brute_key4.py').read().replace(
    r"LIBAPP = r'C:\Dev\MTC_Download\libapp_extracted\libapp.so'",
    r"LIBAPP = sys.argv[1]"
))
