# -*- coding: UTF-8 -*-
# This video extraction code based on youtube-dl: https://github.com/ytdl-org/youtube-dl

from __future__ import print_function

import re

from json import loads

from Components.config import config

from .compat import compat_parse_qs
from .compat import compat_ssl_urlopen
from .compat import compat_str
from .compat import compat_urlencode
from .compat import compat_URLError
from .compat import compat_urljoin
from .compat import compat_urlparse
from .compat import compat_urlunparse
from .jsinterp import JSInterpreter


PRIORITY_VIDEO_FORMAT = []


def createPriorityFormats():
	global PRIORITY_VIDEO_FORMAT
	video_format = {'38': ['38', '266', '264', '138', '313', '315', '272', '308'],  # 4096x3072
			'37': ['37', '96', '301', '137', '299', '248', '303', '271'],  # 1920x1080
			'22': ['22', '95', '300', '136', '298'],  # 1280x720
			'35': ['35', '59', '78', '94', '135', '212'],  # 854x480
			'18': ['18', '93', '34', '6', '134'],  # 640x360
			'5': ['5', '36', '92', '132', '133'],  # 400x240
			'17': ['17', '91', '13', '151', '160']}  # 176x144
	for itag in ['17', '5', '18', '35', '22', '37', '38']:
		PRIORITY_VIDEO_FORMAT = video_format[itag] + PRIORITY_VIDEO_FORMAT
		if itag == config.plugins.YouTube.maxResolution.value:
			break


createPriorityFormats()


DASHMP4_FORMAT = ['133', '134', '135', '136', '137', '138',
		'160', '212', '264', '266', '298', '299',
		'248', '303', '271', '313', '315', '272', '308']

IGNORE_VIDEO_FORMAT = ['43', '44', '45', '46',  # webm
		'82', '83', '84', '85',  # 3D
		'100', '101', '102',  # 3D
		'167', '168', '169',  # webm
		'170', '171', '172',  # webm
		'218', '219',  # webm
		'242', '243', '244', '245', '246', '247',  # webm
		'249', '250', '251',  # webm
		'302']  # webm


def try_get(src, getter, expected_type=None):
	if not isinstance(getter, (list, tuple)):
		getter = [getter]
	for get in getter:
		try:
			v = get(src)
		except (AttributeError, KeyError, TypeError, IndexError):
			pass
		else:
			if expected_type is None or isinstance(v, expected_type):
				return v


def url_or_none(url):
	if not url or not isinstance(url, compat_str):
		return None
	url = url.strip()
	return url if re.match(r'^(?:[a-zA-Z][\da-zA-Z.+-]*:)?//', url) else None


def clean_html(html):
	"""Clean an HTML snippet into a readable string"""

	if html is None:  # Convenience for sanitizing descriptions etc.
		return html

	# Newline vs <br />
	html = html.replace('\n', ' ')
	html = re.sub(r'(?u)\s*<\s*br\s*/?\s*>\s*', '\n', html)
	html = re.sub(r'(?u)<\s*/\s*p\s*>\s*<\s*p[^>]*>', '\n', html)
	# Strip html tags
	html = re.sub('<.*?>', '', html)
	return html.strip()


class YouTubeVideoUrl():
	def __init__(self):
		self._code_cache = {}
		self._player_cache = {}
		self.use_dash_mp4 = []

	def _download_webpage(self, url, query={}):
		""" Return the data of the page as a string """
		content, urlh = self._download_webpage_handle(url, query)
		return content

	@staticmethod
	def _guess_encoding_from_content(content_type, webpage_bytes):
		m = re.match(r'[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+\s*;\s*charset=(.+)', content_type)
		if m:
			encoding = m.group(1)
		else:
			m = re.search(br'<meta[^>]+charset=[\'"]?([^\'")]+)[ /\'">]',
					webpage_bytes[:1024])
			if m:
				encoding = m.group(1).decode('ascii')
			elif webpage_bytes.startswith(b'\xff\xfe'):
				encoding = 'utf-16'
			else:
				encoding = 'utf-8'

		return encoding

	def _download_webpage_handle(self, url_or_request, query={}):
		""" Returns a tuple (page content as string, URL handle) """

		# Strip hashes from the URL (#1038)
		if isinstance(url_or_request, (compat_str, str)):
			url_or_request = url_or_request.partition('#')[0]

		if query:
			parsed_url = compat_urlparse(url_or_request)
			qs = compat_parse_qs(parsed_url.query)
			qs.update(query)
			url_or_request = compat_urlunparse(parsed_url._replace(
					query=compat_urlencode(qs, True)))

		try:
			urlh = compat_ssl_urlopen(url_or_request)
		except compat_URLError as e:
			raise Exception(e.reason)

		content_type = urlh.headers.get('Content-Type', '')
		webpage_bytes = urlh.read()
		encoding = self._guess_encoding_from_content(content_type, webpage_bytes)

		try:
			content = webpage_bytes.decode(encoding, 'replace')
		except Exception:
			content = webpage_bytes.decode('utf-8', 'replace')

		return (content, urlh)

	@staticmethod
	def _search_regex(pattern, string, group=None):
		"""
		Perform a regex search on the given string, using a single or a list of
		patterns returning the first matching group.
		"""
		if isinstance(pattern, (str, compat_str, type(re.compile('')))):
			mobj = re.search(pattern, string, 0)
		else:
			for p in pattern:
				mobj = re.search(p, string, 0)
				if mobj:
					break
		if mobj:
			if group is None:
				# return the first matching group
				return next(g for g in mobj.groups() if g is not None)
			else:
				return mobj.group(group)
		else:
			print('[YouTubeVideoUrl] unable extract pattern from string!')
			return ''

	def _decrypt_signature(self, s, player_url):
		"""Turn the encrypted s field into a working signature"""

		if player_url is None:
			raise Exception('Cannot decrypt signature without player_url!')

		if player_url[:2] == '//':
			player_url = 'https:' + player_url
		elif not re.match(r'https?://', player_url):
			player_url = compat_urljoin('https://www.youtube.com', player_url)

		try:
			player_id = (player_url, self._signature_cache_id(s))
			if player_id not in self._player_cache:
				self._player_cache[player_id] = self._extract_signature_function(player_url)
			func = self._player_cache[player_id]
			return func(s)
		except Exception as e:
			raise Exception('Signature extraction failed!\n%s' % str(e))

	def _signature_cache_id(self, example_sig):
		""" Return a string representation of a signature """
		return '.'.join(compat_str(len(part)) for part in example_sig.split('.'))

	def _extract_signature_function(self, player_url):
		_PLAYER_INFO_RE = (
			r'/s/player/(?P<id>[a-zA-Z0-9_-]{8,})/player',
			r'/(?P<id>[a-zA-Z0-9_-]{8,})/player(?:_ias\.vflset(?:/[a-zA-Z]{2,3}_[a-zA-Z]{2,3})?|-plasma-ias-(?:phone|tablet)-[a-z]{2}_[A-Z]{2}\.vflset)/base\.js$',
			r'\b(?P<id>vfl[a-zA-Z0-9_-]+)\b.*?\.js$',
		)

		for player_re in _PLAYER_INFO_RE:
			id_m = re.search(player_re, player_url)
			if id_m:
				break
		else:
			raise Exception('Cannot identify player %r' % player_url)

		player_id = id_m.group('id')

		if player_id not in self._code_cache:
			self._code_cache[player_id] = self._download_webpage(player_url)
		jscode = self._code_cache[player_id]

		funcname = self._search_regex(
				(r'\b[cs]\s*&&\s*[adf]\.set\([^,]+\s*,\s*encodeURIComponent\s*\(\s*(?P<sig>[a-zA-Z0-9$]+)\(',
				r'\b[a-zA-Z0-9]+\s*&&\s*[a-zA-Z0-9]+\.set\([^,]+\s*,\s*encodeURIComponent\s*\(\s*(?P<sig>[a-zA-Z0-9$]+)\(',
				r'\bm=(?P<sig>[a-zA-Z0-9$]{2})\(decodeURIComponent\(h\.s\)\)',
				r'\bc&&\(c=(?P<sig>[a-zA-Z0-9$]{2})\(decodeURIComponent\(c\)\)',
				r'(?:\b|[^a-zA-Z0-9$])(?P<sig>[a-zA-Z0-9$]{2})\s*=\s*function\(\s*a\s*\)\s*{\s*a\s*=\s*a\.split\(\s*""\s*\);[a-zA-Z0-9$]{2}\.[a-zA-Z0-9$]{2}\(a,\d+\)',
				r'(?:\b|[^a-zA-Z0-9$])(?P<sig>[a-zA-Z0-9$]{2})\s*=\s*function\(\s*a\s*\)\s*{\s*a\s*=\s*a\.split\(\s*""\s*\)',
				r'(?P<sig>[a-zA-Z0-9$]+)\s*=\s*function\(\s*a\s*\)\s*{\s*a\s*=\s*a\.split\(\s*""\s*\)',
				# Obsolete patterns
				r'(["\'])signature\1\s*,\s*(?P<sig>[a-zA-Z0-9$]+)\(',
				r'\.sig\|\|(?P<sig>[a-zA-Z0-9$]+)\(',
				r'yt\.akamaized\.net/\)\s*\|\|\s*.*?\s*[cs]\s*&&\s*[adf]\.set\([^,]+\s*,\s*(?:encodeURIComponent\s*\()?\s*(?P<sig>[a-zA-Z0-9$]+)\(',
				r'\b[cs]\s*&&\s*[adf]\.set\([^,]+\s*,\s*(?P<sig>[a-zA-Z0-9$]+)\(',
				r'\b[a-zA-Z0-9]+\s*&&\s*[a-zA-Z0-9]+\.set\([^,]+\s*,\s*(?P<sig>[a-zA-Z0-9$]+)\(',
				r'\bc\s*&&\s*a\.set\([^,]+\s*,\s*\([^)]*\)\s*\(\s*(?P<sig>[a-zA-Z0-9$]+)\(',
				r'\bc\s*&&\s*[a-zA-Z0-9]+\.set\([^,]+\s*,\s*\([^)]*\)\s*\(\s*(?P<sig>[a-zA-Z0-9$]+)\(',
				r'\bc\s*&&\s*[a-zA-Z0-9]+\.set\([^,]+\s*,\s*\([^)]*\)\s*\(\s*(?P<sig>[a-zA-Z0-9$]+)\('),
				jscode, group='sig')
		jsi = JSInterpreter(jscode)
		initial_function = jsi.extract_function(funcname)
		return lambda s: initial_function([s])

	def _extract_from_m3u8(self, manifest_url):
		url_map = {}

		def _get_urls(_manifest):
			lines = _manifest.split('\n')
			urls = [x for x in lines if x and not x.startswith('#')]
			return urls

		manifest = self._download_webpage(manifest_url)
		formats_urls = _get_urls(manifest)
		for format_url in formats_urls:
			itag = self._search_regex(r'itag/(\d+?)/', format_url)
			url_map[itag] = format_url
		return url_map

	@staticmethod
	def _parse_json(json_string):
		try:
			return loads(json_string)
		except ValueError:
			print('[YouTubeVideoUrl] Failed to parse JSON')

	def _extract_yt_initial_variable(self, webpage, regex):
		_YT_INITIAL_BOUNDARY_RE = r'(?:var\s+meta|</script|\n)'
		return self._parse_json(self._search_regex(
			(r'%s\s*%s' % (regex, _YT_INITIAL_BOUNDARY_RE), regex), webpage))

	def _extract_fmt_url(self, fmt, webpage):
		fmt_url = fmt.get('url', '')
		if not fmt_url:
			sc = compat_parse_qs(fmt.get('signatureCipher'))
			fmt_url = try_get(sc, lambda x: x['url'][0])
			encrypted_sig = try_get(sc, lambda x: x['s'][0])
			if not (sc and fmt_url and encrypted_sig):
				return ''
			player_url = self._search_regex(
					r'"(?:PLAYER_JS_URL|jsUrl)"\s*:\s*"([^"]+)"',
					webpage)
			if not player_url:
				return ''
			signature = self._decrypt_signature(sc['s'][0], player_url)
			sp = try_get(sc, lambda x: x['sp'][0]) or 'signature'
			fmt_url += '&%s=%s' % (sp, signature)
		return fmt_url

	def _not_in_fmt(self, fmt):
		return not (fmt.get('targetDurationSec') or
				fmt.get('drmFamilies') or
				fmt.get('type') == 'FORMAT_STREAM_TYPE_OTF' or
				str(fmt.get('itag', '')) in self.use_dash_mp4)

	def _extract_fmt_video_format(self, streaming_formats, webpage):
		""" Find the best format from our format priority map """
		print('[YouTubeVideoUrl] Try fmt url')
		for our_format in PRIORITY_VIDEO_FORMAT:
			for fmt in streaming_formats:
				if str(fmt.get('itag', '')) == our_format and self._not_in_fmt(fmt):
					url = self._extract_fmt_url(fmt, webpage)
					if url:
						print('[YouTubeVideoUrl] Found fmt url')
						return url, our_format
		return '', ''

	def _extract_dash_audio_format(self, streaming_formats, webpage):
		""" If DASH MP4 video add link also on Dash MP4 Audio """
		print('[YouTubeVideoUrl] Try fmt audio url')
		for our_format in ['141', '140', '139',
				'258', '265', '325', '328']:
			for fmt in streaming_formats:
				if str(fmt.get('itag', '')) == our_format and self._not_in_fmt(fmt):
					url = self._extract_fmt_url(fmt, webpage)
					if url:
						print('[YouTubeVideoUrl] Found fmt audio url')
						return url
		return ''

	def _real_extract(self, video_id):
		webpage = self._download_webpage(
				'https://www.youtube.com/watch?v=%s&bpctr=9999999999' % video_id)
		if not webpage:
			raise Exception('Video webpage not found for!')

		player_response = self._extract_yt_initial_variable(
				webpage, r'ytInitialPlayerResponse\s*=\s*({.+?})\s*;')
		if not player_response:
			# I did not find a video in which the player response was not found
			# and should be used api call
			raise Exception('Player response not found!')

		playability_status = player_response.get('playabilityStatus') or {}

		trailer_video_id = try_get(playability_status,
				lambda x: x['errorScreen']['playerLegacyDesktopYpcTrailerRenderer']['trailerVideoId'],
				compat_str)
		if trailer_video_id:
			print('[YouTubeVideoUrl] Trailer video')
			return str(trailer_video_id)

		if playability_status.get('reason') == 'Sign in to confirm your age':
			print('[YouTubeVideoUrl] Age gate content')
			pr = self._parse_json(try_get(compat_parse_qs(
					self._download_webpage(
							'https://www.youtube.com/get_video_info',
							query={'video_id': video_id,
									'eurl': 'https://youtube.googleapis.com/v/%s' % video_id})),
							lambda x: x['player_response'][0],
							compat_str) or '{}')
			if pr:
				player_response = pr

		url = ''
		streaming_data = player_response.get('streamingData') or {}
		is_live = try_get(player_response, lambda x: x['videoDetails']['isLive'])
		streaming_formats = streaming_data.get('formats') or []

		if not is_live and streaming_formats:
			streaming_formats.extend(streaming_data.get('adaptiveFormats') or [])
			# If priority format changed in config, recreate priority list
			if PRIORITY_VIDEO_FORMAT[0] != config.plugins.YouTube.maxResolution.value:
				createPriorityFormats()

			if config.plugins.YouTube.useDashMP4.value:
				self.use_dash_mp4 = []
			else:
				print('[YouTubeVideoUrl] skip DASH MP4 format')
				self.use_dash_mp4 = DASHMP4_FORMAT

			url, our_format = self._extract_fmt_video_format(streaming_formats, webpage)
			if url and our_format in DASHMP4_FORMAT:
				audio_url = self._extract_dash_audio_format(streaming_formats, webpage)
				if audio_url:
					url += '&suburi=%s' % audio_url
			if not url:
				for fmt in streaming_formats:
					if str(fmt.get('itag', '')) not in IGNORE_VIDEO_FORMAT and self._not_in_fmt(fmt):
						url = self._extract_fmt_url(fmt, webpage)
						if url:
							break
			if not url:
				url = self._extract_fmt_url(streaming_formats[0], webpage)

		if not url:
			print('[YouTubeVideoUrl] Try manifest url')
			hls_manifest_url = streaming_data.get('hlsManifestUrl')
			if hls_manifest_url:
				url_map = self._extract_from_m3u8(hls_manifest_url)

				# Find the best format from our format priority map
				for our_format in PRIORITY_VIDEO_FORMAT:
					if url_map.get(our_format):
						url = url_map[our_format]
						break
				# If anything not found, used first in the list if it not in ignore map
				if not url:
					for url_map_key in list(url_map.keys()):
						if url_map_key not in IGNORE_VIDEO_FORMAT:
							url = url_map[url_map_key]
							break
				if not url:
					url = list(url_map.values())[0]

		if not url:
			if streaming_data.get('licenseInfos'):
				raise Exception('This video is DRM protected!')
			pemr = try_get(playability_status,
				lambda x: x['errorScreen']['playerErrorMessageRenderer'],
				dict) or {}

			def get_text(x):
				if x:
					return x.get('simpleText') or ''.join([r['text'] for r in x['runs']])

			reason = get_text(pemr.get('reason')) or playability_status.get('reason')
			if reason:
				subreason = pemr.get('subreason')
				if subreason:
					subreason = clean_html(get_text(subreason))
					reason += '\n%s' % subreason
			raise Exception(reason)

		return str(url)

	def extract(self, video_id):
		error_message = None
		for retry in range(3):
			try:
				return self._real_extract(video_id)
			except Exception as ex:
				if str(ex) == 'None':
					print('No supported formats found, trying again!')
				else:
					error_message = str(ex)
					break
		if not error_message:
			error_message = 'No supported formats found in video info!'
		raise Exception(error_message)
