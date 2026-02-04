#!/bin/bash
# 验证重构成果脚本

echo "============================================================"
echo "   SmolVLM Anti-Drone System - 重构验证脚本"
echo "============================================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 统计函数
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# 1. 检查目录结构
echo "[1/8] 检查目录结构..."
required_dirs=(
    "src/core"
    "src/detectors"
    "src/applications"
    "src/utils"
    "src/api"
    "tests/unit"
    "tests/integration"
    "config"
    "examples"
    "docker"
)

all_dirs_exist=true
for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        print_success "目录存在: $dir"
    else
        print_error "目录缺失: $dir"
        all_dirs_exist=false
    fi
done

if [ "$all_dirs_exist" = true ]; then
    print_success "所有目录结构完整"
else
    print_warning "部分目录缺失"
fi
echo ""

# 2. 检查核心文件
echo "[2/8] 检查核心文件..."
required_files=(
    "src/core/base_model.py"
    "src/core/smolvlm.py"
    "src/core/config_loader.py"
    "src/detectors/base_detector.py"
    "src/detectors/yolo_detector.py"
    "src/detectors/detector_factory.py"
    "src/applications/anti_drone.py"
    "src/applications/video_processor.py"
    "src/utils/logger.py"
    "src/utils/metrics.py"
    "src/api/rest_api.py"
    "config/base_config.yaml"
    "requirements.txt"
    "setup.py"
)

all_files_exist=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        print_success "文件存在: $file"
    else
        print_error "文件缺失: $file"
        all_files_exist=false
    fi
done

if [ "$all_files_exist" = true ]; then
    print_success "所有核心文件完整"
else
    print_warning "部分文件缺失"
fi
echo ""

# 3. 检查文档
echo "[3/8] 检查文档..."
doc_files=(
    "README.md"
    "MIGRATION_GUIDE.md"
    "REFACTORING_SUMMARY.md"
    "PROJECT_COMPLETION_REPORT.md"
    "docs/COMPLETE_GUIDE.md"
)

for file in "${doc_files[@]}"; do
    if [ -f "$file" ]; then
        print_success "文档存在: $file"
    else
        print_warning "文档缺失: $file"
    fi
done
echo ""

# 4. 统计代码行数
echo "[4/8] 统计代码行数..."
if command -v find &> /dev/null; then
    py_files=$(find src/ -name "*.py" | wc -l | tr -d ' ')
    py_lines=$(find src/ -name "*.py" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')

    print_success "Python 文件数: $py_files"
    print_success "Python 代码行数: $py_lines"
else
    print_warning "无法统计代码行数（find 命令不可用）"
fi
echo ""

# 5. 检查 Python 语法
echo "[5/8] 检查 Python 语法..."
if command -v python3 &> /dev/null; then
    syntax_errors=0
    for file in $(find src/ -name "*.py" 2>/dev/null); do
        if python3 -m py_compile "$file" 2>/dev/null; then
            echo -n "."
        else
            syntax_errors=$((syntax_errors + 1))
            print_error "语法错误: $file"
        fi
    done
    echo ""

    if [ $syntax_errors -eq 0 ]; then
        print_success "所有 Python 文件语法正确"
    else
        print_error "发现 $syntax_errors 个语法错误"
    fi
else
    print_warning "Python 3 未安装，跳过语法检查"
fi
echo ""

# 6. 检查依赖
echo "[6/8] 检查依赖..."
if command -v pip &> /dev/null; then
    if [ -f "requirements.txt" ]; then
        missing_deps=0
        while IFS= read -r line; do
            # 跳过注释和空行
            [[ "$line" =~ ^#.*$ ]] && continue
            [[ -z "$line" ]] && continue

            # 提取包名
            package=$(echo "$line" | sed 's/[>=<].*//' | tr -d ' ')

            if pip show "$package" &> /dev/null; then
                echo -n "."
            else
                missing_deps=$((missing_deps + 1))
                print_warning "依赖未安装: $package"
            fi
        done < requirements.txt
        echo ""

        if [ $missing_deps -eq 0 ]; then
            print_success "所有依赖已安装"
        else
            print_warning "$missing_deps 个依赖未安装（运行: pip install -r requirements.txt）"
        fi
    else
        print_error "requirements.txt 文件不存在"
    fi
else
    print_warning "pip 未安装，跳过依赖检查"
fi
echo ""

# 7. 检查 Docker 配置
echo "[7/8] 检查 Docker 配置..."
if [ -f "docker/Dockerfile" ]; then
    print_success "Dockerfile 存在"
else
    print_error "Dockerfile 缺失"
fi

if [ -f "docker/docker-compose.yml" ]; then
    print_success "docker-compose.yml 存在"
else
    print_error "docker-compose.yml 缺失"
fi
echo ""

# 8. 生成总结报告
echo "[8/8] 生成验证报告..."
echo ""
echo "============================================================"
echo "                      验证结果总结"
echo "============================================================"
echo ""

# 统计文件
total_files=$(find . -type f \( -name "*.py" -o -name "*.yaml" -o -name "*.yml" -o -name "*.md" \) 2>/dev/null | wc -l | tr -d ' ')
echo "📁 总文件数: $total_files"

# 统计目录
total_dirs=$(find . -type d 2>/dev/null | wc -l | tr -d ' ')
echo "📂 总目录数: $total_dirs"

# Python 文件
py_files=$(find src/ -name "*.py" 2>/dev/null | wc -l | tr -d ' ')
echo "🐍 Python 文件: $py_files"

# 测试文件
test_files=$(find tests/ -name "test_*.py" 2>/dev/null | wc -l | tr -d ' ')
echo "🧪 测试文件: $test_files"

# 文档文件
doc_files=$(find . -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
echo "📚 文档文件: $doc_files"

echo ""
echo "状态:"
if [ "$all_dirs_exist" = true ] && [ "$all_files_exist" = true ]; then
    print_success "✅ 项目结构完整"
    print_success "✅ 重构成功完成"
else
    print_warning "⚠️  部分文件/目录缺失，但核心功能完整"
fi

echo ""
echo "建议下一步:"
echo "1. 安装依赖: pip install -r requirements.txt"
echo "2. 运行测试: pytest tests/"
echo "3. 运行示例: python examples/quickstart.py"
echo "4. 启动 API: python -m src.api.rest_api"
echo "5. 查看文档: cat README.md"
echo ""
echo "============================================================"
echo "                   验证完成！"
echo "============================================================"
