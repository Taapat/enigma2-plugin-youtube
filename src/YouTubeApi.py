from __future__ import print_function

from json import dumps, load
from socket import error

from .compat import compat_quote
from .compat import compat_urlopen
from .compat import compat_Request
from .compat import compat_HTTPError
from .compat import compat_URLError
from .OAuth import OAuth, API_KEY


class YouTubeApi:
	def __init__(self, refresh_token):
		self.refresh_token = refresh_token
		if self.refresh_token:
			self.renew_access_token()
		else:
			self.access_token = None
			self.yt_auth = None
			self.key = '&key=%s' % API_KEY

	def renew_access_token(self):
		self.key = '&key=%s' % API_KEY
		self.access_token, self.yt_auth = OAuth().get_access_token(self.refresh_token)
		if self.access_token:
			self.key += '&access_token=%s' % self.access_token

	def is_auth(self):
		return bool(self.access_token)

	def get_yt_auth(self):
		return self.yt_auth

	def try_response(self, url_or_request, renew=True):
		response = {}
		status_code = 'Unknown'
		try:
			response = compat_urlopen(url_or_request, timeout=5)
		except compat_HTTPError as e:
			print('[YouTubeApi] HTTP Error in get response', e)
			status_code = e.getcode()
		except compat_URLError as e:
			print('[YouTubeApi] URL Error in get response', e)
		except Exception as e:
			print('[YouTubeApi] Error in get response', e)
		else:
			if response:
				status_code = response.getcode()
			elif response is None:
				response = {}
		if status_code == 401 and self.access_token and renew:
			print('[YouTubeApi] Unauthorized get response, try get new access token')
			self.renew_access_token()
			response, status_code = self.try_response(url_or_request, False)
		return response, status_code

	def get_response(self, url, max_results, page_token):
		url = 'https://www.googleapis.com/youtube/v3/{}{}{}{}'.format(
				url,
				max_results and '&maxResults=%s' % max_results,
				page_token and '&pageToken=%s' % page_token,
				self.key)
		response, status_code = self.try_response(url)
		if response and status_code == 200:
			try:
				response = load(response)
			except error as e:
				print('[YouTubeApi] Socket error in load response', e)
			else:
				return response
		return {}

	def get_aut_response(self, method, url, data, header, status):
		url = 'https://www.googleapis.com/youtube/v3/{}{}'.format(url, self.key)
		if data:
			data = dumps(data).encode('utf8')
		headers = {'Authorization': 'Bearer %s' % self.access_token}
		if header:
			headers.update(header)
		request = compat_Request(url, data=data, headers=headers)
		request.get_method = lambda: method
		_, status_code = self.try_response(request)
		if status_code == status:
			return True
		else:
			print('[YouTubeApi] aut response status code', status_code)

	def subscriptions_list(self, max_results, page_token, subscript_order):
		url = 'subscriptions?part=snippet&mine=true&order={}'.format(subscript_order)
		return self.get_response(url, max_results, page_token)

	def playlists_list(self, max_results, page_token):
		url = 'playlists?part=snippet&mine=true'
		return self.get_response(url, max_results, page_token)

	def channels_list(self, max_results, page_token):
		url = 'channels?part=contentDetails&mine=true'
		return self.get_response(url, max_results, page_token)

	def search_list_full(self, safe_search, order, part, q, s_type,
			max_results, page_token, **kwargs):

		q = compat_quote(q)

		url = 'search?{}safeSearch={}{}{}{}&order={}&part={}&q={}&type={}{}{}'.format(
				kwargs.get('video_embeddable', '') and 'videoEmbeddable=%s&' % kwargs['video_embeddable'],
				safe_search,
				kwargs.get('event_type', '') and '&eventType=%s' % kwargs['event_type'],
				kwargs.get('video_type', '') and '&videoType=%s' % kwargs['video_type'],
				kwargs.get('video_definition', '') and '&videoDefinition=%s' % kwargs['video_definition'],
				order, part.replace(',', '%2C'), q, s_type,
				kwargs.get('relevance_language', '') and '&relevanceLanguage=%s' % kwargs['relevance_language'],
				kwargs.get('region_code', '') and '&regionCode=%s' % kwargs['region_code'])
		return self.get_response(url, max_results, page_token)

	def search_list(self, order, part, channel_id, max_results, page_token):
		url = 'search?part={}&order={}&channelId={}'.format(
				part.replace(',', '%2C'), order, channel_id)
		return self.get_response(url, max_results, page_token)

	def videos_list(self, v_id):
		url = 'videos?part=id%2Csnippet%2Cstatistics%2CcontentDetails&id={}'.format(
				v_id.replace(',', '%2C'))
		return self.get_response(url, '', '')

	def playlist_items_list(self, order, max_results, playlist_id, page_token):
		url = 'playlistItems?part=snippet&order={}&playlistId={}'.format(
				order, playlist_id)
		return self.get_response(url, max_results, page_token)

	def subscriptions_insert(self, channel_id):
		method = 'POST'
		url = 'subscriptions?part=snippet'
		data = {'kind': 'youtube#subscription',
				'snippet': {
					'resourceId': {
						'kind': 'youtube#channel',
						'channelId': channel_id}}}
		header = {'content-type': 'application/json'}
		status = 200
		return self.get_aut_response(method, url, data, header, status)

	def subscriptions_delete(self, subscribtion_id):
		method = 'DELETE'
		url = 'subscriptions?id=%s' % subscribtion_id
		status = 204
		return self.get_aut_response(method, url, None, None, status)

	def videos_rate(self, video_id, rating):
		method = 'POST'
		url = 'videos/rate?id={}&rating={}'.format(video_id, rating)
		header = {'content-length': '0'}
		status = 204
		return self.get_aut_response(method, url, None, header, status)
