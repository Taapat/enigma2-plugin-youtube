"""Test file to use pytest on Travis CI to test some plugin functions"""
from __future__ import print_function
import pytest


def GetVideoId(q, eventType, order, s_type):
	from src.YouTubeApi import GetKey, YouTubeApi
	youtube = YouTubeApi(
		client_id=GetKey('8903927018292-d15j8smibbw_O27izD924tqkh3991qtw_OizD5193bbw_OizD63uoq10s.w_O75izDpps.goo87gleusercon99tent.com'),
		client_secret=GetKey('Xhi3_Lo1EdTlsyO15H2BQrBpDeN27WFGIC'),
		developer_key=GetKey('Xhi3_LoIzw_OizD15SyBgGWigQZ27mpjHNu3eN239fWv5GQXscX51NUe3E'),
		refresh_token='')

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
			playlistId = result['id'][kind+'Id']
		print('playlistId', playlistId)
		print('kind', kind)
		print('Thumbnail', result['snippet']['thumbnails']['default']['url'])
		print('Title', result['snippet']['title'])

		searchResponse = youtube.playlistItems_list(
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
	except:
		print('Error in GetVideoId, try second time')
		from time import sleep
		sleep(10)
		videos = GetVideoId(q=q, eventType=eventType, order=order, s_type=s_type)
	CheckVideoUrl(videos, descr=descr)

def CheckVideoUrl(videos, descr):
	print('Test', descr)
	try:
		videoUrl = GetUrl(videos)
	except Exception as ex:
		if 'Too Many Requests' in ex:
			pytest.xfail('Error in GetUrl, Too Many Requests')
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
	CheckExample(q='youtube', eventType='', order='relevance', s_type='playlist', descr='Playlist')


_TESTS = [
		{'Id': 'UxxajLWwzqY', 'Description': 'Generic use_cipher_signature video'},
		{'Id': 'BaW_jenozKc', 'Description': 'Ue the first video ID in the URL'},
		{'Id': 'a9LDPn-MO4I', 'Description': '256k DASH audio (format 141) via DASH manifest'},
		{'Id': 'IB3lcPjvWLA', 'Description': 'DASH manifest with encrypted signature'},
		{'Id': 'nfWlot6h_JM', 'Description': 'JS player signature function name containing $'},
		{'Id': 'T4XJQO3qol8', 'Description': 'Controversy video'},
		{'Id': '__2ABJjxzNo', 'Description': 'YouTube Red ad is not captured for creator'},
		{'Id': 'lqQg6PlCWgI', 'Description': 'Olympics'},
		{'Id': 'FIl7x6_3R5Y', 'Description': 'Extraction from multiple DASH manifests'},
		{'Id': 'lsguqyKfVQg', 'Description': 'Title with JS-like syntax'},
		{'Id': 'M4gD1WSo5mA', 'Description': 'Video licensed under Creative Commons'},
		{'Id': 'eQcmzGIKrzg', 'Description': 'Channel-like uploader_url'},
		{'Id': 'uGpuVWrhIzE', 'Description': 'Rental video preview'},
		{'Id': 'iqKdEhx-dD4', 'Description': 'YouTube Red video with episode data'},
		{'Id': 'MgNrAu2pzNs', 'Description': 'Youtube Music Auto-generated description'},
	]

@pytest.fixture(params=_TESTS)
def video_data(request):
	return request.param

def test_videoUrls(video_data):
	CheckVideoUrl(videos=video_data['Id'], descr=video_data['Description'])
