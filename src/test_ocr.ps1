[Windows.Security.Cryptography.CryptographicBuffer, Windows.Security.Cryptography, ContentType = WindowsRuntime] | Out-Null
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Media.Ocr, ContentType = WindowsRuntime]
$null = [Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime]

$asyncOp = [Windows.Storage.StorageFile]::GetFileFromPathAsync((Resolve-Path "dataset/evidence/images/account_admin_console_20260926.png").Path)
$file = [WindowsRuntimeSystemExtensions]::AsTask($asyncOp).GetAwaiter().GetResult()

$streamOp = $file.OpenAsync([Windows.Storage.FileAccessMode]::Read)
$stream = [WindowsRuntimeSystemExtensions]::AsTask($streamOp).GetAwaiter().GetResult()

$decOp = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)
$decoder = [WindowsRuntimeSystemExtensions]::AsTask($decOp).GetAwaiter().GetResult()

$bmpOp = $decoder.GetSoftwareBitmapAsync()
$bitmap = [WindowsRuntimeSystemExtensions]::AsTask($bmpOp).GetAwaiter().GetResult()

$lang = [Windows.Globalization.Language]::new("en-US")
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
if (-not $engine) {
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
}

$ocrOp = $engine.RecognizeAsync($bitmap)
$result = [WindowsRuntimeSystemExtensions]::AsTask($ocrOp).GetAwaiter().GetResult()

Write-Host "OCR Text Length: " $result.Text.Length
Write-Host "Sample text: " $result.Text.Substring(0, [Math]::Min(500, $result.Text.Length))
