# 直接接收短/英文路径
param(
    [string]$srcPath,
    [string]$dstPath
)

if (-not (Test-Path $srcPath)) {
    Write-Host "[FAIL] Source not found: $srcPath"
    exit 1
}

Write-Host "[INFO] Source: $srcPath"
Write-Host "[INFO] Dest:   $dstPath"

$word = New-Object -ComObject Word.Application
$word.Visible = $true
$word.DisplayAlerts = 0

try {
    $doc = $word.Documents.Open($srcPath)
    Write-Host "[INFO] Opened, converting..."
    # 17 = wdFormatPDF
    $doc.SaveAs($dstPath, 17)
    $doc.Close()
    Write-Host "[OK] Saved"
} catch {
    Write-Host "[FAIL] $_"
} finally {
    $word.Quit()
}

if (Test-Path $dstPath) {
    $size = (Get-Item $dstPath).Length / 1KB
    Write-Host "[OK] Size: $size KB"
}
