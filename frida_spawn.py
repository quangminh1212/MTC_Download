"""
Try frida spawn approach - spawn the app so frida-server is the parent.
Also try attaching to the existing process with various methods.
"""

import frida
import sys
import time

APP_ID = "com.novelfever.app.android"

HOOK_SCRIPT = r"""
'use strict';

function bytesToHex(arr) {
    var hex = '';
    for (var i = 0; i < arr.length; i++) {
        hex += ('0' + (arr[i] & 0xFF).toString(16)).slice(-2);
    }
    return hex;
}

function maybeString(arr) {
    try {
        var s = '';
        for (var i = 0; i < Math.min(arr.length, 64); i++) {
            var c = arr[i] & 0xFF;
            if (c >= 32 && c < 127) s += String.fromCharCode(c);
            else s += '.';
        }
        return s;
    } catch(e) { return '(error)'; }
}

Java.perform(function() {
    console.log("[*] Java.perform started");

    // Hook SecretKeySpec
    try {
        var SecretKeySpec = Java.use("javax.crypto.spec.SecretKeySpec");
        SecretKeySpec.$init.overload("[B", "java.lang.String").implementation = function(keyBytes, algo) {
            var hex = bytesToHex(keyBytes);
            var str = maybeString(keyBytes);
            console.log("\n[!!!] SecretKeySpec: algo=" + algo + " len=" + keyBytes.length);
            console.log("      hex: " + hex);
            console.log("      str: " + str);
            send({ type: 'key', algo: algo, hex: hex, len: keyBytes.length, str: str });
            return this.$init(keyBytes, algo);
        };
        console.log("[*] Hooked SecretKeySpec");
    } catch(e) { console.log("[!] SecretKeySpec: " + e); }

    // Hook Cipher init
    try {
        var Cipher = Java.use("javax.crypto.Cipher");
        Cipher.init.overload("int", "java.security.Key", 
            "java.security.spec.AlgorithmParameterSpec").implementation = function(op, key, spec) {
            var kb = key.getEncoded();
            var hex = bytesToHex(kb);
            console.log("\n[!!!] Cipher.init: op=" + op + " len=" + kb.length + " hex=" + hex);
            send({ type: 'cipher_init', op: op, hex: hex, len: kb.length });
            return this.init(op, key, spec);
        };
    } catch(e) { console.log("[!] Cipher.init3: " + e); }

    try {
        var Cipher2 = Java.use("javax.crypto.Cipher");
        Cipher2.init.overload("int", "java.security.Key").implementation = function(op, key) {
            var kb = key.getEncoded();
            var hex = bytesToHex(kb);
            console.log("\n[!!!] Cipher.init2: op=" + op + " len=" + kb.length + " hex=" + hex);
            send({ type: 'cipher_init2', op: op, hex: hex, len: kb.length });
            return this.init(op, key);
        };
    } catch(e) { console.log("[!] Cipher.init2: " + e); }

    console.log("[*] All hooks installed - waiting for chapter open...");
});
"""

def on_message(message, data):
    if message['type'] == 'send':
        payload = message['payload']
        print(f"\n{'!'*60}")
        print(f"[CAPTURED] {payload}")
        print('!'*60)
    elif message['type'] == 'error':
        print(f"[Frida Error] {message.get('stack', message)}")

def main():
    print("Connecting to device...")
    dm = frida.get_device_manager()
    device = dm.add_remote_device("127.0.0.1:27042")
    print(f"Connected: {device}")

    # Method 1: Try spawn (frida-server spawns as parent of new process)
    print(f"\nMethod 1: Spawning {APP_ID}...")
    try:
        pid = device.spawn([APP_ID])
        print(f"Spawned PID: {pid}")
        session = device.attach(pid)
        print(f"Attached to spawned PID {pid}")
        
        script = session.create_script(HOOK_SCRIPT)
        script.on('message', on_message)
        script.load()
        
        print("Resuming app...")
        device.resume(pid)
        
        print("\n" + "="*60)
        print("HOOK ACTIVE - wait for app to load, then open a chapter!")
        print("Ctrl+C to stop")
        print("="*60)
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopped.")
    except Exception as e:
        print(f"Spawn failed: {e}")
        
        # Method 2: Try current PID again
        print(f"\nMethod 2: Trying direct attach to existing process...")
        import subprocess
        result = subprocess.run(
            ['C:\\Program Files\\BlueStacks_nxt\\HD-Adb.exe', '-s', 'emulator-5554', 
             'shell', 'ps -ef | grep com.novelfever'],
            capture_output=True, text=True, timeout=10
        )
        print(f"Processes: {result.stdout}")
        
        # Try each PID
        for line in result.stdout.splitlines():
            if 'com.novelfever' in line and 'grep' not in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        pid = int(parts[1])
                        print(f"Trying PID {pid}...")
                        session = device.attach(pid)
                        print(f"SUCCESS! Attached to {pid}")
                        script = session.create_script(HOOK_SCRIPT)
                        script.on('message', on_message)
                        script.load()
                        print("Hook loaded! Open a chapter in the app.")
                        input("Press Enter to stop...")
                    except Exception as e2:
                        print(f"  Failed: {e2}")

if __name__ == "__main__":
    main()
