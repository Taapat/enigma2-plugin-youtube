# Remove enigma2 python imports and variables in used files

cp -f ./test/ci_init.py ./src/__init__.py
sed -i 's/from Components/# from Components/g' ./src/YouTubeVideoUrl.py
sed -i 's/config.plugins.YouTube.maxResolution.value/"22"/g' ./src/YouTubeVideoUrl.py
sed -i 's/config.plugins.YouTube.useDashMP4.value/True/g' ./src/YouTubeVideoUrl.py
