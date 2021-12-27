# -*- coding: utf-8 -*-

# Language extension for distutils Python scripts. Based on this concept:
# http://wiki.maemo.org/Internationalize_a_Python_application
from __future__ import print_function
from distutils import cmd
from distutils.command.build import build as _build
import os


class build_trans(cmd.Command):
	description = 'Compile .po files into .mo files'

	def initialize_options(self):
		"""
		This method must be implemented by all command classes,
		but we don't need to set default values.
		"""

	def finalize_options(self):
		"""
		This method must be implemented by all command classes,
		but we don't need to set final values.
		"""

	def run(self):
		for lang in os.listdir('po'):
			if lang.endswith('.po'):
				src = os.path.join('po', lang)
				lang = lang[:-3]
				destdir = os.path.join('build/lib/Extensions/YouTube/locale',
						lang, 'LC_MESSAGES')
				if not os.path.exists(destdir):
					os.makedirs(destdir)
				dest = os.path.join(destdir, 'YouTube.mo')
				print("Language compile %s -> %s" % (src, dest))
				if os.system("msgfmt '%s' -o '%s'" % (src, dest)) != 0:
					raise RuntimeError("Failed to compile", src)


class build(_build):
	sub_commands = _build.sub_commands + [('build_trans', None)]

	def run(self):
		_build.run(self)


cmdclass = {
	'build': build,
	'build_trans': build_trans}
