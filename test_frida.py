import frida
import sys

print("Frida version:", frida.__version__)

# Try ADB transport first
try:
    device = frida.get_device("emulator-5554")
    print("Connected via ADB:", device)
except Exception as e:
    print("ADB transport failed:", e)
    print("Trying TCP...")
    try:
        dm = frida.get_device_manager()
        device = dm.add_remote_device("127.0.0.1:27042")
        print("Connected via TCP:", device)
    except Exception as e2:
        print("TCP transport failed:", e2)
        sys.exit(1)

print("\n--- Processes ---")
try:
    processes = device.enumerate_processes()
    for p in processes:
        if "novel" in p.name.lower() or "lono" in p.name.lower() or "flutter" in p.name.lower():
            print(f"  *** PID={p.pid} name={p.name!r}")
    print(f"Total processes: {len(processes)}")
    # Print all to find the app
    for p in processes[:30]:
        print(f"  PID={p.pid} name={p.name!r}")
except Exception as e:
    print("Error listing processes:", e)

print("\n--- Applications ---")
try:
    apps = device.enumerate_applications()
    for a in apps:
        if "novel" in a.identifier.lower() or "lono" in a.identifier.lower():
            print(f"  *** {a.identifier!r} pid={a.pid} name={a.name!r}")
    print(f"Total apps: {len(apps)}")
except Exception as e:
    print("Error listing apps:", e)
