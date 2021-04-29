from Plugins.Plugin import PluginDescriptor

from . import _, screenwidth


def main(session, **kwargs):
	from .YouTubeUi import YouTubeMain
	session.open(YouTubeMain)


def Plugins(**kwargs):
	if screenwidth == 'svg':
		icon = 'YouTube.svg'
	elif screenwidth == 1920:
		icon = 'YouTube_FHD.png'
	else:
		icon = 'YouTube_HD.png'
	return [PluginDescriptor(
		name=_('YouTube'),
		description=_('Watch YouTube videos'),
		where=[PluginDescriptor.WHERE_PLUGINMENU,
				PluginDescriptor.WHERE_EXTENSIONSMENU],
		icon=icon,
		fnc=main)]
