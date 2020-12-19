from __future__ import print_function

from json import dumps, load

from .compat import compat_ssl_urlopen
from .compat import compat_quote
from .compat import compat_urlopen
from .compat import compat_Request
from .compat import compat_HTTPError
from .OAuth import OAuth, API_KEY


class YouTubeApi:
	def __init__(self, refresh_token):
		self.refresh_token = refresh_token
		if self.refresh_token:
			self.renew_access_token()
		else:
			self.access_token = None
			self.key = '&key=%s' % API_KEY

	def renew_access_token(self):
		self.key = '&key=%s' % API_KEY
		self.access_token = OAuth().get_access_token(self.refresh_token)
		if self.access_token:
			self.key += '&access_token=%s' % self.access_token

	def try_response(self, url):
		try:
			response = compat_ssl_urlopen(url)
			status_code = response.getcode()
		except compat_HTTPError as e:
			print ('[YouTubeApi] HTTPError error in get response', e)
			status_code = e.getcode()
		except Exception as e:
			print ('[YouTubeApi] error in get response', e)
			status_code = 'Unknown'
		if status_code == 200:
			return load(response), None
		else:
			print ('[YouTubeApi] get response status code', status_code)
			return {}, status_code

	def get_response(self, url, maxResults, pageToken):
		url = 'https://www.googleapis.com/youtube/v3/{}{}{}{}'.format(
				url,
				maxResults and '&maxResults=%s' % maxResults,
				pageToken and '&pageToken=%s' % pageToken,
				self.key)
		response, status_code = self.try_response(url)
		if response:
			return response
		elif status_code == 401 and self.access_token:
			print('[YouTubeApi] Unauthorized get response, try get new access token')
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
			print ('[YouTubeApi] HTTPError error in aut response', e)
			status_code = e.getcode()
		except Exception as e:
			print ('[YouTubeApi] error in aut response', e)
			return 'Unknown'
		return status_code

	def get_aut_response(self, method, url, data, header, status):
		url = 'https://www.googleapis.com/youtube/v3/{}{}'.format(url, self.key)
		headers = {'Authorization': 'Bearer %s' % self.access_token}
		if header:
			headers.update(header)
		status_code = self.try_aut_response(method, url, data, headers)
		if status_code == 401 and self.access_token:
			print('[YouTubeApi] Unauthorized get aut response, try get new access token')
			self.renew_access_token()
			status_code = self.try_aut_response(method, url, data, headers)
		if status_code == status:
			return True
		else:
			print('[YouTubeApi] aut response status code', status_code)
			return None

	def subscriptions_list(self, maxResults, pageToken):
		url = 'subscriptions?part=snippet&mine=true'
		return self.get_response(url, maxResults, pageToken)

	def playlists_list(self, maxResults, pageToken):
		url = 'playlists?part=snippet&mine=true'
		return self.get_response(url, maxResults, pageToken)

	def channels_list(self, maxResults, pageToken):
		url = 'channels?part=contentDetails&mine=true'
		return self.get_response(url, maxResults, pageToken)

	def search_list_full(self, videoEmbeddable, safeSearch, eventType, videoType,
			videoDefinition, order, part, q, relevanceLanguage,
			s_type, regionCode, maxResults, pageToken):

		q = compat_quote(q)

		url = 'search?{}safeSearch={}{}{}{}&order={}&part={}&q={}&type={}{}{}'.format(
				videoEmbeddable and 'videoEmbeddable=%s&' % videoEmbeddable,
				safeSearch,
				eventType and '&eventType=%s' % eventType,
				videoType and '&videoType=%s' % videoType,
				videoDefinition and '&videoDefinition=%s' % videoDefinition,
				order, part.replace(',', '%2C'), q, s_type,
				relevanceLanguage and '&relevanceLanguage=%s' % relevanceLanguage,
				regionCode and '&regionCode=%s' % regionCode)
		return self.get_response(url, maxResults, pageToken)

	def search_list(self, order, part, channelId, maxResults, pageToken):
		url = 'search?part={}&order={}&channelId={}'.format(
				part.replace(',', '%2C'), order, channelId)
		return self.get_response(url, maxResults, pageToken)

	def videos_list(self, v_id):
		url = 'videos?part=id%2Csnippet%2Cstatistics%2CcontentDetails&id={}'.format(
				v_id.replace(',', '%2C'))
		return self.get_response(url, '', '')

	def playlistItems_list(self, order, maxResults, playlistId, pageToken):
		url = 'playlistItems?part=snippet&order={}&playlistId={}'.format(
				order, playlistId)
		return self.get_response(url, maxResults, pageToken)

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
		url = 'subscriptions?id=%s' % subscribtionId
		status = 204
		return self.get_aut_response(method, url, '', None, status)

	def videos_rate(self, videoId, rating):
		method = 'POST'
		url = 'videos/rate?id={}&rating={}'.format(videoId, rating)
		header = {'content-length': '0'}
		status = 204
		return self.get_aut_response(method, url, '', header, status)
