$shell = New-Object -COMObject Shell.Application
$folder = $shell.Namespace("d:\Projects\VideoGenerator")
$file = $folder.ParseName("song_begi.mp3")
$dur = $folder.GetDetailsOf($file, 27) # 27 is usually Duration in Windows Shell
Write-Host "Duration:" $dur
Write-Host "File size:" (Get-Item "d:\Projects\VideoGenerator\song_begi.mp3").Length
