#!/bin/bash

# MeTruyenCV Web Interface Setup Script for Linux/Mac
# Cài đặt tự động web interface

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                  MeTruyenCV Web Setup                        ║"
    echo "║              Cài đặt tự động web interface                  ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}🔍 $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

# Install Python on different systems
install_python() {
    local os=$(detect_os)
    
    case $os in
        "linux")
            if command_exists apt-get; then
                print_info "Cài đặt Python qua apt..."
                sudo apt-get update
                sudo apt-get install -y python3 python3-pip python3-venv
            elif command_exists yum; then
                print_info "Cài đặt Python qua yum..."
                sudo yum install -y python3 python3-pip
            elif command_exists dnf; then
                print_info "Cài đặt Python qua dnf..."
                sudo dnf install -y python3 python3-pip
            else
                print_error "Không thể tự động cài đặt Python. Vui lòng cài đặt thủ công."
                exit 1
            fi
            ;;
        "macos")
            if command_exists brew; then
                print_info "Cài đặt Python qua Homebrew..."
                brew install python3
            else
                print_error "Homebrew không được tìm thấy. Vui lòng cài đặt Homebrew hoặc Python thủ công."
                exit 1
            fi
            ;;
        *)
            print_error "OS không được hỗ trợ"
            exit 1
            ;;
    esac
}

# Main setup
main() {
    print_header
    
    # Check Python
    print_info "Kiểm tra Python..."
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_success "Python $PYTHON_VERSION đã được cài đặt"
        PYTHON_CMD="python3"
        PIP_CMD="pip3"
    elif command_exists python; then
        PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
        if [[ $PYTHON_VERSION == 3.* ]]; then
            print_success "Python $PYTHON_VERSION đã được cài đặt"
            PYTHON_CMD="python"
            PIP_CMD="pip"
        else
            print_error "Cần Python 3.x, hiện tại là Python $PYTHON_VERSION"
            exit 1
        fi
    else
        print_warning "Python không được tìm thấy, đang cài đặt..."
        install_python
        PYTHON_CMD="python3"
        PIP_CMD="pip3"
    fi
    
    # Check pip
    if ! command_exists $PIP_CMD; then
        print_info "Cài đặt pip..."
        curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
        $PYTHON_CMD get-pip.py
        rm get-pip.py
    fi
    
    # Create virtual environment
    print_info "Tạo virtual environment..."
    if [ -d "venv" ]; then
        print_warning "Virtual environment đã tồn tại, đang xóa..."
        rm -rf venv
    fi
    
    $PYTHON_CMD -m venv venv
    print_success "Virtual environment đã được tạo"
    
    # Activate virtual environment
    print_info "Kích hoạt virtual environment..."
    source venv/bin/activate
    
    # Upgrade pip
    print_info "Nâng cấp pip..."
    pip install --upgrade pip
    
    # Install main dependencies
    print_info "Cài đặt dependencies chính..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Dependencies chính đã được cài đặt"
    else
        print_warning "Không tìm thấy requirements.txt, cài đặt dependencies cơ bản..."
        pip install selenium beautifulsoup4 lxml httpx ebooklib configparser
    fi
    
    # Install web dependencies
    print_info "Cài đặt web dependencies..."
    if [ -f "requirements_web.txt" ]; then
        pip install -r requirements_web.txt
    else
        print_warning "Không tìm thấy requirements_web.txt, cài đặt dependencies cơ bản..."
        pip install Flask==3.0.0 Flask-SocketIO==5.3.6 eventlet==0.33.3
    fi
    print_success "Web dependencies đã được cài đặt"
    
    # Setup ChromeDriver
    print_info "Cài đặt ChromeDriver..."
    pip install webdriver-manager
    
    # Create config file
    print_info "Tạo file cấu hình..."
    if [ ! -f "config.txt" ]; then
        $PYTHON_CMD -c "from config_manager import ConfigManager; ConfigManager().create_default_config()" 2>/dev/null || print_warning "Không thể tạo config tự động"
        if [ -f "config.txt" ]; then
            print_success "File config.txt đã được tạo"
        fi
    else
        print_success "File config.txt đã tồn tại"
    fi
    
    # Create run script for Unix
    print_info "Tạo run script..."
    cat > run_web.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python app.py
EOF
    chmod +x run_web.sh
    print_success "Script run_web.sh đã được tạo"
    
    # Test installation
    print_info "Test cài đặt..."
    $PYTHON_CMD -c "import flask, flask_socketio, selenium, bs4; print('✅ Tất cả modules đã được cài đặt thành công')" 2>/dev/null || {
        print_error "Một số modules chưa được cài đặt đúng"
        exit 1
    }
    print_success "Test thành công!"
    
    # Deactivate virtual environment
    deactivate
    
    # Success message
    echo
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                    CÀI ĐẶT HOÀN TẤT!                        ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo
    print_success "Web interface đã được cài đặt thành công!"
    echo
    echo -e "${BLUE}📋 Cách sử dụng:${NC}"
    echo "   1. Chạy: ./run_web.sh"
    echo "   2. Mở browser: http://localhost:5000"
    echo "   3. Cấu hình tại: http://localhost:5000/config"
    echo
    echo -e "${BLUE}📁 Files quan trọng:${NC}"
    echo "   - app.py: Web server chính"
    echo "   - config.txt: File cấu hình"
    echo "   - templates/: Giao diện web"
    echo "   - static/: Assets (CSS, JS, images)"
    echo
    echo -e "${BLUE}💡 Lưu ý:${NC}"
    echo "   - Lần đầu chạy cần cấu hình email/password"
    echo "   - Web interface chạy trên port 5000"
    echo "   - Logs được lưu trong web_app.log"
    echo
    
    # Ask to run immediately
    read -p "🚀 Bạn có muốn chạy web interface ngay bây giờ? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo
        print_info "Đang khởi động web interface..."
        ./run_web.sh
    else
        echo
        print_success "Setup hoàn tất. Chạy ./run_web.sh khi cần sử dụng."
    fi
}

# Run main function
main "$@"
