$ffmpeg = "d:\Projects\VideoGenerator\bin\ffmpeg.exe"
$outDir = "d:\Projects\VideoGenerator\begi_za_solntsem_frames"
$song = "$outDir\song.mp3"
$phDir = "$outDir\clips_ph"

if (-not (Test-Path $phDir)) {
    New-Item -ItemType Directory -Path $phDir -Force | Out-Null
}

Write-Host "Rendering 12 animatic clips from approved keyframes (8.0s each)..."
$concatEntries = @()

for ($i = 1; $i -le 12; $i++) {
    $num = "{0:D2}" -f $i
    $clipPath = "$phDir\scene_$num.mp4"
    $srcImg = "$outDir\scene_$num.png"
    
    # Render fresh clip from the real generated keyframe
    & $ffmpeg -y -loglevel error -loop 1 -framerate 24 -i $srcImg `
        -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1" -t 8.0 `
        -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p $clipPath
        
    Write-Host "Scene $num rendered from $srcImg"
    $concatEntries += "file '$clipPath'"
}

$concatList = "$outDir\concat_animatic.txt"
[System.IO.File]::WriteAllLines($concatList, $concatEntries)

$finalAnimatic = "$outDir\begi_animatic_umbrella.mp4"
Write-Host "Assembling final animatic with full 12 scenes and song.mp3..."

& $ffmpeg -y -f concat -safe 0 -i $concatList -i $song `
    -map 0:v:0 -map 1:a:0 `
    -c:v libx264 -pix_fmt yuv420p -crf 18 `
    -c:a aac -b:a 256k `
    -shortest $finalAnimatic

Copy-Item $finalAnimatic "d:\Projects\VideoGenerator\begi_animatic.mp4" -Force
Write-Host "Animatic successfully assembled: $finalAnimatic"
