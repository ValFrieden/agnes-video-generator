@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo   Сборка клипа «Беги за солнцем» (Жёлтый зонт) в ffmpeg
echo ============================================================

(
  for /L %%i in (1,1,9) do echo file 'scene_0%%i.mp4'
  for /L %%i in (10,1,12) do echo file 'scene_%%i.mp4'
) > concat_list.txt

ffmpeg -y -f concat -safe 0 -i concat_list.txt -i song.mp3 -map 0:v:0 -map 1:a:0 -c:v libx264 -pix_fmt yuv420p -crf 18 -c:a aac -b:a 256k -shortest "Беги_за_солнцем_клип_Желтый_зонт.mp4"

echo Готово: Беги_за_солнцем_клип_Желтый_зонт.mp4
pause
