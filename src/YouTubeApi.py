from httplib import HTTPSConnection
from json import dumps, load
from urllib import quote
from urllib2 import urlopen, HTTPError


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
		print '[YouTubeApi] Unauthorized, try get new access token'
		self.key = self.key.split('&access_token=')[0]
		self.access_token = self.get_access_token()
		if self.access_token:
			self.key = self.key + '&access_token=' + self.access_token

	def get_response(self, url, count):
		url = 'https://www.googleapis.com/youtube/v3/' + url
		response = None
		try:
			response = urlopen(url)
		except HTTPError, e:
			if e.code == 401 and self.access_token and count:
				self.renew_access_token()
				self.get_response(url, False)
			else:
				print ('[YouTubeApi] error in response %d' %e.code)
				return []
		if response:
			return load(response).get('items', [])

	def get_aut_response(self, method, url, data, header, status, count):
		url = '/youtube/v3/' + url + self.key
		headers = {'Authorization': 'Bearer %s' % self.access_token}
		if header:
			headers[header[0]] = header[1]
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
			print '[YouTubeApi] error in response', response.status
			return None

	def subscriptions_list(self, maxResults):
		url = 'subscriptions?part=snippet&maxResults=' + maxResults + \
			 '&mine=true' + self.key
		return self.get_response(url, True)

	def playlists_list(self):
		url = 'playlists?part=snippet&mine=true' + self.key
		return self.get_response(url, True)

	def channels_list(self):
		url = 'channels?part=contentDetails&mine=true' + self.key
		return self.get_response(url, True)

	def search_list_full(self, videoEmbeddable, safeSearch, videoType,
			videoDefinition, order, part, q, relevanceLanguage,
			s_type, regionCode, maxResults):

		videoEmbeddable = videoEmbeddable and 'videoEmbeddable=' + videoEmbeddable + '&'
		videoType = videoType and '&videoType=' + videoType
		videoDefinition = videoDefinition and '&videoDefinition=' + videoDefinition
		relevanceLanguage = relevanceLanguage and '&relevanceLanguage=' + relevanceLanguage
		regionCode = regionCode and '&regionCode=' + regionCode
		q = quote(q)

		url = 'search?' + videoEmbeddable + 'safeSearch=' + safeSearch + videoType + \
			videoDefinition + '&order=' + order + '&part=' + part.replace(',', '%2C') + \
			'&q=' + q + relevanceLanguage + '&type=' + s_type + regionCode + \
			'&maxResults=' + maxResults + self.key
		return self.get_response(url, True)

	def search_list(self, part, channelId, maxResults):
		url = 'search?part=' + part.replace(',', '%2C') + \
		'&channelId=' + channelId + '&maxResults=' + maxResults + \
		self.key
		return self.get_response(url, True)

	def videos_list(self, v_id):
		url = 'videos?part=id%2Csnippet%2Cstatistics%2CcontentDetails&id=' + \
			 v_id.replace(',', '%2C') + self.key
		return self.get_response(url, True)

	def playlistItems_list(self, maxResults, playlistId):
		url = 'playlistItems?part=snippet&maxResults=' + \
			 maxResults + '&playlistId=' + playlistId + self.key
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
		header = ['content-type', 'application/json']
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
		status = 204
		return self.get_aut_response(method, url, '', None, status, True)

