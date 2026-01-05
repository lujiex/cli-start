#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Code 一键配置脚本
适用于 Windows / Linux / WSL / macOS
Python 3.8+
"""

import os
import sys
import re
import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional

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


def get_input(prompt: str) -> str:
    """获取用户输入并清理"""
    try:
        return clean_input(input(prompt))
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


def run_command(args: list, check: bool = True) -> bool:
    """运行命令"""
    try:
        result = subprocess.run(
            args,
            check=check,
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False


def print_banner():
    """打印横幅"""
    print(f"{colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║           Claude Code 一键配置脚本                         ║")
    print("║        适用于 Windows / Linux / WSL / macOS                ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{colors.NC}")


def check_claude_installed() -> bool:
    """检查 Claude Code 是否已安装"""
    if not check_command_exists('claude'):
        print(f"{colors.YELLOW}[提示] 未检测到 Claude Code，请先安装：{colors.NC}")
        print("  npm install -g @anthropic-ai/claude-code")
        print()
        return False
    return True


def get_api_config() -> tuple:
    """获取 API 配置"""
    # Base URL
    print(f"{colors.GREEN}请输入 API Base URL (直接回车使用默认值 https://api.anthropic.com):{colors.NC}")
    base_url = get_input("")
    if not base_url:
        base_url = "https://api.anthropic.com"
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


def write_config_file(base_url: str, api_key: str) -> Path:
    """写入配置文件"""
    config_dir = Path.home() / '.claude'
    config_dir.mkdir(parents=True, exist_ok=True)

    # 写入 settings.json
    config_file = config_dir / 'settings.json'
    config_content = {
        "env": {
            "ANTHROPIC_AUTH_TOKEN": api_key,
            "ANTHROPIC_BASE_URL": base_url,
            "API_TIMEOUT_MS": "3000000",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"
        },
        "model": "opus"
    }
    config_file.write_text(json.dumps(config_content, indent=2), encoding='utf-8')

    print()
    print(f"{colors.GREEN}✓ API 配置完成！{colors.NC}")
    print(f"配置文件位置: {colors.BLUE}{config_file}{colors.NC}")

    return config_dir


def install_mcp_servers(claude_available: bool):
    """安装 MCP 服务器"""
    print()
    print(f"{colors.CYAN}════════════════════════════════════════════════════════════{colors.NC}")
    print(f"{colors.CYAN}                    MCP 服务器安装                          {colors.NC}")
    print(f"{colors.CYAN}════════════════════════════════════════════════════════════{colors.NC}")
    print()

    if not claude_available:
        print(f"{colors.YELLOW}[跳过] Claude Code 未安装，无法配置 MCP 服务器{colors.NC}")
        return

    # Context7 MCP
    if confirm(f"{colors.GREEN}是否安装 Context7 MCP？(用于获取最新库文档){colors.NC}", default=False):
        print(f"{colors.GREEN}请输入 Context7 API Key:{colors.NC}")
        context7_key = get_input("")
        if context7_key:
            print(f"{colors.BLUE}正在安装 Context7 MCP...{colors.NC}")
            if run_command(['claude', 'mcp', 'add', 'context7', '-s', 'user', '--',
                           'npx', '-y', '@upstash/context7-mcp', '--api-key', context7_key], check=False):
                print(f"{colors.GREEN}✓ Context7 MCP 安装成功{colors.NC}")
            else:
                print(f"{colors.RED}✗ Context7 MCP 安装失败{colors.NC}")
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
                print(f"{colors.BLUE}正在安装 Cunzhi MCP...{colors.NC}")
                if run_command(['claude', 'mcp', 'add', 'cunzhi', '-s', 'user', '--', str(cunzhi_path_obj)], check=False):
                    print(f"{colors.GREEN}✓ Cunzhi MCP 安装成功{colors.NC}")
                else:
                    print(f"{colors.RED}✗ Cunzhi MCP 安装失败{colors.NC}")
            else:
                print(f"{colors.YELLOW}[跳过] 文件不存在: {cunzhi_path}{colors.NC}")
        else:
            print(f"{colors.YELLOW}[跳过] 未输入路径，跳过 Cunzhi 安装{colors.NC}")

    # GitHub MCP
    print()
    if confirm(f"{colors.GREEN}是否安装 GitHub MCP？(GitHub 文档查询){colors.NC}", default=True):
        print(f"{colors.BLUE}正在安装 GitHub MCP...{colors.NC}")
        if run_command(['claude', 'mcp', 'add', 'github', '-s', 'user', '--transport', 'http', 'https://gitmcp.io/docs'], check=False):
            print(f"{colors.GREEN}✓ GitHub MCP 安装成功{colors.NC}")
        else:
            print(f"{colors.RED}✗ GitHub MCP 安装失败{colors.NC}")


def get_shell_rc_file() -> Optional[Path]:
    """检测当前 shell 配置文件"""
    # Windows 不需要配置 shell rc 文件
    if sys.platform == 'win32':
        return None

    shell = os.environ.get('SHELL', '')
    home = Path.home()

    if 'zsh' in shell:
        return home / '.zshrc'
    elif 'bash' in shell:
        bashrc = home / '.bashrc'
        if bashrc.exists():
            return bashrc
        return home / '.bash_profile'
    elif 'fish' in shell:
        # fish 使用不同的配置目录
        fish_config = home / '.config' / 'fish' / 'config.fish'
        fish_config.parent.mkdir(parents=True, exist_ok=True)
        return fish_config
    else:
        return home / '.profile'


def configure_environment_variable(config_dir: Path):
    """配置环境变量"""
    print()
    print(f"{colors.CYAN}════════════════════════════════════════════════════════════{colors.NC}")
    print(f"{colors.CYAN}                    环境变量配置                            {colors.NC}")
    print(f"{colors.CYAN}════════════════════════════════════════════════════════════{colors.NC}")
    print()

    env_var_name = "CLAUDE_CONFIG_DIR"
    env_var_value = str(config_dir)

    # Windows 使用不同的方式设置环境变量
    if sys.platform == 'win32':
        # 检查环境变量是否已存在
        current_value = os.environ.get(env_var_name)
        if current_value:
            print(f"{colors.GREEN}✓ 环境变量 {env_var_name} 已存在，跳过配置{colors.NC}")
            print(f"  当前值: {colors.BLUE}{current_value}{colors.NC}")
            return

        print(f"{colors.YELLOW}[提示] Claude Code 需要 {env_var_name} 环境变量才能读取配置文件{colors.NC}")
        if confirm(f"{colors.GREEN}是否设置用户环境变量？{colors.NC}", default=True):
            try:
                # 使用 setx 命令设置用户环境变量
                result = subprocess.run(
                    ['setx', env_var_name, env_var_value],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print(f"{colors.GREEN}✓ 环境变量已设置{colors.NC}")
                    print(f"{colors.YELLOW}[重要] 请重新打开命令提示符或 PowerShell 使环境变量生效{colors.NC}")
                else:
                    print(f"{colors.RED}✗ 设置环境变量失败{colors.NC}")
                    print(f"{colors.YELLOW}您可以手动设置环境变量：{colors.NC}")
                    print(f"  {colors.BLUE}setx {env_var_name} \"{env_var_value}\"{colors.NC}")
            except Exception as e:
                print(f"{colors.RED}✗ 设置环境变量失败: {e}{colors.NC}")
        else:
            print(f"{colors.YELLOW}[跳过] 未设置环境变量，Claude Code 可能无法读取配置文件{colors.NC}")
            print(f"{colors.YELLOW}您可以手动设置环境变量：{colors.NC}")
            print(f"  {colors.BLUE}setx {env_var_name} \"{env_var_value}\"{colors.NC}")
        return

    # Linux/macOS
    shell_rc = get_shell_rc_file()
    if not shell_rc:
        return

    # 检查环境变量是否已存在
    current_value = os.environ.get(env_var_name)
    if current_value:
        print(f"{colors.GREEN}✓ 环境变量 {env_var_name} 已存在，跳过配置{colors.NC}")
        print(f"  当前值: {colors.BLUE}{current_value}{colors.NC}")
        return

    # 检查 shell 配置文件中是否已有该变量
    if shell_rc.exists():
        try:
            content = shell_rc.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            content = ''
        # 检查 bash/zsh 和 fish 两种语法
        if f'export {env_var_name}=' in content or f'set -gx {env_var_name} ' in content:
            print(f"{colors.GREEN}✓ 环境变量 {env_var_name} 已在 {shell_rc} 中配置{colors.NC}")
            return

    print(f"{colors.YELLOW}[提示] Claude Code 需要 {env_var_name} 环境变量才能读取配置文件{colors.NC}")
    if confirm(f"{colors.GREEN}是否添加环境变量到 {shell_rc}？{colors.NC}", default=True):
        try:
            # fish shell 使用不同的语法
            is_fish = 'fish' in os.environ.get('SHELL', '')
            with open(shell_rc, 'a', encoding='utf-8') as f:
                f.write(f'\n# Claude Code 配置目录\n')
                if is_fish:
                    f.write(f'set -gx {env_var_name} "{env_var_value}"\n')
                else:
                    f.write(f'export {env_var_name}="{env_var_value}"\n')
            print(f"{colors.GREEN}✓ 环境变量已添加到 {shell_rc}{colors.NC}")
            print(f"{colors.YELLOW}[重要] 请运行以下命令使环境变量生效，或重新打开终端：{colors.NC}")
            print(f"  {colors.BLUE}source {shell_rc}{colors.NC}")

            # 同时设置当前 session 的环境变量
            os.environ[env_var_name] = env_var_value
        except Exception as e:
            print(f"{colors.RED}✗ 添加环境变量失败: {e}{colors.NC}")
    else:
        print(f"{colors.YELLOW}[跳过] 未添加环境变量，Claude Code 可能无法读取配置文件{colors.NC}")
        print(f"{colors.YELLOW}您可以手动添加以下内容到您的 shell 配置文件：{colors.NC}")
        print(f"  {colors.BLUE}export {env_var_name}=\"{env_var_value}\"{colors.NC}")


def print_completion():
    """打印完成信息"""
    print()
    print(f"{colors.GREEN}╔════════════════════════════════════════════════════════════╗{colors.NC}")
    print(f"{colors.GREEN}║                    全部配置完成！                          ║{colors.NC}")
    print(f"{colors.GREEN}╚════════════════════════════════════════════════════════════╝{colors.NC}")
    print()
    print(f"{colors.YELLOW}使用方法:{colors.NC}")
    print("  1. 进入您的项目目录: cd 你的项目目录")
    print("  2. 启动 Claude Code: claude")
    print()
    print(f"{colors.BLUE}查看已安装的 MCP: claude mcp list{colors.NC}")
    print()
    print(f"{colors.GREEN}祝您使用愉快！{colors.NC}")


def main():
    """主函数"""
    try:
        print_banner()
        claude_available = check_claude_installed()

        base_url, api_key = get_api_config()
        config_dir = write_config_file(base_url, api_key)
        install_mcp_servers(claude_available)
        configure_environment_variable(config_dir)
        print_completion()
    except KeyboardInterrupt:
        print(f"\n{colors.YELLOW}已取消配置{colors.NC}")
        sys.exit(130)


if __name__ == '__main__':
    main()
