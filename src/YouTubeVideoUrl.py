# -*- coding: UTF-8 -*-
# This video extraction code based on youtube-dl: https://github.com/ytdl-org/youtube-dl

from __future__ import print_function

from re import escape
from re import match
from re import search
from re import sub
from json import dumps
from json import loads

from Components.config import config

from .compat import compat_str
from .compat import compat_Request
from .compat import compat_urlopen
from .compat import compat_URLError
from .compat import SUBURI
from .jsinterp import JSInterpreter
from .OAuth import YT_EMBKEY
from .OAuth import YT_KEY


PRIORITY_VIDEO_FORMAT = ()


def create_priority_formats():
	global PRIORITY_VIDEO_FORMAT
	itag = config.plugins.YouTube.maxResolution.value
	video_formats = (
		('17', '91', '13', '151', '160'),  # 176x144
		('5', '36', '92', '132', '133'),  # 400x240
		('18', '93', '34', '6', '134'),  # 640x360
		('35', '59', '78', '94', '135', '212'),  # 854x480
		('22', '95', '300', '136', '298'),  # 1280x720
		('37', '96', '301', '137', '299', '248', '303', '271'),  # 1920x1080
		('38', '266', '264', '138', '313', '315', '272', '308')  # 4096x3072
	)
	for video_format in video_formats:
		PRIORITY_VIDEO_FORMAT = video_format + PRIORITY_VIDEO_FORMAT
		if video_format[0] == itag:
			break


create_priority_formats()


class YouTubeVideoUrl():
	def __init__(self):
		self.use_dash_mp4 = ()
		self._code_cache = {}
		self._player_cache = {}
		self.nsig_cache = (None, None)

	@staticmethod
	def try_get(src, get, expected_type=None):
		try:
			v = get(src)
		except (AttributeError, KeyError, TypeError, IndexError):
			pass
		else:
			if expected_type is None or isinstance(v, expected_type):
				return v

	@staticmethod
	def _guess_encoding_from_content(content_type, webpage_bytes):
		m = match(r'[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+\s*;\s*charset=(.+)', content_type)
		if m:
			encoding = m.group(1)
		else:
			m = search(br'<meta[^>]+charset=[\'"]?([^\'")]+)[ /\'">]', webpage_bytes[:1024])
			if m:
				encoding = m.group(1).decode('ascii')
			elif webpage_bytes.startswith(b'\xff\xfe'):
				encoding = 'utf-16'
			else:
				encoding = 'utf-8'

		return encoding

	def _download_webpage(self, url, data=None, headers={}):
		""" Return the data of the page as a string """

		if data:
			data = dumps(data).encode('utf8')
		if data or headers:
			url = compat_Request(url, data=data, headers=headers)
			url.get_method = lambda: 'POST'

		try:
			urlh = compat_urlopen(url, timeout=5)
		except compat_URLError as e:  # pragma: no cover
			raise RuntimeError(e.reason)

		content_type = urlh.headers.get('Content-Type', '')
		webpage_bytes = urlh.read()
		encoding = self._guess_encoding_from_content(content_type, webpage_bytes)

		try:
			content = webpage_bytes.decode(encoding, 'replace')
		except Exception:  # pragma: no cover
			content = webpage_bytes.decode('utf-8', 'replace')

		return content

	@staticmethod
	def _extract_n_function_name(jscode):
		nfunc, idx = search(
			r'\.get\("n"\)\)&&\(b=(?P<nfunc>[a-zA-Z0-9$]+)(?:\[(?P<idx>\d+)\])?\([a-zA-Z0-9]\)',
			jscode
		).group('nfunc', 'idx')
		if not idx:
			return nfunc
		if int(idx) == 0:
			real_nfunc = search(
				r'var %s\s*=\s*\[([a-zA-Z_$][\w$]*)\];' % (escape(nfunc), ),
				jscode
			)
			if real_nfunc:
				return real_nfunc.group(1)

	def _extract_player_info(self):
		res = self._download_webpage('https://www.youtube.com/iframe_api')
		if res:
			player_id = search(r'player\\?/([0-9a-fA-F]{8})\\?/', res)
			if player_id:
				return player_id.group(1)
		print('[YouTubeVideoUrl] Cannot get player info')

	def _load_player(self, player_id):
		if player_id and player_id not in self._player_cache:
			self._player_cache[player_id] = self._download_webpage(
				'https://www.youtube.com/s/player/%s/player_ias.vflset/en_US/base.js' % player_id
			)

	def _extract_n_function(self, player_id):
		if player_id not in self._player_cache:
			self._load_player(player_id)
		jsi = JSInterpreter(self._player_cache[player_id])
		if player_id not in self._code_cache:
			funcname = self._extract_n_function_name(self._player_cache[player_id])
			self._code_cache[player_id] = jsi.extract_function_code(funcname)
		return lambda s: jsi.extract_function_from_code(*self._code_cache[player_id])([s])

	def _unthrottle_url(self, url, player_id):
		print('[YouTubeVideoUrl] Try unthrottle url')
		if not player_id:
			print('[YouTubeVideoUrl] Cannot decrypt nsig without player info')
			return url
		n_param = search(r'&n=(.+?)&', url).group(1)
		if self.nsig_cache[0] != n_param:
			self.nsig_cache = (None, None)
			try:
				ret = self._extract_n_function(player_id)(n_param)
			except Exception as ex:
				print('[YouTubeVideoUrl] Unable to decode nsig', ex)
			else:
				if ret.startswith('enhanced_except_'):
					print('[YouTubeVideoUrl] Unhandled exception in decode', ret)
				else:
					self.nsig_cache = (n_param, ret)
		if self.nsig_cache[1]:
			print('[YouTubeVideoUrl] Decrypted nsig %s => %s' % self.nsig_cache)
			return url.replace(self.nsig_cache[0], self.nsig_cache[1])
		if player_id in self._code_cache:
			del self._code_cache[player_id]
		return url

	def _extract_from_m3u8(self, manifest_url):
		url_map = {}

		def _get_urls(_manifest):
			lines = _manifest.split('\n')
			urls = [x for x in lines if x and not x.startswith('#')]
			return urls

		manifest = self._download_webpage(manifest_url)
		formats_urls = _get_urls(manifest)
		for format_url in formats_urls:
			itag = search(r'itag/(\d+?)/', format_url)
			itag = itag.group(1) if itag else ''
			url_map[itag] = format_url
		return url_map

	def _not_in_fmt(self, fmt, itag):
		return not (
			fmt.get('targetDurationSec') or
			fmt.get('drmFamilies') or
			fmt.get('type') == 'FORMAT_STREAM_TYPE_OTF' or
			itag in self.use_dash_mp4
		)

	def _extract_fmt_video_format(self, streaming_formats):
		""" Find the best format from our format priority map """
		print('[YouTubeVideoUrl] Try fmt url')
		for our_format in PRIORITY_VIDEO_FORMAT:
			for fmt in streaming_formats:
				itag = str(fmt.get('itag', ''))
				if itag == our_format and self._not_in_fmt(fmt, itag):
					url = fmt.get('url')
					if url:
						print('[YouTubeVideoUrl] Found fmt url')
						return url, our_format
		return '', ''

	def _extract_dash_audio_format(self, streaming_formats):
		""" If DASH MP4 video add link also on Dash MP4 Audio """
		print('[YouTubeVideoUrl] Try fmt audio url')
		for our_format in ('141', '140', '139', '258', '265', '325', '328'):
			for fmt in streaming_formats:
				itag = str(fmt.get('itag', ''))
				if itag == our_format and self._not_in_fmt(fmt, itag):
					url = fmt.get('url')
					if url:
						print('[YouTubeVideoUrl] Found fmt audio url')
						return url
		return ''

	def _extract_player_response(self, video_id, client):
		player_id = None
		url = 'https://www.youtube.com/youtubei/v1/player?key=%s&bpctr=9999999999&has_verified=1' % (YT_EMBKEY if client == 85 else YT_KEY)
		USER_AGENT = 'com.google.android.youtube/17.31.35 (Linux; U; Android 12) gzip'
		data = {
			'videoId': video_id,
			'playbackContext': {
				'contentPlaybackContext': {
					'html5Preference': 'HTML5_PREF_WANTS'
				}
			}
		}
		headers = {
			'content-type': 'application/json',
			'Origin': 'https://www.youtube.com'
		}
		if client == 85:
			player_id = self._extract_player_info()
			if player_id:
				if player_id not in self._player_cache:
					self._load_player(player_id)
				sts = search(
					r'(?:signatureTimestamp|sts)\s*:\s*(?P<sts>\d{5})',
					self._player_cache[player_id]
				).group('sts')
				if sts:
					data['playbackContext']['contentPlaybackContext']['signatureTimestamp'] = sts
			data['context'] = {
				'client': {
					'hl': 'en',
					'clientName': 'TVHTML5_SIMPLY_EMBEDDED_PLAYER',
					'clientVersion': '2.0',
				},
				'thirdParty': {
					'embedUrl': 'https://www.youtube.com/'
				}
			}
			headers['X-YouTube-Client-Name'] = 85
			headers['X-YouTube-Client-Version'] = '2.0'
		else:
			data['context'] = {
				'client': {
					'hl': 'en',
					'clientVersion': '17.31.35',
					'androidSdkVersion': 31,
					'clientName': 'ANDROID',
					'osName': 'Android',
					'osVersion': '12',
					'userAgent': USER_AGENT
				}
			}
			data['params'] = 'CgIQBg'
			headers['X-YouTube-Client-Name'] = 3
			headers['X-YouTube-Client-Version'] = '17.31.35'
			headers['User-Agent'] = USER_AGENT
		try:
			return loads(self._download_webpage(url, data, headers)), player_id
		except ValueError:  # pragma: no cover
			print('[YouTubeVideoUrl] Failed to parse JSON')
			return None, None

	def _real_extract(self, video_id):
		IGNORE_VIDEO_FORMAT = (
			'43', '44', '45', '46',  # webm
			'82', '83', '84', '85',  # 3D
			'100', '101', '102',  # 3D
			'167', '168', '169',  # webm
			'170', '171', '172',  # webm
			'218', '219',  # webm
			'242', '243', '244', '245', '246', '247',  # webm
			'249', '250', '251',  # webm
			'302'  # webm
		)
		url = ''

		player_response, player_id = self._extract_player_response(video_id, 3)
		if not player_response:
			raise RuntimeError('Player response not found!')

		is_live = self.try_get(player_response, lambda x: x['videoDetails']['isLive'])
		playability_status = player_response.get('playabilityStatus', {})

		if not is_live and playability_status.get('status') == 'LOGIN_REQUIRED':
			print('[YouTubeVideoUrl] Age gate content')
			player_response, player_id = self._extract_player_response(video_id, 85)
			if not player_response:
				raise RuntimeError('Age gate content player response not found!')

			playability_status = player_response.get('playabilityStatus', {})

		trailer_video_id = self.try_get(
			playability_status,
			lambda x: x['errorScreen']['playerLegacyDesktopYpcTrailerRenderer']['trailerVideoId'],
			compat_str
		)
		if trailer_video_id:
			print('[YouTubeVideoUrl] Trailer video')
			return str(trailer_video_id)

		streaming_data = player_response.get('streamingData', {})
		streaming_formats = streaming_data.get('formats', [])

		# If priority format changed in config, recreate priority list
		if PRIORITY_VIDEO_FORMAT[0] != config.plugins.YouTube.maxResolution.value:
			create_priority_formats()

		if not is_live and streaming_formats:
			DASHMP4_FORMAT = (
				'133', '134', '135', '136', '137', '138',
				'160', '212', '264', '266', '298', '299',
				'248', '303', '271', '313', '315', '272', '308'
			)
			streaming_formats.extend(streaming_data.get('adaptiveFormats', []))

			if config.plugins.YouTube.useDashMP4.value:
				self.use_dash_mp4 = ()
			else:  # pragma: no cover
				print('[YouTubeVideoUrl] skip DASH MP4 format')
				self.use_dash_mp4 = DASHMP4_FORMAT

			url, our_format = self._extract_fmt_video_format(streaming_formats)
			if url and '&n=' in url:
				url = self._unthrottle_url(url, player_id)
			if url and our_format in DASHMP4_FORMAT:
				audio_url = self._extract_dash_audio_format(streaming_formats)
				if audio_url:
					if '&n=' in audio_url:
						audio_url = self._unthrottle_url(audio_url, player_id)
					url += SUBURI + audio_url
			if not url:  # pragma: no cover
				for fmt in streaming_formats:
					itag = str(fmt.get('itag', ''))
					if itag not in IGNORE_VIDEO_FORMAT and self._not_in_fmt(fmt, itag):
						url = fmt.get('url')
						if url:
							break
			if not url:  # pragma: no cover
				url = streaming_formats[0].get('url', '')

		if not url:
			print('[YouTubeVideoUrl] Try manifest url')
			hls_manifest_url = streaming_data.get('hlsManifestUrl')
			if hls_manifest_url:
				url_map = self._extract_from_m3u8(hls_manifest_url)

				# Find the best format from our format priority map
				for our_format in PRIORITY_VIDEO_FORMAT:
					if our_format in url_map:
						url = url_map[our_format]
						break
				# If anything not found, used first in the list if it not in ignore map
				if not url:  # pragma: no cover
					for url_map_key in list(url_map.keys()):
						if url_map_key not in IGNORE_VIDEO_FORMAT:
							url = url_map[url_map_key]
							break
				if not url and url_map:  # pragma: no cover
					url = list(url_map.values())[0]

		if not url:
			reason = playability_status.get('reason')
			if reason:
				subreason = playability_status.get('messages')
				if subreason:
					if isinstance(subreason, list):
						subreason = subreason[0]
					reason += '\n%s' % subreason
			raise RuntimeError(reason)

		return str(url)

	def extract(self, video_id):
		error_message = None
		for _ in range(3):
			try:
				return self._real_extract(video_id)
			except Exception as ex:
				if ex is None:
					print('No supported formats found, trying again!')
				else:
					error_message = str(ex)
					break
		if not error_message:
			error_message = 'No supported formats found in video info!'
		raise RuntimeError(error_message)
