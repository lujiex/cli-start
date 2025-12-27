# CLI 一键配置工具

一键配置 Claude Code 和 Codex CLI 的脚本集合，支持 Linux、WSL 和 macOS。

## 功能特性

- 自动配置 API 密钥
- 可选安装 MCP 服务器（Context7、Cunzhi、GitHub）
- 支持 Windows (PowerShell) 和 Unix (Bash) 环境

## 包含脚本

| 脚本 | 说明 |
|------|------|
| `claude-code-setup.sh` | Claude Code 配置脚本 (Linux/WSL/macOS) |
| `claude-code-setup.ps1` | Claude Code 配置脚本 (Windows PowerShell) |
| `codex-setup.sh` | Codex CLI 配置脚本 (Linux/WSL/macOS) |
| `codex-setup.ps1` | Codex CLI 配置脚本 (Windows PowerShell) |

## 使用方法

### Claude Code

**前置条件：** 先安装 Claude Code
```bash
npm install -g @anthropic-ai/claude-code
```

**Linux / WSL / macOS：**
```bash
bash claude-code-setup.sh
```

**Windows PowerShell：**
```powershell
.\claude-code-setup.ps1
```

### Codex CLI

**前置条件：** 先安装 Codex CLI
```bash
npm install -g @openai/codex
```

**Linux / WSL / macOS：**
```bash
bash codex-setup.sh
```

**Windows PowerShell：**
```powershell
.\codex-setup.ps1
```

## MCP 服务器

脚本支持安装以下 MCP 服务器：

- **Context7** - 获取最新库文档（需要 API Key）
- **Cunzhi** - 智能代码审查工具
- **GitHub** - GitHub 文档查询

## 许可证

[MIT](LICENSE)
