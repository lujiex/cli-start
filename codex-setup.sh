#!/bin/bash

# Codex CLI 一键配置脚本
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
    echo "$1" | sed 's/\x1b\[[0-9;]*[a-zA-Z]//g' | tr -d '\000-\037\177' | xargs
}

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║             Codex CLI 一键配置脚本                         ║"
echo "║           适用于 Linux / WSL / macOS                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 检查是否已安装 Codex CLI
if ! command -v codex &> /dev/null; then
    echo -e "${YELLOW}[提示] 未检测到 Codex CLI，请先安装：${NC}"
    echo -e "  npm install -g @openai/codex"
    echo ""
fi

# 提示用户输入 API Base URL
echo -e "${GREEN}请输入 API Base URL (直接回车使用默认值 https://api.openai.com/v1):${NC}"
read -r BASE_URL_INPUT < /dev/tty
BASE_URL=$(clean_input "$BASE_URL_INPUT")
if [ -z "$BASE_URL" ]; then
    BASE_URL="https://api.openai.com/v1"
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
CONFIG_DIR="$HOME/.codex"
mkdir -p "$CONFIG_DIR"

# 写入 config.toml (基础配置，不含 MCP)
CONFIG_FILE="$CONFIG_DIR/config.toml"
cat > "$CONFIG_FILE" << EOF
model_provider = "custom"
model = "gpt-4o"
model_reasoning_effort = "high"
network_access = "enabled"
disable_response_storage = true
model_verbosity = "high"

[model_providers.custom]
name = "custom"
base_url = "$BASE_URL"
wire_api = "responses"
requires_openai_auth = true
EOF

# 写入 auth.json
AUTH_FILE="$CONFIG_DIR/auth.json"
cat > "$AUTH_FILE" << EOF
{
  "OPENAI_API_KEY": "$API_KEY"
}
EOF

echo ""
echo -e "${GREEN}✓ API 配置完成！${NC}"
echo -e "配置文件位置:"
echo -e "  ${BLUE}$CONFIG_FILE${NC}"
echo -e "  ${BLUE}$AUTH_FILE${NC}"

# ==================== MCP 服务器安装 ====================
echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}                    MCP 服务器安装                          ${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

# MCP 配置将追加到 config.toml
MCP_CONFIG=""

# Context7 MCP
echo -e "${GREEN}是否安装 Context7 MCP？(用于获取最新库文档) [y/N]:${NC}"
read -r INSTALL_CONTEXT7_INPUT < /dev/tty
INSTALL_CONTEXT7=$(clean_input "$INSTALL_CONTEXT7_INPUT")
if [ "$INSTALL_CONTEXT7" = "y" ] || [ "$INSTALL_CONTEXT7" = "Y" ]; then
    echo -e "${GREEN}请输入 Context7 API Key:${NC}"
    read -r CONTEXT7_KEY_INPUT < /dev/tty
    CONTEXT7_KEY=$(clean_input "$CONTEXT7_KEY_INPUT")
    if [ -n "$CONTEXT7_KEY" ]; then
        MCP_CONFIG="${MCP_CONFIG}

[mcp_servers.context7]
type = \"stdio\"
command = \"npx\"
args = [\"-y\", \"@upstash/context7-mcp\", \"--api-key\", \"$CONTEXT7_KEY\"]
tool_timeout_sec = 60.0"
        echo -e "${GREEN}✓ Context7 MCP 配置已添加${NC}"
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
            MCP_CONFIG="${MCP_CONFIG}

[mcp_servers.cunzhi]
type = \"stdio\"
command = \"$CUNZHI_PATH\"
tool_timeout_sec = 600.0"
            echo -e "${GREEN}✓ Cunzhi MCP 配置已添加${NC}"
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
    MCP_CONFIG="${MCP_CONFIG}

[mcp_servers.github]
type = \"http\"
url = \"https://gitmcp.io/docs\""
    echo -e "${GREEN}✓ GitHub MCP 配置已添加${NC}"
fi

# 追加 MCP 配置到 config.toml
if [ -n "$MCP_CONFIG" ]; then
    echo "$MCP_CONFIG" >> "$CONFIG_FILE"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    全部配置完成！                          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}使用方法:${NC}"
echo -e "  1. 进入您的项目目录: cd 你的项目目录"
echo -e "  2. 启动 Codex CLI: codex"
echo ""
echo -e "${GREEN}祝您使用愉快！${NC}"
