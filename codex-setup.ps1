# Codex CLI 一键配置脚本
# 适用于 Windows PowerShell

$ErrorActionPreference = "Stop"

# 颜色输出函数
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

# 清理输入中的不可见字符（控制字符、转义序列等）
function Clean-Input {
    param([string]$Input)
    # 移除 Bracketed Paste Mode 序列 (^[[200~ 和 ^[[201~)
    $cleaned = $Input -replace '\x1b\[\d*~', ''
    # 移除所有 ANSI 转义序列 (如方向键 ^[[A, ^[[B, ^[[C, ^[[D)
    $cleaned = $cleaned -replace '\x1b\[[0-9;]*[a-zA-Z]', ''
    # 移除所有控制字符 (ASCII 0-31, 127)
    $cleaned = $cleaned -replace '[\x00-\x1f\x7f]', ''
    return $cleaned.Trim()
}

Write-Host ""
Write-ColorOutput "╔════════════════════════════════════════════════════════════╗" "Cyan"
Write-ColorOutput "║             Codex CLI 一键配置脚本                         ║" "Cyan"
Write-ColorOutput "║           适用于 Windows PowerShell                        ║" "Cyan"
Write-ColorOutput "╚════════════════════════════════════════════════════════════╝" "Cyan"
Write-Host ""

# 检查是否已安装 Codex CLI
$codexInstalled = Get-Command codex -ErrorAction SilentlyContinue
if (-not $codexInstalled) {
    Write-ColorOutput "[提示] 未检测到 Codex CLI，请先安装：" "Yellow"
    Write-Host "  npm install -g @openai/codex"
    Write-Host ""
}

# 提示用户输入 API Base URL
Write-ColorOutput "请输入 API Base URL (直接回车使用默认值 https://api.openai.com/v1):" "Green"
$BaseUrl = Clean-Input (Read-Host)
if ([string]::IsNullOrWhiteSpace($BaseUrl)) {
    $BaseUrl = "https://api.openai.com/v1"
} else {
    # 如果 URL 不以 /v1 结尾，自动补充
    if (-not $BaseUrl.EndsWith("/v1")) {
        $BaseUrl = $BaseUrl.TrimEnd('/') + "/v1"
    }
}
Write-ColorOutput "使用 Base URL: $BaseUrl" "Cyan"

# 提示用户输入 API 密钥
Write-Host ""
Write-ColorOutput "请输入您的 API 密钥 (sk-xxx):" "Green"
$ApiKey = Clean-Input (Read-Host)

# 验证输入
if ([string]::IsNullOrWhiteSpace($ApiKey)) {
    Write-ColorOutput "[错误] API 密钥不能为空！" "Red"
    exit 1
}

if (-not $ApiKey.StartsWith("sk-")) {
    Write-ColorOutput "[警告] API 密钥格式可能不正确，通常以 'sk-' 开头" "Yellow"
    $continue = Clean-Input (Read-Host "是否继续？(y/n)")
    if ($continue -ne "y" -and $continue -ne "Y") {
        Write-ColorOutput "已取消配置" "Red"
        exit 1
    }
}

# 创建配置目录
$ConfigDir = "$env:USERPROFILE\.codex"
if (-not (Test-Path $ConfigDir)) {
    New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null
}

# 写入 config.toml (基础配置)
$ConfigFile = "$ConfigDir\config.toml"
$ConfigContent = @"
model_provider = "custom"
model = "gpt-5.2-codex"
model_reasoning_effort = "high"
network_access = "enabled"
disable_response_storage = true
model_verbosity = "high"

[model_providers.custom]
name = "custom"
base_url = "$BaseUrl"
wire_api = "responses"
requires_openai_auth = true
"@

[System.IO.File]::WriteAllText($ConfigFile, $ConfigContent, [System.Text.UTF8Encoding]::new($false))

# 写入 auth.json
$AuthFile = "$ConfigDir\auth.json"
$AuthContent = @"
{
  "OPENAI_API_KEY": "$ApiKey"
}
"@

[System.IO.File]::WriteAllText($AuthFile, $AuthContent, [System.Text.UTF8Encoding]::new($false))

Write-Host ""
Write-ColorOutput "✓ API 配置完成！" "Green"
Write-Host "配置文件位置:"
Write-Host "  " -NoNewline
Write-ColorOutput $ConfigFile "Cyan"
Write-Host "  " -NoNewline
Write-ColorOutput $AuthFile "Cyan"

# ==================== MCP 服务器安装 ====================
Write-Host ""
Write-ColorOutput "════════════════════════════════════════════════════════════" "Cyan"
Write-ColorOutput "                    MCP 服务器安装                          " "Cyan"
Write-ColorOutput "════════════════════════════════════════════════════════════" "Cyan"
Write-Host ""

# MCP 配置将追加到 config.toml
$McpConfig = ""

# Context7 MCP
Write-ColorOutput "是否安装 Context7 MCP？(用于获取最新库文档) [y/N]:" "Green"
$installContext7 = Clean-Input (Read-Host)
if ($installContext7 -eq "y" -or $installContext7 -eq "Y") {
    Write-ColorOutput "请输入 Context7 API Key:" "Green"
    $context7Key = Clean-Input (Read-Host)
    if (-not [string]::IsNullOrWhiteSpace($context7Key)) {
        $McpConfig += @"

[mcp_servers.context7]
type = "stdio"
command = "npx"
args = ["-y", "@upstash/context7-mcp", "--api-key", "$context7Key"]
tool_timeout_sec = 60.0
"@
        Write-ColorOutput "✓ Context7 MCP 配置已添加" "Green"
    } else {
        Write-ColorOutput "[跳过] 未输入 API Key，跳过 Context7 安装" "Yellow"
    }
}

# Cunzhi MCP
Write-Host ""
Write-ColorOutput "是否安装 Cunzhi MCP？(智能代码审查工具) [y/N]:" "Green"
$installCunzhi = Clean-Input (Read-Host)
if ($installCunzhi -eq "y" -or $installCunzhi -eq "Y") {
    Write-ColorOutput "请输入 Cunzhi 可执行文件的完整路径 (如 C:\path\to\cz.exe):" "Green"
    $cunzhiPath = Clean-Input (Read-Host)
    if (-not [string]::IsNullOrWhiteSpace($cunzhiPath)) {
        if (Test-Path $cunzhiPath) {
            $McpConfig += @"

[mcp_servers.cunzhi]
type = "stdio"
command = "$cunzhiPath"
tool_timeout_sec = 600.0
"@
            Write-ColorOutput "✓ Cunzhi MCP 配置已添加" "Green"
        } else {
            Write-ColorOutput "[跳过] 文件不存在: $cunzhiPath" "Yellow"
        }
    } else {
        Write-ColorOutput "[跳过] 未输入路径，跳过 Cunzhi 安装" "Yellow"
    }
}

# GitHub MCP
Write-Host ""
Write-ColorOutput "是否安装 GitHub MCP？(GitHub 文档查询) [Y/n]:" "Green"
$installGithub = Clean-Input (Read-Host)
if ($installGithub -ne "n" -and $installGithub -ne "N") {
    $McpConfig += @"

[mcp_servers.github]
type = "http"
url = "https://gitmcp.io/docs"
"@
    Write-ColorOutput "✓ GitHub MCP 配置已添加" "Green"
}

# 追加 MCP 配置到 config.toml
if (-not [string]::IsNullOrWhiteSpace($McpConfig)) {
    $existingContent = [System.IO.File]::ReadAllText($ConfigFile)
    [System.IO.File]::WriteAllText($ConfigFile, $existingContent + $McpConfig, [System.Text.UTF8Encoding]::new($false))
}

Write-Host ""
Write-ColorOutput "╔════════════════════════════════════════════════════════════╗" "Green"
Write-ColorOutput "║                    全部配置完成！                          ║" "Green"
Write-ColorOutput "╚════════════════════════════════════════════════════════════╝" "Green"
Write-Host ""
Write-ColorOutput "使用方法:" "Yellow"
Write-Host "  1. 进入您的项目目录: cd 你的项目目录"
Write-Host "  2. 启动 Codex CLI: codex"
Write-Host ""
Write-ColorOutput "祝您使用愉快！" "Green"
