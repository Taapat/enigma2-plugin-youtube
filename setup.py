from distutils.core import setup
import setup_translate


PLUGIN_DIR = 'Extensions.YouTube'


setup(name='enigma2-plugin-extensions-youtube',
		version='1.0',
		author='Taapat',
		author_email='taapat@gmail.com',
		package_dir={PLUGIN_DIR: 'src'},
		packages=[PLUGIN_DIR],
		package_data={PLUGIN_DIR: ['*.png', 'icons/*.png', '*.svg', 'icons/*.svg', 'locale/*/LC_MESSAGES/*.mo']},
		description='Watch YouTube videos',
		cmdclass=setup_translate.cmdclass)
