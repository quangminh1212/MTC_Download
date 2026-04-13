try:
    import frida
    print('frida version:', frida.__version__)
except ImportError:
    print('frida NOT installed')

# Also check mitmproxy capture size
import os
if os.path.exists('mitm_capture.bin'):
    print('mitm_capture.bin size:', os.path.getsize('mitm_capture.bin'), 'bytes')
else:
    print('mitm_capture.bin not found')
