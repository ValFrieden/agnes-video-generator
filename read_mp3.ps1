$files = Get-ChildItem "C:\Users\Valeri\Downloads" -Filter "*.mp3"
foreach ($f in $files) {
    if ($f.Length -eq 2100655) {
        Write-Host "MATCHED BY SIZE:" $f.FullName
        Copy-Item $f.FullName -Destination "d:\Projects\VideoGenerator\song_begi.mp3"
        Write-Host "Copied to song_begi.mp3"
        
        $bytes = [System.IO.File]::ReadAllBytes("d:\Projects\VideoGenerator\song_begi.mp3")
        Write-Host "Total bytes:" $bytes.Length
        
        # Write first 50KB to a text file for examination
        $enc = [System.Text.Encoding]::UTF8
        $str = $enc.GetString($bytes[0..[Math]::Min(50000, $bytes.Length-1)])
        [System.IO.File]::WriteAllText("d:\Projects\VideoGenerator\song_begi_raw_header.txt", $str)
        Write-Host "Wrote raw header text"
    }
}
