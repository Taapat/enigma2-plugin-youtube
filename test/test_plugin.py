"""Test file to use pytest to test some plugin functions"""
from __future__ import print_function

import os
import pytest
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.compat import compat_urlopen  # noqa: E402
from src.jsinterp import JSInterpreter  # noqa: E402
from src.jsinterp import JSUndefined  # noqa: E402
from src.YouTubeApi import YouTubeApi  # noqa: E402
from src.YouTubeVideoUrl import YouTubeVideoUrl  # noqa: E402


def get_video_id(q, event_type, order, s_type):
	youtube = YouTubeApi('')

	search_response = youtube.search_list_full(
		safe_search='none',
		order=order,
		part='id,snippet',
		q=q,
		s_type=s_type,
		max_results='3',
		page_token='')

	if s_type != 'video':
		for result in search_response.get('items', []):
			kind = result['id']['kind'].split('#')[1]
			playlist_id = result['id'][kind + 'Id']
		print('playlistId', playlist_id)
		print('kind', kind)
		print('Thumbnail', result['snippet']['thumbnails']['default']['url'])
		print('Title', result['snippet']['title'])

		search_response = youtube.playlist_items_list(
			order=order,
			max_results='3',
			playlist_id=playlist_id,
			page_token='')

		for result in search_response.get('items', []):
			videos = result['snippet']['resourceId']['videoId']
	else:
		for result in search_response.get('items', []):
			videos = result['id']['videoId']

	print('Video Id', videos)

	search_response = youtube.videos_list(v_id=videos)
	for result in search_response.get('items', []):
		print('Id', result['id'])
		print('Thumbnail', result['snippet']['thumbnails']['default']['url'])
		print('Title', result['snippet']['title'])
		print('Duration', result['contentDetails']['duration'])
		print('Description', result['snippet']['description'])
		print('ThumbnailUrl', result['snippet']['thumbnails']['medium']['url'])
		print('ChannelId', result['snippet']['channelId'])
		print('PublishedAt', result['snippet']['publishedAt'])
	return videos


def get_url(videos):
	ytdl = YouTubeVideoUrl()
	ytapi = YouTubeApi(os.environ['YOUTUBE_PLUGIN_TOKEN'])
	video_url = ytdl.extract(videos, ytapi.get_yt_auth())
	video_url = video_url.split('&suburi=', 1)[0]
	print('Video Url', video_url)
	return video_url


def check_example(q, event_type='', order='relevance', s_type='video', descr=''):
	try:
		videos = get_video_id(q=q, event_type=event_type, order=order, s_type=s_type)
	except Exception as ex:
		print('Error in get_video_id %s, try second time' % str(ex))
		from time import sleep
		sleep(10)
		videos = get_video_id(q=q, event_type=event_type, order=order, s_type=s_type)
	check_video_url(videos, descr=descr)


def check_video_url(videos, descr):
	print('Test', descr)
	try:
		video_url = get_url(videos)
	except Exception as ex:
		if str(ex) == 'Too Many Requests':
			pytest.xfail('Error in get_url, Too Many Requests')
		elif str(ex) == 'No supported formats found in video info!':
			pytest.xfail('Error in get_url, No supported formats found in video info!')
		else:
			raise RuntimeError(ex)
	else:
		response = compat_urlopen(video_url)
		info = response.info()
		print('Video Url info:')
		print(info, descr, 'Video Url exist')


def check_jsinterpreter(code, args, expected):
	jsi = JSInterpreter(code)
	got = jsi.extract_function_from_code(*jsi.extract_function_code('f'))(args)
	print('JSInterpreter expected % s return %s' % (str(expected), str(got)))
	assert expected == got


def test_search_url():
	check_example(q='official video', descr='Search')


def test_search_live():
	check_example(q='112', event_type='live', descr='Search Live')


def test_most_viewed_feeds():
	try:
		check_example(q='', event_type='', order='viewCount', descr='Most Viewed')
	except Exception as ex:
		pytest.xfail(str(ex))


def test_playlist():
	check_example(q='vevo', event_type='', order='relevance', s_type='playlist', descr='Playlist')


video_list = (
	('YQHsXMglC9A', 'DASH mp4 video and audio'),
	('a9LDPn-MO4I', '256k DASH audio via manifest'),
	('T4XJQO3qol8', 'Controversy video'),
	('__2ABJjxzNo', 'Ad is not captured for creator'),
	('FIl7x6_3R5Y', 'Multiple DASH manifests'),
	('lsguqyKfVQg', 'Title with JS-like syntax'),
	('M4gD1WSo5mA', 'Licensed under Creative Commons'),
	('eQcmzGIKrzg', 'Channel-like uploader_url'),
	('iqKdEhx-dD4', 'YouTube Red with episode data'),
	('MgNrAu2pzNs', 'Auto generated description'),
	('zaPI8MvL8pg', 'Multifeed videos'),
	('HtVdAasjOgU', 'Embeddable video'),
	('bWgPKTOMoSY', 'Decrypting n-sig'),
	('9UMxZofMNbA', 'm3u8 playlist'),
	('8scG3KhC6Wo', 'Multiple audio languages'),
	('IUPU2Ygj_OQ', 'Live video'),
	('YDvsBbKfLPA', 'Live video'),
	pytest.param('uGpuVWrhIzE', 'Rental video preview', marks=pytest.mark.xfail),
	pytest.param('MeJVWBSsPAY', 'Non-agegated non-embeddable', marks=pytest.mark.xfail),
	pytest.param('7Do70nztRNE', 'Age gated embedded', marks=pytest.mark.xfail),
	pytest.param('Tq92D6wQ1mg', 'Age gated video', marks=pytest.mark.xfail),
	pytest.param('E8MCiceJJdY', 'Age gated video', marks=pytest.mark.xfail),
	pytest.param('K9TRaGNnjEU', 'Age gated video', marks=pytest.mark.xfail),
	pytest.param('6SJNVb0GnPI', 'Inappropriate video', marks=pytest.mark.xfail),
	pytest.param('s7_qI6_mIXc', 'DRM protected video', marks=pytest.mark.xfail),
	pytest.param('yYr8q0y5Jfg', 'Not available video', marks=pytest.mark.xfail),
	pytest.param('wrong_id', 'Wrong id', marks=pytest.mark.xfail),
)


@pytest.mark.parametrize('videos,descr', video_list)
def test_url(videos, descr):
	check_video_url(videos=videos, descr=descr)


function_list = (
	('function f(dt) { return new Date(dt) - 0; }', ['8/7/2009'], 'date', 1249603200000),
	('function f() { return new Date("December 15, 2017 at 7:49 am") - 0; }', (), 'date', 1513324140000),
	("function f(){return Math.pow(3, 5) + new Date('December 15, 2017 at 7:49 am') / 1000 * -239 - -24205;}", (), 'date', -361684445012),
	('function f() { return new Date("Wednesday 31 December 1969 18:01:26 MDT") - 0; }', (), 'date', 86000),
	('function f() { return new Date("1970-01-01T06:15:13.000+06:15") - 0; }', (), 'date', 13000),
	('function f(){return 1 + "2" + [3,4] + {k: 56} + null + undefined + Infinity;}', (), 'infinity', '123,4[object Object]nullundefinedInfinity'),
	('function f() { return void 42; }', (), 'void', JSUndefined),
	('function f() { var g = function(){}; return typeof g; }', (), 'typeof', 'function'),
	('function f(a, b){return Array.prototype.join.call(a, b)}', [[], '-'], 'prototype call', ''),
	('function f(a, b){return Array.prototype.join.apply(a, [b])}', [[], '-'], 'prototype apply', ''),
	('function f(i){return "test".charCodeAt(i)}', [0], 'charCodeAt', 116),
	('function f() {(d%e.length+e.length)%e.length;}', (), 'length', None),
	('function f(){return (19 & 21) + (19.0 & NaN);}', (), 'bit operator', 17.0),
	('function f(){return 11 >> 2;}', (), 'bit operator', 2),
	('function f(){return 42 << Infinity}', (), 'bit operator', 42),
	('function f(){return 42 ** "2";}', (), 'bit operator', 1764),
	('function f(){return 0 ?? 42;}', (), 'bit operator', 0),
	('function f() { if (0!=0) {return 1} else if (1==0) {return 2} else {return 10} }', (), 'else if', 10),
	('function f() { var x = /* 1 + */ 2; var y = /* 30 * 40 */ 50; return x + y; }', (), 'comments', 52),
)

function_repr_list = [(x, function_list[x][2]) for x in range(len(function_list))]


@pytest.mark.parametrize('line,descr', function_repr_list)
def test_jsinterpreter(line, descr):
	val = function_list[line]
	check_jsinterpreter(code=val[0], args=val[1], expected=val[3])


nsig_list = (
	('7862ca1f', 'X_LCxVDjAavgE5t', 'yxJ1dM6iz5ogUg'),
	('2f1832d2', 'YWt1qdbe8SAfkoPHW5d', 'RrRjWQOJmBiP'),
	('9c6dfc4a', 'jbu7ylIosQHyJyJV', 'uwI0ESiynAmhNg'),
)

nsig_repr_list = [(x, nsig_list[x][0]) for x in range(len(nsig_list))]


@pytest.mark.parametrize('line,descr', nsig_repr_list)
def test_nsig_extraction(line, descr):
	ytdl = YouTubeVideoUrl()
	val = nsig_list[line]
	ret = ytdl._unthrottle_url('&n=%s&' % val[1], val[0])[3:-1]
	print('Expected nsig % s return %s' % (val[2], ret))
	assert val[2] == ret


sig_list = (
	('6ed0d907', 'AOq0QJ8wRAIgXmPlOPSBkkUs1bYFYlJCfe29xx8j7v1pDL2QwbdV96sCIEzpWqMGkFR20CFOg51Tp-7vj_EMu-m37KtXJoOySqa0'),
	('3bb1f723', 'MyOSJXtKI3m-uME_jv7-pT12gOFC02RFkGoqWpzE0Cs69VdbwQ0LDp1v7j8xx92efCJlYFYb1sUkkBSPOlPmXgIARw8JQ0qOAOAA'),
	('2f1832d2', '0QJ8wRAIgXmPlOPSBkkUs1bYFYlJCfe29xxAj7v1pDL0QwbdV96sCIEzpWqMGkFR20CFOg51Tp-7vj_EMu-m37KtXJ2OySqa0q'),
)

sig_repr_list = [(x, sig_list[x][0]) for x in range(len(sig_list))]


@pytest.mark.parametrize('line,descr', sig_repr_list)
def test_signature_extraction(line, descr):
	ytdl = YouTubeVideoUrl()
	sig = '2aq0aqSyOoJXtK73m-uME_jv7-pT15gOFC02RFkGMqWpzEICs69VdbwQ0LDp1v7j8xx92efCJlYFYb1sUkkBSPOlPmXgIARw8JQ0qOAOAA'
	val = sig_list[line]
	ret = ytdl._decrypt_signature_url({'s': [sig], 'url': ['']}, val[0])[11:]
	print('Expected signature % s return %s' % (val[1], ret))
	assert val[1] == ret


def test_function_exceptions():
	ytdl = YouTubeVideoUrl()
	player_id = ytdl._extract_player_info()
	ytdl._unthrottle_url('&n=a&', player_id)
	ytdl._guess_encoding_from_content('', br'<meta charset=ascii>')
	ytdl._guess_encoding_from_content('', b'\xff\xfe')
