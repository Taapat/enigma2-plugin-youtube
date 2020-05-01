"""Test file to use pytest on Travis CI to test some plugin functions"""


def GetVideoId(q, eventType, order, s_type):
	from src.YouTubeApi import GetKey, YouTubeApi
	youtube = YouTubeApi(
		client_id=GetKey('823351347975-bn15et5mgugmu127cw_OizDn7h39v5siv55vbp51blrtc.w_Oi63zDpps.goog75leusercont87ent.com'),
		client_secret=GetKey('njp3Ep36VCkMQuw15_OizDcePvZ27qEqFE'),
		developer_key=GetKey('Xhi3_LoIzw_OizD15SyDVOJNmQn27JyFy43wWcf39CO9DVximw-51vB9Vg'),
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

	videos = None
	if s_type != 'video':
		for result in searchResponse.get('items', []):
			kind = result['id']['kind'].split('#')[1]
			playlistId = result['id'][kind+'Id']
		print 'playlistId', playlistId
		print 'kind', kind
		print 'Thumbnail', result['snippet']['thumbnails']['default']['url']
		print 'Title', result['snippet']['title']

		searchResponse = youtube.playlistItems_list(
			maxResults='3',
			playlistId=playlistId,
			pageToken='')

		for result in searchResponse.get('items', []):
			videos = result['snippet']['resourceId']['videoId']
	else:
		for result in searchResponse.get('items', []):
			videos = result['id']['videoId']

	print 'Video Id', videos
	if not videos:
		raise ValueError('Video Id not found')

	searchResponse = youtube.videos_list(v_id=videos)
	for result in searchResponse.get('items', []):
		print 'Id', result['id']
		print 'Thumbnail', result['snippet']['thumbnails']['default']['url']
		print 'Title', result['snippet']['title']
		print 'Views', result['statistics']['viewCount']
		print 'Duration', result['contentDetails']['duration']
		print 'Description', result['snippet']['description']
		print 'Likes', result['statistics']['likeCount']
		print 'Dislikes', result['statistics']['dislikeCount']
		print 'ThumbnailUrl', result['snippet']['thumbnails']['medium']['url']
		print 'ChannelId', result['snippet']['channelId']
		print 'PublishedAt', result['snippet']['publishedAt']

	return videos

def GetUrl(videos):
	from src.YouTubeVideoUrl import YouTubeVideoUrl
	ytdl = YouTubeVideoUrl()
	videoUrl = ytdl.extract(videos)
	videoUrl = videoUrl.split('&suburi=', 1)[0]
	print 'Video Url', videoUrl
	return videoUrl

def CheckExample(q, eventType='', order='relevance', s_type='video'):
	videos = GetVideoId(q=q, eventType=eventType, order=order, s_type=s_type)
	CheckVideoUrl(videos)

def CheckVideoUrl(videos):
	videoUrl = GetUrl(videos)
	from urllib2 import urlopen
	from src.__init__ import sslContext
	if sslContext:
		response = urlopen(videoUrl, context=sslContext)
	else:
		response = urlopen(videoUrl)
	info = response.info()
	print 'Video Url info:'
	print info

def test_searchUrl():
	CheckExample(q='official video')
	print 'Video Url exist'

def test_searchLive():
	CheckExample(q='112', eventType='live')
	print 'Live Video Url exist'

def test_mostViewedFeeds():
	CheckExample(q='', eventType='', order='viewCount')
	print 'Most Viewed Video Url exist'

def test_playlist():
	CheckExample(q='ello', eventType='', order='relevance', s_type='playlist')
	print 'Playlist Video Url exist'

_TESTS = [
		['UxxajLWwzqY', 'Test generic use_cipher_signature video'],
		['BaW_jenozKc', 'Test use the first video ID in the URL'],
		['a9LDPn-MO4I', 'Test 256k DASH audio (format 141) via DASH manifest'],
		['IB3lcPjvWLA', 'Test DASH manifest with encrypted signature'],
		['nfWlot6h_JM', 'Test JS player signature function name containing $'],
		['T4XJQO3qol8', 'Test controversy video'],
		['__2ABJjxzNo', 'Test YouTube Red ad is not captured for creator'],
		['lqQg6PlCWgI', 'Test Olympics'],
		['FIl7x6_3R5Y', 'Test extraction from multiple DASH manifests'],
		['lsguqyKfVQg', 'Test Title with JS-like syntax'],
		['M4gD1WSo5mA', 'Test Video licensed under Creative Commons'],
		['eQcmzGIKrzg', 'Test Channel-like uploader_url'],
		['uGpuVWrhIzE', 'Test Rental video preview'],
		['iqKdEhx-dD4', 'Test YouTube Red video with episode data'],
		['MgNrAu2pzNs', 'Test Youtube Music Auto-generated description'],
	]

def test_videoUrls():
	for url in _TESTS:
		print url[1]
		CheckVideoUrl(url[0])
		print 'Video Url exist'
