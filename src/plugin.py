from Plugins.Plugin import PluginDescriptor
from enigma import getDesktop

from . import _


def main(session, **kwargs):
	from YouTubeUi import YouTubeMain
	session.open(YouTubeMain)

def Plugins(**kwargs):
	screenwidth = getDesktop(0).size().width()
	if screenwidth and screenwidth == 1920:
		return [PluginDescriptor(
			name = _('YouTube'),
			description = _('Watch YouTube videos'),
			where = [
				PluginDescriptor.WHERE_PLUGINMENU,
				PluginDescriptor.WHERE_EXTENSIONSMENU
			],
			icon = "piconhd.png", 
			fnc = main
			)]
	else:
		return [PluginDescriptor(
			name = _('YouTube'),
			description = _('Watch YouTube videos'),
			where = [
				PluginDescriptor.WHERE_PLUGINMENU,
				PluginDescriptor.WHERE_EXTENSIONSMENU
			],
			icon = "picon.png", 
			fnc = main
			)]

