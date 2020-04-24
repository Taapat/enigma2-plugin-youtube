"""Test file to use on Travis CI to test some plugin functions"""

from src.YouTubeApi import GetKey, YouTubeApi


def GetVideoId(q):
	youtube = YouTubeApi(
		client_id=GetKey('823351347975-bn15et5mgugmu127cw_OizDn7h39v5siv55vbp51blrtc.w_Oi63zDpps.goog75leusercont87ent.com'),
		client_secret=GetKey('njp3Ep36VCkMQuw15_OizDcePvZ27qEqFE'),
		developer_key=GetKey('Xhi3_LoIzw_OizD15SyDVOJNmQn27JyFy43wWcf39CO9DVximw-51vB9Vg'),
		refresh_token='')

	searchResponse = youtube.search_list_full(
		videoEmbeddable='',
		safeSearch='none',
		eventType='',
		videoType='',
		videoDefinition='',
		order='relevance',
		part='id,snippet',
		q=q,
		relevanceLanguage='',
		s_type='video',
		regionCode='',
		maxResults='3',
		pageToken='')

	for result in searchResponse.get('items', []):
		videos = result['id']['videoId']

	print 'YouTube Video ID', videos
	return videos

videos = GetVideoId('official video')

from src.YouTubeVideoUrl import YouTubeVideoUrl


def GetUrl(videos):
	ytdl = YouTubeVideoUrl()
	videoUrl = ytdl.extract(videos)
	videoUrl = videoUrl.split('&suburi=', 1)[0]
	print 'YouTube Video Url', videoUrl
	return videoUrl

videoUrl = GetUrl(videos)

from urllib2 import urlopen
from src.__init__ import sslContext


response = urlopen(videoUrl, context=sslContext)
print 'YouTube Video Url exist'
