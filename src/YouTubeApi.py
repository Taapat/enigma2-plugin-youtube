from __future__ import print_function
from httplib import HTTPSConnection
from json import dumps, load
from urllib import quote
from urllib2 import urlopen, URLError, HTTPError

from . import sslContext


def GetKey(x):
	p = 3
	while True:
		if p > len(x):
			break
		pl = len(str(p))
		x = x[:p] + x[p+pl:]
		p += 12 - pl
	x = x.replace('w_OizD', 'a')
	x = x.replace('Xhi_Lo', 'A')
	return x


class YouTubeApi:
	def __init__(self, client_id, client_secret, developer_key, refresh_token):
		self.client_id = client_id
		self.client_secret = client_secret
		self.refresh_token = refresh_token
		self.key = '&key=' + developer_key
		if self.refresh_token:
			self.access_token = self.get_access_token()
		else:
			self.access_token = None
		if self.access_token:
			self.key = self.key + '&access_token=' + self.access_token

	def get_access_token(self):
		from OAuth import OAuth
		oauth = OAuth(self.client_id, self.client_secret)
		return oauth.get_access_token(self.refresh_token)

	def renew_access_token(self):
		print('[YouTubeApi] Unauthorized, try get new access token')
		self.key = self.key.split('&access_token=')[0]
		self.access_token = self.get_access_token()
		if self.access_token:
			self.key = self.key + '&access_token=' + self.access_token

	def get_response(self, url, count):
		if count:
			url = 'https://www.googleapis.com/youtube/v3/' + url
		response = None
		try:
			if sslContext:
				response = urlopen(url, context=sslContext)
			else:
				response = urlopen(url)
		except HTTPError as e:
			if e.code == 401 and self.access_token and count:
				self.renew_access_token()
				self.get_response(url, False)
			else:
				print ('[YouTubeApi] error in response %d' % e.code)
				return {}
		except URLError as e:
			print('[YouTubeApi] failed to reach a server:', e.reason)
			return {}
		if response:
			return load(response)
		return {}

	def get_aut_response(self, method, url, data, header, status, count):
		url = '/youtube/v3/' + url + self.key
		headers = {'Authorization': 'Bearer %s' % self.access_token}
		if header:
			headers.update(header)
		if sslContext:
			conn = HTTPSConnection('www.googleapis.com', context=sslContext)
		else:
			conn = HTTPSConnection('www.googleapis.com')
		conn.request(method, url, data, headers)
		response = conn.getresponse()
		conn.close()
		if response.status == status:
			return True
		elif response.status == 401 and self.access_token and count:
			self.renew_access_token()
			self.get_aut_response(self, method, url, data, header, status, False)
		else:
			print('[YouTubeApi] error in response', response.status)
			return None

	def subscriptions_list(self, maxResults, pageToken):
		pageToken = pageToken and '&pageToken=' + pageToken
		url = 'subscriptions?part=snippet&maxResults=' + maxResults + \
			'&mine=true' + pageToken + self.key
		return self.get_response(url, True)

	def playlists_list(self, maxResults, pageToken):
		pageToken = pageToken and '&pageToken=' + pageToken
		url = 'playlists?part=snippet&maxResults=' + maxResults + \
			'&mine=true' + pageToken + self.key
		return self.get_response(url, True)

	def channels_list(self, maxResults, pageToken):
		pageToken = pageToken and '&pageToken=' + pageToken
		url = 'channels?part=contentDetails&maxResults=' + maxResults + \
			'&mine=true' + pageToken + self.key
		return self.get_response(url, True)

	def search_list_full(self, videoEmbeddable, safeSearch, eventType, videoType,
			videoDefinition, order, part, q, relevanceLanguage,
			s_type, regionCode, maxResults, pageToken):

		videoEmbeddable = videoEmbeddable and 'videoEmbeddable=' + videoEmbeddable + '&'
		eventType = eventType and '&eventType=' + eventType
		videoType = videoType and '&videoType=' + videoType
		videoDefinition = videoDefinition and '&videoDefinition=' + videoDefinition
		relevanceLanguage = relevanceLanguage and '&relevanceLanguage=' + relevanceLanguage
		regionCode = regionCode and '&regionCode=' + regionCode
		pageToken = pageToken and '&pageToken=' + pageToken
		q = quote(q)

		url = 'search?' + videoEmbeddable + 'safeSearch=' + safeSearch + eventType + videoType + \
			videoDefinition + '&order=' + order + '&part=' + part.replace(',', '%2C') + \
			'&q=' + q + relevanceLanguage + '&type=' + s_type + regionCode + \
			'&maxResults=' + maxResults + pageToken + self.key
		return self.get_response(url, True)

	def search_list(self, part, channelId, maxResults, pageToken):
		pageToken = pageToken and '&pageToken=' + pageToken
		url = 'search?part=' + part.replace(',', '%2C') + \
			'&channelId=' + channelId + '&maxResults=' + maxResults + \
			pageToken + self.key
		return self.get_response(url, True)

	def videos_list(self, v_id):
		url = 'videos?part=id%2Csnippet%2Cstatistics%2CcontentDetails&id=' + \
			v_id.replace(',', '%2C') + self.key
		return self.get_response(url, True)

	def playlistItems_list(self, maxResults, playlistId, pageToken):
		pageToken = pageToken and '&pageToken=' + pageToken
		url = 'playlistItems?part=snippet&maxResults=' + \
			maxResults + '&playlistId=' + playlistId + pageToken + self.key
		return self.get_response(url, True)

	def subscriptions_insert(self, channelId):
		method = 'POST'
		url = 'subscriptions?part=snippet'
		data = dumps({
				'kind': 'youtube#subscription',
				'snippet': {
					'resourceId': {
						'kind': 'youtube#channel',
						'channelId': channelId
					}
				}
			})
		header = {'content-type': 'application/json'}
		status = 200
		return self.get_aut_response(method, url, data, header, status, True)

	def subscriptions_delete(self, subscribtionId):
		method = 'DELETE'
		url = 'subscriptions?id=' + subscribtionId
		status = 204
		return self.get_aut_response(method, url, '', None, status, True)

	def videos_rate(self, videoId, rating):
		method = 'POST'
		url = 'videos/rate?id=' + videoId + '&rating=' + rating
		header = {'content-length': '0'}
		status = 204
		return self.get_aut_response(method, url, '', header, status, True)
