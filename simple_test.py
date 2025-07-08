import requests
from bs4 import BeautifulSoup

def test_simple():
    url = "https://metruyencv.com/truyen/ta-co-mot-toa-thanh-pho-ngay-tan-the/chuong-1"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status code: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Tìm nội dung chương
        content_element = soup.find('div', id='chapter-content')
        
        if content_element:
            print("✅ Tìm thấy chapter-content")
            content = content_element.get_text()
            print(f"Content length: {len(content)}")
            print(f"Content preview: {content[:200]}...")
        else:
            print("❌ Không tìm thấy chapter-content")
            
            # Thử tìm các element khác
            divs = soup.find_all('div')
            print(f"Tổng số div: {len(divs)}")
            
            for div in divs[:10]:
                if div.get('id'):
                    print(f"Div có id: {div.get('id')}")
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_simple()
