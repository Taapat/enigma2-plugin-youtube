# Remove enigma2 python imports and variables in used files

sed -i 's/from Components/#from Components/g' ./src/YouTubeVideoUrl.py
sed -i 's/config.plugins.YouTube.maxResolution.value/"22"/g' ./src/YouTubeVideoUrl.py
sed -i 's/config.plugins.YouTube.searchRegion.value/"US"/g' ./src/YouTubeVideoUrl.py
sed -i 's/config.plugins.YouTube.searchLanguage.value/"en"/g' ./src/YouTubeVideoUrl.py
