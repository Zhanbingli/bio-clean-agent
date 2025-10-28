#!/bin/bash
set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logo
echo -e "${BLUE}"
cat << "EOF"
  ____  _         ____ _                     _                    _
 |  _ \(_) ___   / ___| | ___  __ _ _ __    / \   __ _  ___ _ __ | |_
 | |_) | |/ _ \ | |   | |/ _ \/ _` | '_ \  / _ \ / _` |/ _ \ '_ \| __|
 |  _ <| | (_) || |___| |  __/ (_| | | | |/ ___ \ (_| |  __/ | | | |_
 |_| \_\_|\___/  \____|_|\___|\__,_|_| |_/_/   \_\__, |\___|_| |_|\__|
                                                  |___/
EOF
echo -e "${NC}"
echo -e "${GREEN}智能生物医学数据清理代理 - 安装程序${NC}"
echo ""

# 检查是否为root用户
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}请不要使用root用户运行此脚本${NC}"
    exit 1
fi

# 检查Python版本
echo -e "${BLUE}[1/7]${NC} 检查Python版本..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到Python3${NC}"
    echo "请先安装Python 3.10或更高版本"
    exit 1
fi

python_version=$(python3 --version | awk '{print $2}')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${RED}错误: Python版本过低${NC}"
    echo "当前版本: $python_version"
    echo "需要版本: $required_version 或更高"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python版本: $python_version"

# 询问安装类型
echo ""
echo -e "${BLUE}[2/7]${NC} 选择安装类型:"
echo "  1) 基础安装 (仅核心功能)"
echo "  2) API安装 (包含Web界面和REST API)"
echo "  3) 完整安装 (所有功能，包括OpenAI集成)"
read -p "请选择 [1-3]: " install_type

case $install_type in
    1) extras="" ;;
    2) extras="[api]" ;;
    3) extras="[all]" ;;
    *)
        echo -e "${RED}无效选择，使用API安装${NC}"
        extras="[api]"
        ;;
esac

# 创建虚拟环境
echo ""
echo -e "${BLUE}[3/7]${NC} 创建虚拟环境..."
if [ -d ".venv" ]; then
    echo -e "${YELLOW}警告: .venv目录已存在${NC}"
    read -p "是否删除并重新创建? [y/N]: " recreate
    if [[ $recreate =~ ^[Yy]$ ]]; then
        rm -rf .venv
        python3 -m venv .venv
    fi
else
    python3 -m venv .venv
fi

# 激活虚拟环境
source .venv/bin/activate

# 升级pip
echo ""
echo -e "${BLUE}[4/7]${NC} 升级pip..."
pip install --upgrade pip -q

# 安装依赖
echo ""
echo -e "${BLUE}[5/7]${NC} 安装依赖 (这可能需要几分钟)..."
pip install -e ."$extras" -q

# 生成配置文件
echo ""
echo -e "${BLUE}[6/7]${NC} 生成配置文件..."

# 生成安全盐值
phi_salt=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# 创建.env文件
cat > .env <<EOF
# Bio Clean Agent 配置文件
# 生成时间: $(date)

# ==================== 安全配置 ====================
# PHI数据哈希盐值 (请妥善保管，不要泄露)
PHI_HASH_SALT=$phi_salt

# CORS允许的源 (生产环境请修改为实际域名)
ALLOWED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080

# 文件上传大小限制 (MB)
MAX_FILE_SIZE_MB=100

# ==================== API配置 ====================
# OpenAI API密钥 (可选，用于AI功能)
# OPENAI_API_KEY=your-key-here

# DeepSeek API密钥 (可选)
# DEEPSEEK_API_KEY=your-key-here

# ==================== 日志配置 ====================
# 日志级别: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO

# 启用审计日志
ENABLE_AUDIT_LOGGING=true

# ==================== 数据库配置 ====================
# 默认使用SQLite，生产环境建议使用PostgreSQL
# DATABASE_URL=sqlite:///./bio_clean.db
# DATABASE_URL=postgresql://user:password@localhost:5432/bioclean

# ==================== Redis配置 ====================
# 用于缓存和任务队列
# REDIS_URL=redis://localhost:6379/0

EOF

echo -e "${GREEN}✓${NC} 配置文件已创建: .env"

# 创建必要的目录
echo ""
echo -e "${BLUE}[7/7]${NC} 创建工作目录..."
mkdir -p data outputs reports uploads logs

echo -e "${GREEN}✓${NC} 目录结构已创建"

# 测试安装
echo ""
echo -e "${BLUE}测试安装...${NC}"
if python -c "import bio_clean_agent; print(f'Bio Clean Agent v{bio_clean_agent.__version__}')" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} 安装成功！"
else
    echo -e "${RED}✗${NC} 安装测试失败"
    exit 1
fi

# 显示下一步
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ 安装完成！${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}下一步操作:${NC}"
echo ""
echo "1. 激活虚拟环境:"
echo -e "   ${BLUE}source .venv/bin/activate${NC}"
echo ""

if [[ $extras == *"api"* ]] || [[ $extras == *"all"* ]]; then
    echo "2. 启动Web界面:"
    echo -e "   ${BLUE}python start_web.py${NC}"
    echo "   然后在浏览器打开: http://localhost:8080"
    echo ""
    echo "   或者使用CLI:"
    echo -e "   ${BLUE}bio-clean-agent --help${NC}"
else
    echo "2. 使用CLI:"
    echo -e "   ${BLUE}bio-clean-agent --help${NC}"
fi

echo ""
echo "3. 查看文档:"
echo -e "   ${BLUE}cat START_HERE.md${NC}"
echo ""
echo "4. 运行示例:"
echo -e "   ${BLUE}python examples/task_oriented_workflow.py${NC}"
echo ""

# 可选：询问是否配置OpenAI
if [[ $extras == *"openai"* ]] || [[ $extras == *"all"* ]]; then
    echo ""
    read -p "是否现在配置OpenAI API密钥? [y/N]: " config_openai
    if [[ $config_openai =~ ^[Yy]$ ]]; then
        read -p "请输入OpenAI API密钥: " openai_key
        if [ -n "$openai_key" ]; then
            sed -i "s/# OPENAI_API_KEY=your-key-here/OPENAI_API_KEY=$openai_key/" .env
            echo -e "${GREEN}✓${NC} OpenAI API密钥已配置"
        fi
    fi
fi

# Docker提示
echo ""
echo -e "${BLUE}提示:${NC} 也可以使用Docker运行:"
echo -e "   ${BLUE}docker-compose up -d${NC}"
echo ""

echo -e "${GREEN}感谢使用 Bio Clean Agent!${NC}"
echo ""
