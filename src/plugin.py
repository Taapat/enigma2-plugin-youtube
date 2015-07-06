from Plugins.Plugin import PluginDescriptor

from . import _


def main(session, **kwargs):
	from YouTubeUi import YouTubeMain
	session.open(YouTubeMain)

def Plugins(**kwargs):
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

