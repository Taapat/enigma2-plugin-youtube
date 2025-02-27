"""Test file to use pytest to test some plugin functions"""
from __future__ import print_function

import os
import pytest
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_video_id(q, event_type, order, s_type):
	from src.YouTubeApi import YouTubeApi
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
	from src.YouTubeVideoUrl import YouTubeVideoUrl
	from src.YouTubeApi import YouTubeApi
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
		from src.compat import compat_urlopen
		response = compat_urlopen(video_url)
		info = response.info()
		print('Video Url info:')
		print(info, descr, 'Video Url exist')


def check_jsinterpreter(code, args, expected):
	from src.jsinterp import JSInterpreter
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
	('Q_Nf4YoYY7E', 'Live video'),
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


from src.jsinterp import JSUndefined  # noqa: E402

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
def test_jsinterpreter(line, descr):  # NOSONAR Description in parameter for log
	val = function_list[line]
	check_jsinterpreter(code=val[0], args=val[1], expected=val[3])


def test_function_exceptions():
	from src.YouTubeVideoUrl import YouTubeVideoUrl
	ytdl = YouTubeVideoUrl()
	player_id = ytdl._extract_player_info()
	ytdl._unthrottle_url('&n=a&', player_id)
	ytdl._guess_encoding_from_content('', br'<meta charset=ascii>')
	ytdl._guess_encoding_from_content('', b'\xff\xfe')
