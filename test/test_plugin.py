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


def test_function_exceptions():
	from src.YouTubeVideoUrl import YouTubeVideoUrl
	ytdl = YouTubeVideoUrl()
	player_id = ytdl._extract_player_info()
	ytdl._decrypt_signature('', player_id)
	ytdl._unthrottle_url('&n=a&', player_id)
	ytdl._guess_encoding_from_content('', br'<meta charset=ascii>')
	ytdl._guess_encoding_from_content('', b'\xff\xfe')
