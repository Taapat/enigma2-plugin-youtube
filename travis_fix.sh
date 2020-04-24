# Remove enigma2 python imports and variables in used files

cp -f travis_init.py ./src/__init__.py
sed -i 's/from Components/#from Components/g' ./src/YouTubeVideoUrl.py
sed -i 's/config.plugins.YouTube.maxResolution.value/"22"/g' ./src/YouTubeVideoUrl.py
sed -i 's/config.plugins.YouTube.searchRegion.value/""/g' ./src/YouTubeVideoUrl.py
sed -i 's/config.plugins.YouTube.searchLanguage.value/""/g' ./src/YouTubeVideoUrl.py
