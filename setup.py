from distutils.core import setup
import setup_translate


setup(name='enigma2-plugin-extensions-youtube',
		version='1.0',
		author='Taapat',
		author_email='taapat@gmail.com',
		package_dir={'Extensions.YouTube': 'src'},
		packages=['Extensions.YouTube'],
		package_data={'Extensions.YouTube': ['*.png', 'icons/*.png', '*.svg' 'icons/*.svg']},
		description='Watch YouTube videos',
		cmdclass=setup_translate.cmdclass)
