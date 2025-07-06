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

def download_file(url, filename):
    print(f'Downloading {filename}...')
    try:
        def report_progress(count, block_size, total_size):
            if count % 50 == 0:
                percent = int(count * block_size * 100 / total_size) if total_size > 0 else 0
                print(f"\rProgress: {percent}% ", end="", flush=True)
        
        urllib.request.urlretrieve(url, filename, report_progress)
        print("\nDownload complete!")
        return True
    except Exception as e:
        print(f'\nDownload failed: {e}')
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
        
        # Try to download Tesseract portable version
        success = download_file('https://github.com/nguyentd010/tesseract-portable/releases/download/v1.0.0/tesseract-portable.zip', 'tesseract-portable.zip')
        
        if success and os.path.exists('tesseract-portable.zip'):
            # Extract zip file
            print('Extracting Tesseract...')
            try:
                with zipfile.ZipFile('tesseract-portable.zip', 'r') as zip_ref:
                    zip_ref.extractall(tesseract_dir)
                
                # Clean up
                os.remove('tesseract-portable.zip')
                print('✅ Tesseract extracted successfully')
            except Exception as e:
                print(f"❌ Error extracting Tesseract: {e}")
                manual_installation()
        else:
            manual_installation()
    
    # Check if Vietnamese language data exists
    if not os.path.exists(os.path.join(tesseract_dir, 'tessdata', 'vie.traineddata')):
        download_vie_data()
    else:
        print("✅ Vietnamese language data already installed")
    
    print('✅ Tesseract OCR setup completed.')

def manual_installation():
    print('\n[MANUAL DOWNLOAD REQUIRED]')
    print('Please download Tesseract OCR from:')
    url = 'https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3/tesseract-ocr-w64-setup-v5.3.3.20231005.exe'
    print(url)
    print('\nWhen installing:')
    print(f'- Change installation path to: {os.getcwd()}\\Tesseract-OCR')
    print('- Make sure to select Vietnamese language data')
    
    # Try to open download page in browser
    try:
        webbrowser.open(url)
    except:
        pass
    
    input('\nPress Enter after installation is complete...')

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
            'novel_url': 'https://metruyencv.info/truyen/your-novel-url',
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