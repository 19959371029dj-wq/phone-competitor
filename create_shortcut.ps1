# 创建桌面快捷方式 - 手机竞品分析
$InstallDir = $args[0]
if (-not $InstallDir -or -not (Test-Path $InstallDir)) {
    Write-Host "错误: 安装目录无效: $InstallDir"
    exit 1
}
$InstallDir = (Resolve-Path $InstallDir).Path.TrimEnd('\')

$Desktop = [Environment]::GetFolderPath('Desktop')
if (-not (Test-Path $Desktop)) {
    $Desktop = Join-Path $env:USERPROFILE "Desktop"
}
if (-not (Test-Path $Desktop)) {
    $Desktop = Join-Path $env:USERPROFILE "桌面"
}

$lnkPath = Join-Path $Desktop "手机竞品分析.lnk"
$WshShell = New-Object -ComObject WScript.Shell
$s = $WshShell.CreateShortcut($lnkPath)
$s.TargetPath = Join-Path $InstallDir "start.bat"
$s.WorkingDirectory = $InstallDir
$s.Description = "手机竞品分析 - 一键启动"
$s.Save()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($WshShell) | Out-Null

Write-Host "已创建快捷方式:"
Write-Host "  $lnkPath"
if (Test-Path $lnkPath) {
    Write-Host "成功。请到桌面查看「手机竞品分析」图标。"
} else {
    Write-Host "失败。请检查桌面路径: $Desktop"
    exit 1
}
