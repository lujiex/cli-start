#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Codex CLI 一键配置脚本
适用于 Windows / Linux / WSL / macOS
Python 3.8+
"""

import os
import sys
import re
import json
import shutil
from pathlib import Path

# 颜色支持
class Colors:
    """跨平台终端颜色支持"""

    def __init__(self):
        self.enabled = self._check_color_support()

    def _check_color_support(self) -> bool:
        """检查终端是否支持颜色"""
        # Windows 10+ 支持 ANSI 颜色
        if sys.platform == 'win32':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                # 获取标准输出句柄
                handle = kernel32.GetStdHandle(-11)
                # 获取当前控制台模式
                mode = ctypes.c_ulong()
                kernel32.GetConsoleMode(handle, ctypes.byref(mode))
                # 添加 ENABLE_VIRTUAL_TERMINAL_PROCESSING (0x0004) 标志
                kernel32.SetConsoleMode(handle, mode.value | 0x0004)
                return True
            except Exception:
                return os.environ.get('TERM') is not None
        return sys.stdout.isatty()

    @property
    def RED(self) -> str:
        return '\033[0;31m' if self.enabled else ''

    @property
    def GREEN(self) -> str:
        return '\033[0;32m' if self.enabled else ''

    @property
    def YELLOW(self) -> str:
        return '\033[1;33m' if self.enabled else ''

    @property
    def BLUE(self) -> str:
        return '\033[0;34m' if self.enabled else ''

    @property
    def CYAN(self) -> str:
        return '\033[0;36m' if self.enabled else ''

    @property
    def NC(self) -> str:
        return '\033[0m' if self.enabled else ''


colors = Colors()


def clean_input(text: str) -> str:
    """清理输入中的不可见字符（控制字符、转义序列等）"""
    # 移除 ANSI 转义序列
    text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z~]', '', text)
    # 移除控制字符
    text = re.sub(r'[\x00-\x1f\x7f]', '', text)
    return text.strip()


def get_tty_input(prompt: str) -> str:
    """
    从终端获取用户输入，支持 curl | python3 方式运行。
    当 stdin 被管道占用时，直接从 /dev/tty (Unix) 或 CON (Windows) 读取。
    """
    # 先打印提示信息到 stdout
    print(prompt, end='', flush=True)

    # 检查 stdin 是否是终端
    if sys.stdin.isatty():
        # 正常情况，stdin 是终端
        try:
            return sys.stdin.readline().rstrip('\n\r')
        except EOFError:
            return ''

    # stdin 被管道占用，需要从终端设备读取
    tty_path = None
    if sys.platform == 'win32':
        tty_path = 'CON'
    else:
        tty_path = '/dev/tty'

    try:
        with open(tty_path, 'r') as tty:
            return tty.readline().rstrip('\n\r')
    except (OSError, IOError) as e:
        print(f"\n{colors.RED}[错误] 无法从终端读取输入: {e}{colors.NC}", file=sys.stderr)
        print(f"{colors.YELLOW}提示: 请直接运行脚本而非通过管道{colors.NC}", file=sys.stderr)
        sys.exit(1)


def get_input(prompt: str) -> str:
    """获取用户输入并清理"""
    try:
        return clean_input(get_tty_input(prompt))
    except EOFError:
        return ''


def confirm(prompt: str, default: bool = False) -> bool:
    """确认提示"""
    suffix = '[Y/n]' if default else '[y/N]'
    response = get_input(f"{prompt} {suffix}: ").lower()
    if not response:
        return default
    return response in ('y', 'yes')


def check_command_exists(command: str) -> bool:
    """检查命令是否存在"""
    return shutil.which(command) is not None


def print_banner():
    """打印横幅"""
    print(f"{colors.CYAN}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║             Codex CLI 一键配置脚本                         ║")
    print("║        适用于 Windows / Linux / WSL / macOS                ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{colors.NC}")


def check_codex_installed():
    """检查 Codex CLI 是否已安装"""
    if not check_command_exists('codex'):
        print(f"{colors.YELLOW}[提示] 未检测到 Codex CLI，请先安装：{colors.NC}")
        print("  npm install -g @openai/codex")
        print()


def get_api_config() -> tuple:
    """获取 API 配置"""
    # Base URL
    print(f"{colors.GREEN}请输入 API Base URL (直接回车使用默认值 https://api.openai.com/v1):{colors.NC}")
    base_url = get_input("")
    if not base_url:
        base_url = "https://api.openai.com/v1"
    else:
        # 如果 URL 不以 /v1 结尾，自动补充
        base_url = base_url.rstrip('/')
        if not base_url.endswith('/v1'):
            base_url = f"{base_url}/v1"
    print(f"{colors.BLUE}使用 Base URL: {base_url}{colors.NC}")

    # API Key
    print()
    print(f"{colors.GREEN}请输入您的 API 密钥 (sk-xxx):{colors.NC}")
    api_key = get_input("")

    if not api_key:
        print(f"{colors.RED}[错误] API 密钥不能为空！{colors.NC}")
        sys.exit(1)

    if not api_key.startswith('sk-'):
        print(f"{colors.YELLOW}[警告] API 密钥格式可能不正确，通常以 'sk-' 开头{colors.NC}")
        if not confirm("是否继续？", default=False):
            print(f"{colors.RED}已取消配置{colors.NC}")
            sys.exit(1)

    return base_url, api_key


def escape_toml_string(s: str) -> str:
    """转义 TOML 字符串中的特殊字符"""
    # 转义反斜杠和双引号
    return s.replace('\\', '\\\\').replace('"', '\\"')


def write_config_files(base_url: str, api_key: str) -> Path:
    """写入配置文件"""
    config_dir = Path.home() / '.codex'
    config_dir.mkdir(parents=True, exist_ok=True)

    # 写入 config.toml
    config_file = config_dir / 'config.toml'
    escaped_base_url = escape_toml_string(base_url)
    config_content = f'''model_provider = "custom"
model = "gpt-5.2-codex"
model_reasoning_effort = "high"
network_access = "enabled"
disable_response_storage = true
model_verbosity = "high"

[model_providers.custom]
name = "custom"
base_url = "{escaped_base_url}"
wire_api = "responses"
requires_openai_auth = true
'''
    config_file.write_text(config_content, encoding='utf-8')

    # 写入 auth.json
    auth_file = config_dir / 'auth.json'
    auth_content = json.dumps({"OPENAI_API_KEY": api_key}, indent=2)
    auth_file.write_text(auth_content, encoding='utf-8')

    print()
    print(f"{colors.GREEN}✓ API 配置完成！{colors.NC}")
    print("配置文件位置:")
    print(f"  {colors.BLUE}{config_file}{colors.NC}")
    print(f"  {colors.BLUE}{auth_file}{colors.NC}")

    return config_dir


def install_mcp_servers(config_dir: Path):
    """安装 MCP 服务器"""
    print()
    print(f"{colors.CYAN}════════════════════════════════════════════════════════════{colors.NC}")
    print(f"{colors.CYAN}                    MCP 服务器安装                          {colors.NC}")
    print(f"{colors.CYAN}════════════════════════════════════════════════════════════{colors.NC}")
    print()

    config_file = config_dir / 'config.toml'
    mcp_config = ""

    # Context7 MCP
    if confirm(f"{colors.GREEN}是否安装 Context7 MCP？(用于获取最新库文档){colors.NC}", default=False):
        print(f"{colors.GREEN}请输入 Context7 API Key:{colors.NC}")
        context7_key = get_input("")
        if context7_key:
            escaped_key = escape_toml_string(context7_key)
            mcp_config += f'''

[mcp_servers.context7]
type = "stdio"
command = "npx"
args = ["-y", "@upstash/context7-mcp", "--api-key", "{escaped_key}"]
tool_timeout_sec = 60.0'''
            print(f"{colors.GREEN}✓ Context7 MCP 配置已添加{colors.NC}")
        else:
            print(f"{colors.YELLOW}[跳过] 未输入 API Key，跳过 Context7 安装{colors.NC}")

    # Cunzhi MCP
    print()
    if confirm(f"{colors.GREEN}是否安装 Cunzhi MCP？(智能代码审查工具){colors.NC}", default=False):
        print(f"{colors.GREEN}请输入 Cunzhi 可执行文件的完整路径 (如 /path/to/cz 或 C:\\path\\to\\cz.exe):{colors.NC}")
        cunzhi_path = get_input("")
        if cunzhi_path:
            cunzhi_path_obj = Path(cunzhi_path)
            if cunzhi_path_obj.exists():
                # 在 TOML 中需要转义反斜杠和双引号
                escaped_path = escape_toml_string(str(cunzhi_path_obj))
                mcp_config += f'''

[mcp_servers.cunzhi]
type = "stdio"
command = "{escaped_path}"
tool_timeout_sec = 600.0'''
                print(f"{colors.GREEN}✓ Cunzhi MCP 配置已添加{colors.NC}")
            else:
                print(f"{colors.YELLOW}[跳过] 文件不存在: {cunzhi_path}{colors.NC}")
        else:
            print(f"{colors.YELLOW}[跳过] 未输入路径，跳过 Cunzhi 安装{colors.NC}")

    # GitHub MCP
    print()
    if confirm(f"{colors.GREEN}是否安装 GitHub MCP？(GitHub 文档查询){colors.NC}", default=True):
        mcp_config += '''

[mcp_servers.github]
type = "http"
url = "https://gitmcp.io/docs"'''
        print(f"{colors.GREEN}✓ GitHub MCP 配置已添加{colors.NC}")

    # 追加 MCP 配置到 config.toml
    if mcp_config:
        with open(config_file, 'a', encoding='utf-8') as f:
            f.write(mcp_config)


def print_completion():
    """打印完成信息"""
    print()
    print(f"{colors.GREEN}╔════════════════════════════════════════════════════════════╗{colors.NC}")
    print(f"{colors.GREEN}║                    全部配置完成！                          ║{colors.NC}")
    print(f"{colors.GREEN}╚════════════════════════════════════════════════════════════╝{colors.NC}")
    print()
    print(f"{colors.YELLOW}使用方法:{colors.NC}")
    print("  1. 进入您的项目目录: cd 你的项目目录")
    print("  2. 启动 Codex CLI: codex")
    print()
    print(f"{colors.GREEN}祝您使用愉快！{colors.NC}")


def main():
    """主函数"""
    try:
        print_banner()
        check_codex_installed()

        base_url, api_key = get_api_config()
        config_dir = write_config_files(base_url, api_key)
        install_mcp_servers(config_dir)
        print_completion()
    except KeyboardInterrupt:
        print(f"\n{colors.YELLOW}已取消配置{colors.NC}")
        sys.exit(130)


if __name__ == '__main__':
    main()
