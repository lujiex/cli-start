#!/bin/bash

# Claude Code 一键配置脚本
# 适用于 Linux / WSL / macOS

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 清理输入中的不可见字符（控制字符、转义序列等）
clean_input() {
    # 移除 Bracketed Paste Mode 序列、ANSI 转义序列和控制字符
    echo "$1" | sed 's/\x1b\[[0-9;]*[a-zA-Z~]//g' | tr -d '\000-\037\177' | xargs
}

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║           Claude Code 一键配置脚本                         ║"
echo "║           适用于 Linux / WSL / macOS                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 检查是否已安装 Claude Code
if ! command -v claude &> /dev/null; then
    echo -e "${YELLOW}[提示] 未检测到 Claude Code，请先安装：${NC}"
    echo -e "  npm install -g @anthropic-ai/claude-code"
    echo ""
fi

# 提示用户输入 API Base URL
echo -e "${GREEN}请输入 API Base URL (直接回车使用默认值 https://api.anthropic.com):${NC}"
read -r BASE_URL_INPUT < /dev/tty
BASE_URL=$(clean_input "$BASE_URL_INPUT")
if [ -z "$BASE_URL" ]; then
    BASE_URL="https://api.anthropic.com"
fi
echo -e "${BLUE}使用 Base URL: $BASE_URL${NC}"

# 提示用户输入 API 密钥
echo ""
echo -e "${GREEN}请输入您的 API 密钥 (sk-xxx):${NC}"
read -r API_KEY_INPUT < /dev/tty
API_KEY=$(clean_input "$API_KEY_INPUT")

# 验证输入
if [ -z "$API_KEY" ]; then
    echo -e "${RED}[错误] API 密钥不能为空！${NC}"
    exit 1
fi

if [[ ! "$API_KEY" =~ ^sk- ]]; then
    echo -e "${YELLOW}[警告] API 密钥格式可能不正确，通常以 'sk-' 开头${NC}"
    echo -e "是否继续？(y/n)"
    read -r CONTINUE_INPUT < /dev/tty
    CONTINUE=$(clean_input "$CONTINUE_INPUT")
    if [ "$CONTINUE" != "y" ] && [ "$CONTINUE" != "Y" ]; then
        echo -e "${RED}已取消配置${NC}"
        exit 1
    fi
fi

# 创建配置目录
CONFIG_DIR="$HOME/.claude"
mkdir -p "$CONFIG_DIR"

# 写入配置文件
CONFIG_FILE="$CONFIG_DIR/settings.json"
cat > "$CONFIG_FILE" << EOF
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "$API_KEY",
    "ANTHROPIC_BASE_URL": "$BASE_URL",
    "API_TIMEOUT_MS": "3000000",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"
  },
  "model": "opus"
}
EOF

echo ""
echo -e "${GREEN}✓ API 配置完成！${NC}"
echo -e "配置文件位置: ${BLUE}$CONFIG_FILE${NC}"

# ==================== MCP 服务器安装 ====================
echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}                    MCP 服务器安装                          ${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

# 检查 claude 命令是否可用
if ! command -v claude &> /dev/null; then
    echo -e "${YELLOW}[跳过] Claude Code 未安装，无法配置 MCP 服务器${NC}"
else
    # Context7 MCP
    echo -e "${GREEN}是否安装 Context7 MCP？(用于获取最新库文档) [y/N]:${NC}"
    read -r INSTALL_CONTEXT7_INPUT < /dev/tty
    INSTALL_CONTEXT7=$(clean_input "$INSTALL_CONTEXT7_INPUT")
    if [ "$INSTALL_CONTEXT7" = "y" ] || [ "$INSTALL_CONTEXT7" = "Y" ]; then
        echo -e "${GREEN}请输入 Context7 API Key:${NC}"
        read -r CONTEXT7_KEY_INPUT < /dev/tty
        CONTEXT7_KEY=$(clean_input "$CONTEXT7_KEY_INPUT")
        if [ -n "$CONTEXT7_KEY" ]; then
            echo -e "${BLUE}正在安装 Context7 MCP...${NC}"
            claude mcp add context7 -s user -- npx -y @upstash/context7-mcp --api-key "$CONTEXT7_KEY" && \
            echo -e "${GREEN}✓ Context7 MCP 安装成功${NC}" || \
            echo -e "${RED}✗ Context7 MCP 安装失败${NC}"
        else
            echo -e "${YELLOW}[跳过] 未输入 API Key，跳过 Context7 安装${NC}"
        fi
    fi

    # Cunzhi MCP
    echo ""
    echo -e "${GREEN}是否安装 Cunzhi MCP？(智能代码审查工具) [y/N]:${NC}"
    read -r INSTALL_CUNZHI_INPUT < /dev/tty
    INSTALL_CUNZHI=$(clean_input "$INSTALL_CUNZHI_INPUT")
    if [ "$INSTALL_CUNZHI" = "y" ] || [ "$INSTALL_CUNZHI" = "Y" ]; then
        echo -e "${GREEN}请输入 Cunzhi 可执行文件的完整路径 (如 /path/to/cz 或 /path/to/cz.exe):${NC}"
        read -r CUNZHI_PATH_INPUT < /dev/tty
        CUNZHI_PATH=$(clean_input "$CUNZHI_PATH_INPUT")
        if [ -n "$CUNZHI_PATH" ]; then
            if [ -f "$CUNZHI_PATH" ] || [ -x "$CUNZHI_PATH" ]; then
                echo -e "${BLUE}正在安装 Cunzhi MCP...${NC}"
                claude mcp add cunzhi -s user -- "$CUNZHI_PATH" && \
                echo -e "${GREEN}✓ Cunzhi MCP 安装成功${NC}" || \
                echo -e "${RED}✗ Cunzhi MCP 安装失败${NC}"
            else
                echo -e "${YELLOW}[跳过] 文件不存在或不可执行: $CUNZHI_PATH${NC}"
            fi
        else
            echo -e "${YELLOW}[跳过] 未输入路径，跳过 Cunzhi 安装${NC}"
        fi
    fi

    # GitHub MCP
    echo ""
    echo -e "${GREEN}是否安装 GitHub MCP？(GitHub 文档查询) [Y/n]:${NC}"
    read -r INSTALL_GITHUB_INPUT < /dev/tty
    INSTALL_GITHUB=$(clean_input "$INSTALL_GITHUB_INPUT")
    if [ "$INSTALL_GITHUB" != "n" ] && [ "$INSTALL_GITHUB" != "N" ]; then
        echo -e "${BLUE}正在安装 GitHub MCP...${NC}"
        claude mcp add github -s user --transport http https://gitmcp.io/docs && \
        echo -e "${GREEN}✓ GitHub MCP 安装成功${NC}" || \
        echo -e "${RED}✗ GitHub MCP 安装失败${NC}"
    fi
fi

# ==================== 环境变量配置 ====================
echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}                    环境变量配置                            ${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

ENV_VAR_NAME="CLAUDE_CONFIG_DIR"
ENV_VAR_VALUE="$HOME/.claude"

# 检测当前 shell 配置文件
detect_shell_rc() {
    if [ -n "$ZSH_VERSION" ] || [ "$SHELL" = "/bin/zsh" ] || [ "$SHELL" = "/usr/bin/zsh" ]; then
        echo "$HOME/.zshrc"
    elif [ -n "$BASH_VERSION" ] || [ "$SHELL" = "/bin/bash" ] || [ "$SHELL" = "/usr/bin/bash" ]; then
        # 优先使用 .bashrc，如果不存在则使用 .bash_profile
        if [ -f "$HOME/.bashrc" ]; then
            echo "$HOME/.bashrc"
        else
            echo "$HOME/.bash_profile"
        fi
    else
        # 默认使用 .profile
        echo "$HOME/.profile"
    fi
}

SHELL_RC=$(detect_shell_rc)

# 检查环境变量是否已存在
check_env_exists() {
    # 检查当前环境
    if [ -n "${!ENV_VAR_NAME}" ]; then
        return 0
    fi
    # 检查 shell 配置文件中是否已有该变量
    if [ -f "$SHELL_RC" ] && grep -q "export $ENV_VAR_NAME=" "$SHELL_RC" 2>/dev/null; then
        return 0
    fi
    return 1
}

if check_env_exists; then
    echo -e "${GREEN}✓ 环境变量 $ENV_VAR_NAME 已存在，跳过配置${NC}"
    if [ -n "${!ENV_VAR_NAME}" ]; then
        echo -e "  当前值: ${BLUE}${!ENV_VAR_NAME}${NC}"
    fi
else
    echo -e "${YELLOW}[提示] Claude Code 需要 $ENV_VAR_NAME 环境变量才能读取配置文件${NC}"
    echo -e "${GREEN}是否添加环境变量到 $SHELL_RC？[Y/n]:${NC}"
    read -r ADD_ENV_INPUT < /dev/tty
    ADD_ENV=$(clean_input "$ADD_ENV_INPUT")
    if [ "$ADD_ENV" != "n" ] && [ "$ADD_ENV" != "N" ]; then
        # 添加环境变量到 shell 配置文件
        echo "" >> "$SHELL_RC"
        echo "# Claude Code 配置目录" >> "$SHELL_RC"
        echo "export $ENV_VAR_NAME=\"$ENV_VAR_VALUE\"" >> "$SHELL_RC"
        echo -e "${GREEN}✓ 环境变量已添加到 $SHELL_RC${NC}"
        echo -e "${YELLOW}[重要] 请运行以下命令使环境变量生效，或重新打开终端：${NC}"
        echo -e "  ${BLUE}source $SHELL_RC${NC}"

        # 同时设置当前 session 的环境变量
        export "$ENV_VAR_NAME"="$ENV_VAR_VALUE"
    else
        echo -e "${YELLOW}[跳过] 未添加环境变量，Claude Code 可能无法读取配置文件${NC}"
        echo -e "${YELLOW}您可以手动添加以下内容到您的 shell 配置文件：${NC}"
        echo -e "  ${BLUE}export $ENV_VAR_NAME=\"$ENV_VAR_VALUE\"${NC}"
    fi
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    全部配置完成！                          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}使用方法:${NC}"
echo -e "  1. 进入您的项目目录: cd 你的项目目录"
echo -e "  2. 启动 Claude Code: claude"
echo ""
echo -e "${BLUE}查看已安装的 MCP: claude mcp list${NC}"
echo ""
echo -e "${GREEN}祝您使用愉快！${NC}"
