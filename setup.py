# -*- coding: utf-8 -*-

from distutils.core import setup
import os
import setup_translate


setup (name = 'enigma2-plugin-extensions-youtube',
	version='1.0',
	author='Taapat',
	author_email='taapat@gmail.com',
	packages=['YouTube'],
	package_data={'YouTube': ['*.png', 'icons/*.png']},
	description = 'Watch YouTube videos',
	cmdclass = setup_translate.cmdclass,
)
