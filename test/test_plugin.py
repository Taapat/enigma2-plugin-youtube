"""Test file to use pytest to test some plugin functions"""
from __future__ import print_function

import os
import pytest
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def GetVideoId(q, eventType, order, s_type):
	from src.YouTubeApi import YouTubeApi
	youtube = YouTubeApi('')

	searchResponse = youtube.search_list_full(
		videoEmbeddable='',
		safeSearch='none',
		eventType=eventType,
		videoType='',
		videoDefinition='',
		order=order,
		part='id,snippet',
		q=q,
		relevanceLanguage='',
		s_type=s_type,
		regionCode='',
		maxResults='3',
		pageToken='')

	if s_type != 'video':
		for result in searchResponse.get('items', []):
			kind = result['id']['kind'].split('#')[1]
			playlistId = result['id'][kind + 'Id']
		print('playlistId', playlistId)
		print('kind', kind)
		print('Thumbnail', result['snippet']['thumbnails']['default']['url'])
		print('Title', result['snippet']['title'])

		searchResponse = youtube.playlistItems_list(
			order=order,
			maxResults='3',
			playlistId=playlistId,
			pageToken='')

		for result in searchResponse.get('items', []):
			videos = result['snippet']['resourceId']['videoId']
	else:
		for result in searchResponse.get('items', []):
			videos = result['id']['videoId']

	print('Video Id', videos)

	searchResponse = youtube.videos_list(v_id=videos)
	for result in searchResponse.get('items', []):
		print('Id', result['id'])
		print('Thumbnail', result['snippet']['thumbnails']['default']['url'])
		print('Title', result['snippet']['title'])
		print('Duration', result['contentDetails']['duration'])
		print('Description', result['snippet']['description'])
		print('ThumbnailUrl', result['snippet']['thumbnails']['medium']['url'])
		print('ChannelId', result['snippet']['channelId'])
		print('PublishedAt', result['snippet']['publishedAt'])
	return videos


def GetUrl(videos):
	from src.YouTubeVideoUrl import YouTubeVideoUrl
	ytdl = YouTubeVideoUrl()
	videoUrl = ytdl.extract(videos)
	videoUrl = videoUrl.split('&suburi=', 1)[0]
	print('Video Url', videoUrl)
	return videoUrl


def CheckExample(q, eventType='', order='relevance', s_type='video', descr=''):
	try:
		videos = GetVideoId(q=q, eventType=eventType, order=order, s_type=s_type)
	except Exception as ex:
		print('Error in GetVideoId %s, try second time' % str(ex))
		from time import sleep
		sleep(10)
		videos = GetVideoId(q=q, eventType=eventType, order=order, s_type=s_type)
	CheckVideoUrl(videos, descr=descr)


def CheckVideoUrl(videos, descr):
	print('Test', descr)
	try:
		videoUrl = GetUrl(videos)
	except Exception as ex:
		if str(ex) == 'Too Many Requests':
			pytest.xfail('Error in GetUrl, Too Many Requests')
		elif str(ex) == 'No supported formats found in video info!':
			pytest.xfail('Error in GetUrl, No supported formats found in video info!')
		else:
			raise Exception(ex)
	else:
		from src.compat import compat_ssl_urlopen
		response = compat_ssl_urlopen(videoUrl)
		info = response.info()
		print('Video Url info:')
		print(info, descr, 'Video Url exist')


def test_searchUrl():
	CheckExample(q='official video', descr='Search')


def test_searchLive():
	CheckExample(q='112', eventType='live', descr='Search Live')


def test_mostViewedFeeds():
	CheckExample(q='', eventType='', order='viewCount', descr='Most Viewed')


def test_playlist():
	CheckExample(q='vevo', eventType='', order='relevance', s_type='playlist', descr='Playlist')


@pytest.mark.parametrize(
		'videos, descr',
		[('BaW_jenozKc', 'Use the first video ID'),
		('a9LDPn-MO4I', '256k DASH audio via DASH manifest'),
		('T4XJQO3qol8', 'Controversy video'),
		('__2ABJjxzNo', 'Ad is not captured for creator'),
		('FIl7x6_3R5Y', 'Multiple DASH manifests'),
		('lsguqyKfVQg', 'Title with JS-like syntax'),
		('M4gD1WSo5mA', 'Licensed under Creative Commons'),
		('eQcmzGIKrzg', 'Channel-like uploader_url'),
		('uGpuVWrhIzE', 'Rental video preview'),
		('iqKdEhx-dD4', 'YouTube Red with episode data'),
		('MgNrAu2pzNs', 'Auto generated description')],
)
def test_videoUrl(videos, descr):
	CheckVideoUrl(videos=videos, descr=descr)
