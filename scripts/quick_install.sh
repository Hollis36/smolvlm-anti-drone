#!/bin/bash
# 快速安装脚本

set -e  # 遇到错误立即退出

echo "============================================================"
echo "   SmolVLM Anti-Drone System - 快速安装"
echo "============================================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# 检查 Python 版本
echo "[1/5] 检查 Python 版本..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    print_success "Python 版本: $PYTHON_VERSION"
else
    print_error "Python 3 未安装，请先安装 Python 3.9+"
    exit 1
fi

# 创建虚拟环境（可选）
echo ""
echo "[2/5] 创建虚拟环境..."
read -p "是否创建虚拟环境? (推荐) [Y/n] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "虚拟环境已创建"
    else
        print_warning "虚拟环境已存在"
    fi

    # 激活虚拟环境
    source venv/bin/activate
    print_success "虚拟环境已激活"
else
    print_warning "跳过虚拟环境创建"
fi

# 升级 pip
echo ""
echo "[3/5] 升级 pip..."
python3 -m pip install --upgrade pip --quiet
print_success "pip 已升级"

# 安装依赖
echo ""
echo "[4/5] 安装依赖..."
pip install -r requirements.txt --quiet
print_success "依赖安装完成"

# 安装项目（开发模式）
echo ""
echo "[5/5] 安装项目..."
pip install -e . --quiet
print_success "项目安装完成"

# 完成
echo ""
echo "============================================================"
echo "                   安装完成！"
echo "============================================================"
echo ""
echo "下一步："
echo "1. 运行快速测试: python examples/quickstart.py"
echo "2. 启动 API 服务: python -m src.api.rest_api"
echo "3. 运行验证脚本: bash scripts/verify_refactoring.sh"
echo "4. 查看文档: cat README.md"
echo ""
echo "如果创建了虚拟环境，下次使用时记得激活："
echo "  source venv/bin/activate"
echo ""
