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
from typing import Dict, List, Optional

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

MANAGED_ENV_BLOCK_START = "# >>> Claude Code env (managed by claude-code-setup.py) >>>"
MANAGED_ENV_BLOCK_END = "# <<< Claude Code env <<<"


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
        if sys.stdin is not None and sys.stdin.isatty():
            return clean_input(input(prompt))

        try:
            if sys.platform == 'win32':
                tty_in = 'CONIN$'
                tty_out = 'CONOUT$'
            else:
                tty_in = '/dev/tty'
                tty_out = '/dev/tty'

            with open(tty_out, 'w', encoding='utf-8', errors='ignore') as tty_w:
                tty_w.write(prompt)
                tty_w.flush()

            with open(tty_in, 'r', encoding='utf-8', errors='ignore') as tty_r:
                return clean_input(tty_r.readline())
        except OSError:
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


def detect_default_environment() -> str:
    """推断默认运行环境类型（用于预填选择项）"""
    if sys.platform == 'win32':
        return 'powershell'
    shell = os.environ.get('SHELL', '')
    if 'zsh' in shell:
        return 'zsh'
    if 'fish' in shell:
        return 'fish'
    if 'bash' in shell:
        return 'bash'
    return 'profile'


def choose_environment() -> str:
    """让用户选择当前的运行环境（用于写入环境变量并永久生效）"""
    default_env = detect_default_environment()
    print()
    print(f"{colors.CYAN}════════════════════════════════════════════════════════════{colors.NC}")
    print(f"{colors.CYAN}                    运行环境选择                            {colors.NC}")
    print(f"{colors.CYAN}════════════════════════════════════════════════════════════{colors.NC}")
    print()
    print(f"{colors.BLUE}检测到的平台: {sys.platform}{colors.NC}")
    print(f"{colors.BLUE}检测到的 SHELL: {os.environ.get('SHELL', '(未设置)')}{colors.NC}")
    print()
    print("请选择要写入环境变量的环境（永久生效）：")
    if sys.platform == 'win32':
        print("  1) PowerShell（用户环境变量 + Profile）")
        print("  2) 跳过（不写入环境变量）")
        default_choice = '1' if default_env == 'powershell' else '2'
        choice = get_input(f"请输入选项 [默认 {default_choice}]: ").strip()
        if not choice:
            choice = default_choice
        return 'powershell' if choice == '1' else 'skip'

    print("  1) bash（.bashrc / .bash_profile）")
    print("  2) zsh（.zshrc）")
    print("  3) fish（~/.config/fish/config.fish）")
    print("  4) PowerShell（~/.config/powershell/Microsoft.PowerShell_profile.ps1）")
    print("  5) POSIX 通用（~/.profile）")
    print("  6) 跳过（不写入环境变量）")
    default_map = {
        'bash': '1',
        'zsh': '2',
        'fish': '3',
        'powershell': '4',
        'profile': '5',
    }
    default_choice = default_map.get(default_env, '5')
    choice = get_input(f"请输入选项 [默认 {default_choice}]: ").strip()
    if not choice:
        choice = default_choice
    if choice == '1':
        return 'bash'
    if choice == '2':
        return 'zsh'
    if choice == '3':
        return 'fish'
    if choice == '4':
        return 'powershell'
    if choice == '5':
        return 'profile'
    return 'skip'


def get_shell_rc_file(selected_env: str) -> Optional[Path]:
    """根据用户选择返回需要写入的 rc/profile 文件路径"""
    home = Path.home()
    if selected_env == 'bash':
        bashrc = home / '.bashrc'
        bash_profile = home / '.bash_profile'
        if bashrc.exists() and bash_profile.exists():
            print()
            print("检测到以下 bash 配置文件：")
            print(f"  1) {bashrc}")
            print(f"  2) {bash_profile}")
            sub = get_input("请选择写入目标 [默认 1]: ").strip()
            if sub == '2':
                return bash_profile
            return bashrc
        if bashrc.exists():
            return bashrc
        return bash_profile
    if selected_env == 'zsh':
        return home / '.zshrc'
    if selected_env == 'fish':
        fish_config = home / '.config' / 'fish' / 'config.fish'
        fish_config.parent.mkdir(parents=True, exist_ok=True)
        return fish_config
    if selected_env == 'profile':
        return home / '.profile'
    return None


def get_powershell_profile_path() -> Path:
    """返回 PowerShell Profile 路径（按平台选默认位置）"""
    home = Path.home()
    if sys.platform == 'win32':
        documents = Path(os.environ.get('USERPROFILE', str(home))) / 'Documents'
        ps7_dir = documents / 'PowerShell'
        winps_dir = documents / 'WindowsPowerShell'
        # 优先使用 PowerShell 7 目录；如果仅存在 WindowsPowerShell 则使用它
        if ps7_dir.exists():
            return ps7_dir / 'Microsoft.PowerShell_profile.ps1'
        if winps_dir.exists():
            return winps_dir / 'Microsoft.PowerShell_profile.ps1'
        return ps7_dir / 'Microsoft.PowerShell_profile.ps1'
    return home / '.config' / 'powershell' / 'Microsoft.PowerShell_profile.ps1'


def sh_single_quote(value: str) -> str:
    """在 bash/zsh/profile 中安全引用字符串（单引号）"""
    return "'" + value.replace("'", "'\"'\"'") + "'"


def ps_double_quote(value: str) -> str:
    """在 PowerShell 双引号字符串中转义内容"""
    return value.replace('`', '``').replace('"', '`"')


def ps_single_quote(value: str) -> str:
    """在 PowerShell 单引号字符串中转义内容（单引号以两个单引号表示）"""
    return "'" + value.replace("'", "''") + "'"


def write_managed_env_block(target: Path, lines: List[str]) -> bool:
    """写入/更新一个可重复执行的环境变量 block，避免重复追加"""
    try:
        existing = target.read_text(encoding='utf-8', errors='ignore') if target.exists() else ''
    except Exception:
        existing = ''

    block = "\n".join([MANAGED_ENV_BLOCK_START, *lines, MANAGED_ENV_BLOCK_END]) + "\n"

    if MANAGED_ENV_BLOCK_START in existing and MANAGED_ENV_BLOCK_END in existing:
        prefix, rest = existing.split(MANAGED_ENV_BLOCK_START, 1)
        _, suffix = rest.split(MANAGED_ENV_BLOCK_END, 1)
        new_content = prefix.rstrip() + "\n\n" + block + suffix.lstrip()
    else:
        new_content = existing.rstrip() + "\n\n" + block

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(new_content, encoding='utf-8')
        return True
    except Exception:
        return False


def configure_environment_variables(selected_env: str, config_dir: Path, base_url: str, api_key: str):
    """配置环境变量并永久生效（按用户选择的环境写入 rc/profile 或用户环境变量）"""
    print()
    print(f"{colors.CYAN}════════════════════════════════════════════════════════════{colors.NC}")
    print(f"{colors.CYAN}                    环境变量配置                            {colors.NC}")
    print(f"{colors.CYAN}════════════════════════════════════════════════════════════{colors.NC}")
    print()

    if selected_env == 'skip':
        print(f"{colors.YELLOW}[跳过] 未写入环境变量（按你的选择）{colors.NC}")
        return

    # 不要在 rc/profile 中写死绝对路径：使用 shell 变量以便跨机器/用户目录迁移。
    # 仍然继续使用 config_dir 来写入 settings.json（那必须是绝对路径落盘）。
    if selected_env == 'powershell':
        claude_config_dir_value = "$HOME/.claude"
    elif sys.platform == 'win32':
        # 保险起见：Windows 通过 setx 写入时使用 USERPROFILE 占位符（不写死绝对路径）。
        claude_config_dir_value = "%USERPROFILE%\\.claude"
    else:
        claude_config_dir_value = "$HOME/.claude"

    variables: Dict[str, str] = {
        "CLAUDE_CONFIG_DIR": claude_config_dir_value,
        "ANTHROPIC_BASE_URL": base_url,
        "ANTHROPIC_AUTH_TOKEN": api_key,
        "API_TIMEOUT_MS": "3000000",
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    }

    print(f"{colors.YELLOW}[注意] 以下变量将被写入到你的 shell 配置文件/PowerShell Profile 中（包含明文 Token）{colors.NC}")
    print(f"{colors.BLUE}将配置（永久生效）:{colors.NC}")
    for name in variables.keys():
        display_value = variables[name]
        if name == "ANTHROPIC_AUTH_TOKEN":
            display_value = "***"
        print(f"  - {name}={display_value}")

    if not confirm(f"{colors.GREEN}是否继续写入并使其永久生效？{colors.NC}", default=True):
        print(f"{colors.YELLOW}[跳过] 未写入环境变量{colors.NC}")
        return

    # PowerShell（Windows 或用户主动选择）
    if selected_env == 'powershell':
        profile = get_powershell_profile_path()
        lines: List[str] = []
        # 使用 $HOME 组合路径，避免写死绝对路径；其余变量使用单引号避免 $ 展开
        lines.append('$env:CLAUDE_CONFIG_DIR = (Join-Path $HOME ".claude")')
        for name, value in variables.items():
            if name == "CLAUDE_CONFIG_DIR":
                continue
            lines.append(f'$env:{name} = {ps_single_quote(value)}')

        ok_profile = write_managed_env_block(profile, lines)
        if ok_profile:
            print(f"{colors.GREEN}✓ 已写入 PowerShell Profile: {colors.BLUE}{profile}{colors.NC}")
            print(f"{colors.YELLOW}[重要] 新开 PowerShell 会自动生效；当前会话可执行：{colors.NC}")
            print(f"  {colors.BLUE}. $PROFILE{colors.NC}")
        else:
            print(f"{colors.RED}✗ 写入 PowerShell Profile 失败: {profile}{colors.NC}")

        if sys.platform == 'win32' and confirm(f"{colors.GREEN}是否同时写入 Windows 用户环境变量（setx，永久生效）？{colors.NC}", default=True):
            failures: List[str] = []
            for name, value in variables.items():
                try:
                    result = subprocess.run(['setx', name, value], capture_output=True, text=True)
                    if result.returncode != 0:
                        failures.append(name)
                except Exception:
                    failures.append(name)
            if failures:
                print(f"{colors.RED}✗ 以下变量 setx 失败: {', '.join(failures)}{colors.NC}")
            else:
                print(f"{colors.GREEN}✓ 用户环境变量已写入（可能需要重新打开终端生效）{colors.NC}")
        return

    shell_rc = get_shell_rc_file(selected_env)
    if not shell_rc:
        print(f"{colors.RED}[错误] 未找到可写入的配置文件（选择={selected_env}）{colors.NC}")
        return

    if selected_env == 'fish':
        lines = []
        # fish: 使用双引号以支持 $HOME 展开，同时避免空格路径问题
        lines.append('set -gx CLAUDE_CONFIG_DIR "$HOME/.claude"')
        for name, value in variables.items():
            if name == "CLAUDE_CONFIG_DIR":
                continue
            lines.append(f"set -gx {name} {sh_single_quote(value)}")
    else:
        lines = []
        # bash/zsh/profile: 使用双引号以支持 $HOME 展开，同时避免空格路径问题
        lines.append('export CLAUDE_CONFIG_DIR="$HOME/.claude"')
        for name, value in variables.items():
            if name == "CLAUDE_CONFIG_DIR":
                continue
            lines.append(f"export {name}={sh_single_quote(value)}")

    ok = write_managed_env_block(shell_rc, lines)
    if ok:
        print(f"{colors.GREEN}✓ 环境变量已写入 {colors.BLUE}{shell_rc}{colors.NC}")
        print(f"{colors.YELLOW}[重要] 请执行以下命令使其在当前终端生效，或重新打开终端：{colors.NC}")
        print(f"  {colors.BLUE}source {shell_rc}{colors.NC}")
    else:
        print(f"{colors.RED}✗ 写入失败: {shell_rc}{colors.NC}")
        print(f"{colors.YELLOW}你可以手动添加以下内容：{colors.NC}")
        for line in lines:
            print(f"  {line}")


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
        selected_env = choose_environment()
        claude_available = check_claude_installed()

        base_url, api_key = get_api_config()
        config_dir = write_config_file(base_url, api_key)
        install_mcp_servers(claude_available)
        configure_environment_variables(selected_env, config_dir, base_url, api_key)
        print_completion()
    except KeyboardInterrupt:
        print(f"\n{colors.YELLOW}已取消配置{colors.NC}")
        sys.exit(130)


if __name__ == '__main__':
    main()
