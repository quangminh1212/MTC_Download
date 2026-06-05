import os, subprocess, sys
cmd = [sys.executable, 'download_top5_bookmarks_to_mtc.py', '370', '0.0', '24', '3']
raise SystemExit(subprocess.call(cmd, cwd=r'C:\Dev\MTC_Download', env=os.environ.copy()))

