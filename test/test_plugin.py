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
	ytdl = YouTubeVideoUrl()
	video_url = ytdl.extract(videos)
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
		elif 'inappropriate' in str(ex) or 'violating' in str(ex):
			pytest.xfail('Error in get_url, this video may be inappropriate for some users!')
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
	check_example(q='', event_type='', order='viewCount', descr='Most Viewed')


def test_playlist():
	check_example(q='vevo', event_type='', order='relevance', s_type='playlist', descr='Playlist')


video_id = ['BaW_jenozKc',
		'YQHsXMglC9A',
		'a9LDPn-MO4I',
		'T4XJQO3qol8',
		'__2ABJjxzNo',
		'FIl7x6_3R5Y',
		'lsguqyKfVQg',
		'M4gD1WSo5mA',
		'eQcmzGIKrzg',
		'uGpuVWrhIzE',
		'iqKdEhx-dD4',
		'MgNrAu2pzNs',
		'MeJVWBSsPAY',
		'zaPI8MvL8pg',
		'HtVdAasjOgU',
		'Tq92D6wQ1mg',
		'bWgPKTOMoSY',
		'6SJNVb0GnPI']


video_descr = ['Use the first video ID',
		'DASH mp4 video and audio',
		'256k DASH audio via manifest',
		'Controversy video',
		'Ad is not captured for creator',
		'Multiple DASH manifests',
		'Title with JS-like syntax',
		'Licensed under Creative Commons',
		'Channel-like uploader_url',
		'Rental video preview',
		'YouTube Red with episode data',
		'Auto generated description',
		'Non-agegated non-embeddable',
		'Multifeed videos',
		'Embeddable video',
		'Age gated video',
		'Decrypting n-sig',
		'Inappropriate video']


@pytest.mark.parametrize('descr', video_descr)
def test_url(descr):
	check_video_url(videos=video_id[video_descr.index(descr)], descr=descr)


def test_clean_html():
	from src.YouTubeVideoUrl import clean_html
	clean_html('<i>html</i><b>remove</b><br>-><a href="http://www.bbc.co.uk">BBC</a>1<br><p>stuff</p>')


@pytest.mark.xfail
def test_wrong_id():
	get_url('test_wrong_id')


@pytest.mark.xfail
def test_age_gate():
	get_url('K9TRaGNnjEU')
