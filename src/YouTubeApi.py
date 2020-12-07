from __future__ import print_function

from json import dumps, load

from .compat import compat_ssl_urlopen
from .compat import compat_quote
from .compat import compat_urlopen
from .compat import compat_Request
from .compat import compat_HTTPError


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
		from .OAuth import OAuth
		oauth = OAuth(self.client_id, self.client_secret)
		return oauth.get_access_token(self.refresh_token)

	def renew_access_token(self):
		print('[YouTubeApi] Unauthorized, try get new access token')
		self.key = self.key.split('&access_token=')[0]
		self.access_token = self.get_access_token()
		if self.access_token:
			self.key = self.key + '&access_token=' + self.access_token

	def try_response(self, url):
		try:
			response = compat_ssl_urlopen(url)
			status_code = response.getcode()
		except compat_HTTPError as e:
			print ('[YouTubeApi] HTTPError error in get response')
			status_code = e.getcode()
		except:
			print ('[YouTubeApi] error in get response')
			status_code = 'Unknown'
		if status_code == 200:
			return load(response), None
		else:
			print ('[YouTubeApi] get response status code', status_code)
			return {}, status_code

	def get_response(self, url):
		url = 'https://www.googleapis.com/youtube/v3/' + url
		response, status_code = self.try_response(url)
		if response:
			return response
		elif status_code == 401 and self.access_token:
			self.renew_access_token()
			response, status_code = self.try_response(url)
		return response

	def try_aut_response(self, method, url, data, headers):
		try:
			request = compat_Request(url, data=data, headers=headers)
			request.get_method = lambda: method
			response = compat_urlopen(request)
			status_code = response.getcode()
			response.close()
		except compat_HTTPError as e:
			print ('[YouTubeApi] HTTPError error in aut response')
			status_code = e.getcode()
		except:
			print ('[YouTubeApi] error in aut response')
			return 'Unknown'
		return status_code

	def get_aut_response(self, method, url, data, header, status):
		url = 'https://www.googleapis.com/youtube/v3/' + url + self.key
		headers = {'Authorization': 'Bearer %s' % self.access_token}
		if header:
			headers.update(header)
		status_code = self.try_aut_response(method, url, data, header)
		if status_code == 401 and self.access_token:
			self.renew_access_token()
			status_code = self.try_aut_response(method, url, data, header)
		if status_code == status:
			return True
		else:
			print('[YouTubeApi] aut response status code', status_code)
			return None

	def subscriptions_list(self, maxResults, pageToken):
		pageToken = pageToken and '&pageToken=' + pageToken
		url = 'subscriptions?part=snippet&maxResults=' + maxResults + \
			'&mine=true' + pageToken + self.key
		return self.get_response(url)

	def playlists_list(self, maxResults, pageToken):
		pageToken = pageToken and '&pageToken=' + pageToken
		url = 'playlists?part=snippet&maxResults=' + maxResults + \
			'&mine=true' + pageToken + self.key
		return self.get_response(url)

	def channels_list(self, maxResults, pageToken):
		pageToken = pageToken and '&pageToken=' + pageToken
		url = 'channels?part=contentDetails&maxResults=' + maxResults + \
			'&mine=true' + pageToken + self.key
		return self.get_response(url)

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
		q = compat_quote(q)

		url = 'search?' + videoEmbeddable + 'safeSearch=' + safeSearch + eventType + videoType + \
			videoDefinition + '&order=' + order + '&part=' + part.replace(',', '%2C') + \
			'&q=' + q + relevanceLanguage + '&type=' + s_type + regionCode + \
			'&maxResults=' + maxResults + pageToken + self.key
		return self.get_response(url)

	def search_list(self, part, channelId, maxResults, pageToken):
		pageToken = pageToken and '&pageToken=' + pageToken
		url = 'search?part=' + part.replace(',', '%2C') + \
			'&channelId=' + channelId + '&maxResults=' + maxResults + \
			pageToken + self.key
		return self.get_response(url)

	def videos_list(self, v_id):
		url = 'videos?part=id%2Csnippet%2Cstatistics%2CcontentDetails&id=' + \
			v_id.replace(',', '%2C') + self.key
		return self.get_response(url)

	def playlistItems_list(self, maxResults, playlistId, pageToken):
		pageToken = pageToken and '&pageToken=' + pageToken
		url = 'playlistItems?part=snippet&maxResults=' + \
			maxResults + '&playlistId=' + playlistId + pageToken + self.key
		return self.get_response(url)

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
		return self.get_aut_response(method, url, data, header, status)

	def subscriptions_delete(self, subscribtionId):
		method = 'DELETE'
		url = 'subscriptions?id=' + subscribtionId
		status = 204
		return self.get_aut_response(method, url, '', None, status)

	def videos_rate(self, videoId, rating):
		method = 'POST'
		url = 'videos/rate?id=' + videoId + '&rating=' + rating
		header = {'content-length': '0'}
		status = 204
		return self.get_aut_response(method, url, '', header, status)
