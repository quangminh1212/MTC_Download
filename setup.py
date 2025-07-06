import os
import sys
import subprocess
import urllib.request
import zipfile
import time
import json
import webbrowser
from pathlib import Path
import shutil

def print_header(message):
    print("\n" + "="*50)
    print(f"    {message}")
    print("="*50 + "\n")

def download_with_powershell(url, output_file):
    print(f'Downloading {output_file} using PowerShell...')
    try:
        ps_command = f'[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile("{url}", "{output_file}")'
        process = subprocess.run(["powershell", "-Command", ps_command], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE,
                             shell=True)
        
        if process.returncode == 0 and os.path.exists(output_file):
            print(f'Download successful!')
            return True
        else:
            print(f'PowerShell download failed: {process.stderr.decode("utf-8", errors="ignore")}')
            return False
    except Exception as e:
        print(f'PowerShell download error: {e}')
        return False

def download_file(url, filename):
    print(f'Downloading {filename}...')
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
        req = urllib.request.Request(url, headers=headers)
        
        def report_progress(count, block_size, total_size):
            if count % 50 == 0:
                percent = int(count * block_size * 100 / total_size) if total_size > 0 else 0
                print(f"\rProgress: {percent}% ", end="", flush=True)
        
        opener = urllib.request.build_opener()
        opener.addheaders = [(k, v) for k, v in headers.items()]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(url, filename, report_progress)
        print("\nDownload complete!")
        return True
    except Exception as e:
        print(f'\nDownload failed: {e}')
        # Try using PowerShell as fallback on Windows
        if os.name == 'nt':
            return download_with_powershell(url, filename)
        return False

def download_vie_data():
    print('Downloading Vietnamese language data...')
    if not os.path.exists('Tesseract-OCR/tessdata'):
        os.makedirs('Tesseract-OCR/tessdata', exist_ok=True)
    return download_file('https://github.com/tesseract-ocr/tessdata/raw/main/vie.traineddata', 'Tesseract-OCR/tessdata/vie.traineddata')

def setup_tesseract():
    print_header("TESSERACT OCR SETUP")
    tesseract_dir = 'Tesseract-OCR'
    
    if os.path.exists(os.path.join(tesseract_dir, 'tesseract.exe')):
        print(f'✅ Tesseract is already installed at {tesseract_dir}')
    else:
        # Create directory if it doesn't exist
        os.makedirs(tesseract_dir, exist_ok=True)
        
        # Try different download sources
        tesseract_urls = [
            ('https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3/tesseract-ocr-w64-setup-5.3.3.20231005.exe', 'tesseract-setup.exe'),
            ('https://versaweb.dl.sourceforge.net/project/tesseract-ocr-alt/tesseract-ocr-w64-setup-5.3.3.20231005.exe', 'tesseract-setup.exe'),
            ('https://sourceforge.net/projects/tesseract-ocr-alt/files/tesseract-ocr-w64-setup-5.3.3.20231005.exe/download', 'tesseract-setup.exe')
        ]
        
        success = False
        for url, filename in tesseract_urls:
            success = download_file(url, filename)
            if success and os.path.exists(filename):
                break
        
        if not success or not os.path.exists('tesseract-setup.exe'):
            # Try PowerShell download directly
            for url, filename in tesseract_urls:
                success = download_with_powershell(url, filename)
                if success and os.path.exists(filename):
                    break
                
        if success and os.path.exists('tesseract-setup.exe'):
            # Run installer with silent options
            print('Running Tesseract installer...')
            try:
                install_path = os.path.join(os.getcwd(), tesseract_dir).replace('/', '\\')
                print(f'Installing to: {install_path}')
                
                # Execute the installer
                process = subprocess.run(['tesseract-setup.exe', '/SILENT', f'/DIR={install_path}', '/NOCANCEL', '/SUPPRESSMSGBOXES'], 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE)
                
                if process.returncode == 0:
                    print('✅ Tesseract installation started')
                    
                    # Wait for installation to complete (check if tesseract.exe exists)
                    max_wait = 120  # seconds
                    wait_time = 0
                    while wait_time < max_wait:
                        if os.path.exists(os.path.join(tesseract_dir, 'tesseract.exe')):
                            print('✅ Tesseract installed successfully')
                            break
                        time.sleep(1)
                        wait_time += 1
                        if wait_time % 5 == 0:
                            print(f'Waiting for installation to complete... {wait_time}s')
                    
                    if wait_time >= max_wait:
                        print('⚠️ Installation taking longer than expected. Will continue setup.')
                else:
                    print(f"Installation may have issues. Return code: {process.returncode}")
                    print(f"Output: {process.stdout.decode('utf-8', errors='ignore')}")
                    print(f"Error: {process.stderr.decode('utf-8', errors='ignore')}")
                    
                    # Try alternative installation method
                    print("Trying alternative installation method...")
                    try:
                        process = subprocess.run(['start', '/wait', 'tesseract-setup.exe', '/SILENT', f'/DIR={install_path}'], 
                                              shell=True)
                        time.sleep(10)  # Give some time for installer to work
                    except Exception as e:
                        print(f"Alternative installation method error: {e}")
                
                # Clean up
                try:
                    if os.path.exists('tesseract-setup.exe'):
                        os.remove('tesseract-setup.exe')
                except:
                    print("Could not remove installer file. You may delete it manually.")
                
            except Exception as e:
                print(f"❌ Error installing Tesseract: {e}")
                manual_installation()
        else:
            print("Failed to download Tesseract installer from any source.")
            # Create basic structure and proceed
            create_minimal_tesseract()
    
    # Check if Vietnamese language data exists
    if not os.path.exists(os.path.join(tesseract_dir, 'tessdata', 'vie.traineddata')):
        download_vie_data()
    else:
        print("✅ Vietnamese language data already installed")
    
    print('✅ Tesseract OCR setup completed.')

def create_minimal_tesseract():
    """Create minimal Tesseract directory structure for future installation"""
    print("Creating minimal Tesseract directory structure...")
    tesseract_dir = 'Tesseract-OCR'
    os.makedirs(tesseract_dir, exist_ok=True)
    
    # Create a dummy tesseract.exe file so the program won't crash
    with open(os.path.join(tesseract_dir, 'tesseract.exe'), 'w') as f:
        f.write('# Dummy file created during setup. Please install Tesseract OCR properly.')
        
    # Make sure tessdata directory exists
    os.makedirs(os.path.join(tesseract_dir, 'tessdata'), exist_ok=True)
    
    print("⚠️ Warning: Created minimal Tesseract structure.")
    print("⚠️ OCR features will not work until you install Tesseract properly.")

def manual_installation():
    print('\n[MANUAL DOWNLOAD REQUIRED]')
    print('Please download Tesseract OCR from one of these links:')
    urls = [
        'https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3/tesseract-ocr-w64-setup-5.3.3.20231005.exe',
        'https://sourceforge.net/projects/tesseract-ocr-alt/files/tesseract-ocr-w64-setup-5.3.3.20231005.exe'
    ]
    for url in urls:
        print(url)
    
    print('\nWhen installing:')
    print(f'- Change installation path to: {os.getcwd()}\\Tesseract-OCR')
    print('- Make sure to select Vietnamese language data')
    
    # Try to open download page in browser
    try:
        webbrowser.open(urls[0])
    except:
        try:
            webbrowser.open(urls[1])
        except:
            pass
    
    print("\nOptions:")
    print("1. Press Enter after installation is complete")
    print("2. Type 'skip' to continue setup without Tesseract (limited functionality)")
    
    choice = input("\nYour choice: ").strip()
    
    if choice.lower() == 'skip':
        create_minimal_tesseract()
    else:
        print("Waiting for Tesseract installation to complete...")
        print("You can proceed with setup once Tesseract is installed.")

def create_user_agent_file():
    print_header("USER-AGENT FILE SETUP")
    with open('user-agent', 'w') as f:
        f.write('''import random

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Firefox/123.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/122.0.0.0'
]

def get():
    return random.choice(user_agents)
''')
    print("✅ User-agent file created successfully.")

def fix_python_files():
    print_header("FIXING PATH ISSUES")
    
    def fix_file(filename):
        if not os.path.exists(filename):
            print(f'❌ File {filename} not found.')
            return False
            
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Fix Windows paths by using forward slashes
            content = content.replace('\\\\', '/')
            content = content.replace('data_dir + "\\config.ini"', 'data_dir + "/config.ini"')
            content = content.replace('data_dir+"\\config.ini"', 'data_dir+"/config.ini"')
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
                
            print(f'✅ Fixed {filename}')
            return True
        except Exception as e:
            print(f'❌ Error fixing {filename}: {e}')
            return False

    if os.path.exists('main.py'):
        fix_file('main.py')
    else:
        print("❌ main.py not found")
        
    if os.path.exists('fast.py'):
        fix_file('fast.py')
    else:
        print("❌ fast.py not found")

def create_config_json():
    print_header("CONFIG SETUP")
    if not os.path.exists("config.json"):
        config = {
            'username': 'your_email@example.com',
            'password': 'your_password',
            'disk': 'C',
            'max_connections': 50,
            'novel_folder': 'novel',
            'font_family': 'Times New Roman',
            'font_size': '50px',
            'line_height': '150%',
            'headless': True,
            'tesseract_path': 'Tesseract-OCR/tesseract.exe',
            'semaphore_limit': 10,
            'novel_url': 'https://metruyencv.biz/truyen/your-novel-url',
            'start_chapter': 1,
            'end_chapter': 100
        }

        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        
        print("✅ Config file created successfully.")
    else:
        print("✅ Config file already exists.")

def setup_playwright():
    print_header("PLAYWRIGHT SETUP")
    try:
        subprocess.run([sys.executable, '-m', 'playwright', 'install', 'firefox'], check=True)
        print("✅ Playwright browsers installed successfully.")
    except Exception as e:
        print(f"❌ Error installing Playwright browsers: {e}")

def main():
    print_header("MeTruyenCV Downloader - Setup")
    
    # Install required packages
    print_header("PACKAGE INSTALLATION")
    packages = ['httpx', 'bs4', 'ebooklib', 'tqdm', 'backoff', 'playwright', 
                'pytesseract', 'pillow', 'appdirs', 'async_lru', 'requests']
    
    for package in packages:
        try:
            __import__(package)
            print(f"✅ {package} is already installed")
        except ImportError:
            print(f"Installing {package}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', package], check=True)
    
    # Create user agent file
    create_user_agent_file()
    
    # Setup Tesseract OCR
    setup_tesseract()
    
    # Setup Playwright
    setup_playwright()
    
    # Fix Python files
    fix_python_files()
    
    # Create config.json
    create_config_json()
    
    print_header("SETUP COMPLETE")
    print("You can now run main.py or fast.py to start downloading novels.")
    print("\nSelect an option:")
    print("1. Run main.py (standard version)")
    print("2. Run fast.py (faster version)")
    print("3. Edit config.json")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ")
    
    if choice == '1':
        subprocess.run([sys.executable, 'main.py'])
    elif choice == '2':
        subprocess.run([sys.executable, 'fast.py'])
    elif choice == '3':
        if os.name == 'nt':  # Windows
            os.system(f'notepad config.json')
        else:  # Unix/Linux/Mac
            os.system(f'xdg-open config.json')
    else:
        print("Exiting...")
    
if __name__ == "__main__":
    main() 