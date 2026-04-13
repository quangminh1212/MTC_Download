"""
Hook AES cipher in NovelFever app to capture the decryption key.
Attaches directly by PID to avoid enumeration (which crashes as non-root).
"""

import frida
import sys
import time

APP_PID = 13235   # com.novelfever.app.android - update if changed

# JavaScript hook - hooks Java AES and also native crypto functions
HOOK_SCRIPT = r"""
'use strict';

// Track if we found the key
var KEY_FOUND = false;

function bytesToHex(arr) {
    var hex = '';
    for (var i = 0; i < arr.length; i++) {
        hex += ('0' + (arr[i] & 0xFF).toString(16)).slice(-2);
    }
    return hex;
}

function toUtf8(arr) {
    try {
        return String.fromCharCode.apply(null, arr);
    } catch(e) { return '(non-utf8)'; }
}

// ===== JAVA LAYER HOOKS =====
Java.perform(function() {
    console.log("[*] Java.perform started");
    
    // Hook javax.crypto.Cipher - most common Java AES path
    try {
        var Cipher = Java.use("javax.crypto.Cipher");
        
        // Cipher.init(int, Key, AlgorithmParameterSpec)
        Cipher.init.overload("int", "java.security.Key",
            "java.security.spec.AlgorithmParameterSpec").implementation = function(opmode, key, params) {
            
            var keyBytes = key.getEncoded();
            var keyHex = bytesToHex(keyBytes);
            
            // Only report if key length is 16, 24, or 32 bytes (AES key sizes)
            if (keyBytes.length === 16 || keyBytes.length === 24 || keyBytes.length === 32) {
                if (!KEY_FOUND) {
                    KEY_FOUND = true;
                    send({
                        type: 'aes_key',
                        source: 'Cipher.init',
                        opmode: opmode,
                        key_hex: keyHex,
                        key_len: keyBytes.length,
                        key_str: toUtf8(keyBytes)
                    });
                    console.log("[!!!] AES KEY FOUND via Cipher.init:");
                    console.log("      opmode: " + opmode + " (2=decrypt)");
                    console.log("      key length: " + keyBytes.length + " bytes");
                    console.log("      key hex: " + keyHex);
                    console.log("      key str: " + toUtf8(keyBytes));
                }
            }
            return this.init(opmode, key, params);
        };
        console.log("[*] Hooked Cipher.init(int, Key, AlgorithmParameterSpec)");
    } catch(e) {
        console.log("[!] Failed to hook Cipher.init overload: " + e);
    }
    
    // Also hook Cipher.init with just Key (no IV parameter)
    try {
        var Cipher2 = Java.use("javax.crypto.Cipher");
        Cipher2.init.overload("int", "java.security.Key").implementation = function(opmode, key) {
            var keyBytes = key.getEncoded();
            if (keyBytes.length === 16 || keyBytes.length === 24 || keyBytes.length === 32) {
                send({
                    type: 'aes_key',
                    source: 'Cipher.init(2-arg)',
                    opmode: opmode,
                    key_hex: bytesToHex(keyBytes),
                    key_len: keyBytes.length
                });
                console.log("[!!!] AES KEY via Cipher.init(2-arg): " + bytesToHex(keyBytes));
            }
            return this.init(opmode, key);
        };
        console.log("[*] Hooked Cipher.init(int, Key)");
    } catch(e) { console.log("[!] Cipher.init(2-arg) failed: " + e); }
    
    // Hook SecretKeySpec creation
    try {
        var SecretKeySpec = Java.use("javax.crypto.spec.SecretKeySpec");
        SecretKeySpec.$init.overload("[B", "java.lang.String").implementation = function(keyBytes, algo) {
            var hex = bytesToHex(keyBytes);
            if (keyBytes.length === 16 || keyBytes.length === 24 || keyBytes.length === 32) {
                send({
                    type: 'secret_key_spec',
                    algo: algo,
                    key_hex: hex,
                    key_len: keyBytes.length
                });
                console.log("[!!!] SecretKeySpec created: algo=" + algo + " len=" + keyBytes.length);
                console.log("      hex: " + hex);
                console.log("      str: " + toUtf8(keyBytes));
            }
            return this.$init(keyBytes, algo);
        };
        console.log("[*] Hooked SecretKeySpec.$init");
    } catch(e) { console.log("[!] SecretKeySpec hook failed: " + e); }
    
    // Hook IvParameterSpec to capture IVs too
    try {
        var IvParameterSpec = Java.use("javax.crypto.spec.IvParameterSpec");
        IvParameterSpec.$init.overload("[B").implementation = function(iv) {
            send({
                type: 'iv_spec',
                iv_hex: bytesToHex(iv),
                iv_len: iv.length
            });
            console.log("[*] IvParameterSpec created: " + bytesToHex(iv));
            return this.$init(iv);
        };
        console.log("[*] Hooked IvParameterSpec.$init");
    } catch(e) { console.log("[!] IvParameterSpec hook failed: " + e); }
    
    console.log("[*] All Java hooks installed. Waiting for crypto calls...");
    console.log("[*] Open a chapter in the app now!");
});

// ===== NATIVE LAYER HOOKS =====
// Hook OpenSSL/native AES (in case Dart uses native crypto directly)
setTimeout(function() {
    try {
        var aes_cbc_encrypt = Module.getExportByName("libcrypto.so", "EVP_EncryptInit_ex");
        if (aes_cbc_encrypt) {
            Interceptor.attach(aes_cbc_encrypt, {
                onEnter: function(args) {
                    console.log("[*] EVP_EncryptInit_ex called");
                }
            });
            console.log("[*] Hooked EVP_EncryptInit_ex");
        }
    } catch(e) { }
    
    try {
        var aes_decrypt = Module.getExportByName("libcrypto.so", "EVP_DecryptInit_ex");
        if (aes_decrypt) {
            Interceptor.attach(aes_decrypt, {
                onEnter: function(args) {
                    // args[0] = ctx, args[1] = type, args[3] = key, args[4] = iv
                    console.log("[*] EVP_DecryptInit_ex called");
                    try {
                        var key = Memory.readByteArray(args[3], 32);
                        console.log("[!!!] Native AES key: " + hexdump(args[3], {length: 32, ansi: false}));
                        send({ type: 'native_aes', key: Array.from(new Uint8Array(key)) });
                    } catch(e) { }
                }
            });
            console.log("[*] Hooked EVP_DecryptInit_ex");
        }
    } catch(e) { }
}, 1000);
"""

def on_message(message, data):
    if message['type'] == 'send':
        payload = message['payload']
        print(f"\n{'='*60}")
        print(f"[INTERCEPTED] {payload.get('type', 'unknown')}")
        for k, v in payload.items():
            if k != 'type':
                print(f"  {k}: {v}")
        print('='*60)
    elif message['type'] == 'error':
        print(f"[Frida Error] {message['stack']}")
    else:
        print(f"[msg] {message}")

def main():
    print(f"Connecting to frida-server via TCP...")
    
    try:
        dm = frida.get_device_manager()
        device = dm.add_remote_device("127.0.0.1:27042")
        print(f"Connected: {device}")
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)
    
    print(f"Attaching to PID {APP_PID} (NovelFever app)...")
    try:
        session = device.attach(APP_PID)
        print(f"Attached successfully to PID {APP_PID}")
    except Exception as e:
        print(f"Attach failed: {e}")
        print("Tip: Try getting a fresh PID with: adb shell ps -ef | grep novelfever")
        sys.exit(1)
    
    print("Loading hook script...")
    script = session.create_script(HOOK_SCRIPT)
    script.on('message', on_message)
    script.load()
    
    print("\n" + "="*60)
    print("HOOK ACTIVE - Now open/scroll through chapters in the app!")
    print("The AES key will be printed when the app decrypts a chapter.")
    print("Press Ctrl+C to stop.")
    print("="*60 + "\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
    
    session.detach()

if __name__ == "__main__":
    main()
