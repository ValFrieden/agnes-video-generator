@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo   Создание аниматика «Беги за солнцем» (Жёлтый зонт)
echo ============================================================

if not exist clips_ph mkdir clips_ph

REM Генерация 8-секундных плейсхолдеров из кейнфреймов или якорного референса
for /L %%i in (1,1,12) do (
  set "n=0%%i"
  if %%i geq 10 set "n=%%i"
  set "src=scene_!n!.png"
  if not exist "!src!" set "src=character_ref.jpg"
  
  if not exist "clips_ph\scene_!n!.mp4" (
    echo Создание плейсхолдера scene_!n!...
    ffmpeg -y -loglevel error -loop 1 -framerate 24 -i "!src!" -vf "scale=1280:720,setsar=1" -t 8.0 -c:v libx264 -preset fast -crf 20 -pix_fmt yuv420p "clips_ph\scene_!n!.mp4"
  )
)

(
  for /L %%i in (1,1,9) do echo file 'clips_ph\scene_0%%i.mp4'
  for /L %%i in (10,1,12) do echo file 'clips_ph\scene_%%i.mp4'
) > concat_animatic.txt

ffmpeg -y -f concat -safe 0 -i concat_animatic.txt -i song.mp3 -map 0:v:0 -map 1:a:0 -c:v libx264 -pix_fmt yuv420p -crf 18 -c:a aac -b:a 256k -shortest "Беги_за_солнцем_аниматик_Желтый_зонт.mp4"

echo Аниматик готов: Беги_за_солнцем_аниматик_Желтый_зонт.mp4
pause
