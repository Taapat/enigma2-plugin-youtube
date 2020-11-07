# -*- coding: UTF-8 -*-
# This video extraction code based on youtube-dl: https://github.com/rg3/youtube-dl

from __future__ import print_function

import re

from codecs import getdecoder
from json import loads

from Components.config import config

from .compat import compat_parse_qs
from .compat import compat_ssl_urlopen
from .compat import compat_str
from .compat import compat_urlencode
from .compat import compat_URLError
from .compat import compat_urljoin
from .compat import compat_urlparse
from .jsinterp import JSInterpreter


PRIORITY_VIDEO_FORMAT = []


def createPriorityFormats():
	global PRIORITY_VIDEO_FORMAT
	video_format = {
			'38':['38', '266', '264', '138', '313', '315', '272', '308'],  # 4096x3072
			'37':['37', '96', '301', '137', '299', '248', '303', '271'],  # 1920x1080
			'22':['22', '95', '300', '136', '298'],  # 1280x720
			'35':['35', '59', '78', '94', '135', '212'],  # 854x480
			'18':['18', '93', '34', '6', '134'],  # 640x360
			'5':['5', '36', '92', '132', '133'],  # 400x240
			'17':['17', '91', '13', '151', '160']  # 176x144
		}
	for itag in ['17', '5', '18', '35', '22', '37', '38']:
		PRIORITY_VIDEO_FORMAT = video_format[itag] + PRIORITY_VIDEO_FORMAT
		if itag == config.plugins.YouTube.maxResolution.value:
			break

createPriorityFormats()


DASHMP4_FORMAT = [
		'133', '134', '135', '136', '137', '138',
		'160', '212', '264', '266', '298', '299',
		'248', '303', '271', '313', '315', '272', '308'
	]

IGNORE_VIDEO_FORMAT = [
		'43', '44', '45', '46',  # webm
		'82', '83', '84', '85',  # 3D
		'100', '101', '102',  # 3D
		'167', '168', '169',  # webm
		'170', '171', '172',  # webm
		'218', '219',  # webm
		'242', '243', '244', '245', '246', '247',  # webm
		'249', '250', '251',  # webm
		'302'  # webm
	]


def uppercase_escape(s):
	unicode_escape = getdecoder('unicode_escape')
	return re.sub(
		r'\\U[0-9a-fA-F]{8}',
		lambda m: unicode_escape(m.group(0))[0],
		s)


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

	def _download_webpage(self, url):
		""" Return the data of the page as a string """
		content, urlh = self._download_webpage_handle(url)
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

	def _download_webpage_handle(self, url_or_request):
		""" Returns a tuple (page content as string, URL handle) """

		# Strip hashes from the URL (#1038)
		if isinstance(url_or_request, (compat_str, str)):
			url_or_request = url_or_request.partition('#')[0]

		try:
			urlh = compat_ssl_urlopen(url_or_request)
		except compat_URLError as e:
			raise Exception(e.reason)

		content_type = urlh.headers.get('Content-Type', '')
		webpage_bytes = urlh.read()
		encoding = self._guess_encoding_from_content(content_type, webpage_bytes)

		try:
			content = webpage_bytes.decode(encoding, 'replace')
		except:
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

	def _html_search_regex(self, pattern, string, group=None):
		"""
		Like _search_regex, but strips HTML tags and unescapes entities.
		"""
		res = self._search_regex(pattern, string, group)
		if res:
			return clean_html(res).strip()
		else:
			return res

	def _html_search_meta(self, name, html):
		if not isinstance(name, (list, tuple)):
			name = [name]
		return self._html_search_regex(
			[self._meta_regex(n) for n in name],
			html, group='content')

	@staticmethod
	def _meta_regex(prop):
		return r'''(?isx)<meta
				(?=[^>]+(?:itemprop|name|property|id|http-equiv)=(["\']?)%s\1)
				[^>]+?content=(["\'])(?P<content>.*?)\2''' % re.escape(prop)

	def _decrypt_signature(self, s, player_url):
		"""Turn the encrypted s field into a working signature"""

		if player_url is None:
			raise Exception('Cannot decrypt signature without player_url!')

		if player_url[:2] == '//':
			player_url = 'https:' + player_url
		elif not re.match(r'https?://', player_url):
			player_url = compat_urljoin('https://www.youtube.com', player_url)
		try:
			func = self._extract_signature_function(player_url)
			return func(s)
		except Exception as e:
			raise Exception('Signature extraction failed!\n%s' % str(e))

	@staticmethod
	def _extract_player_info(player_url):
		_PLAYER_INFO_RE = (
			r'/(?P<id>[a-zA-Z0-9_-]{8,})/player_ias\.vflset(?:/[a-zA-Z]{2,3}_[a-zA-Z]{2,3})?/base\.(?P<ext>[a-z]+)$',
			r'\b(?P<id>vfl[a-zA-Z0-9_-]+)\b.*?\.(?P<ext>[a-z]+)$',
		)

		for player_re in _PLAYER_INFO_RE:
			id_m = re.search(player_re, player_url)
			if id_m:
				break
		else:
			raise Exception('Cannot identify player %r' % player_url)
		return id_m.group('ext')

	def _extract_signature_function(self, player_url):
		player_type = self._extract_player_info(player_url)
		code = self._download_webpage(player_url)
		if player_type == 'js':
			return self._parse_sig_js(code)
		elif player_type == 'swf':
			raise Exception('Shockwave Flash player is no longer supported!')
		else:
			raise Exception('Invalid player type %r!' % player_type)

	def _parse_sig_js(self, jscode):
		funcname = self._search_regex(
				(r'\b[cs]\s*&&\s*[adf]\.set\([^,]+\s*,\s*encodeURIComponent\s*\(\s*(?P<sig>[a-zA-Z0-9$]+)\(',
				r'\b[a-zA-Z0-9]+\s*&&\s*[a-zA-Z0-9]+\.set\([^,]+\s*,\s*encodeURIComponent\s*\(\s*(?P<sig>[a-zA-Z0-9$]+)\(',
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
			urls = [l for l in lines if l and not l.startswith('#')]
			return urls

		manifest = self._download_webpage(manifest_url)
		formats_urls = _get_urls(manifest)
		for format_url in formats_urls:
			itag = self._search_regex(r'itag/(\d+?)/', format_url)
			url_map[itag] = format_url
		return url_map

	def _get_ytplayer_config(self, webpage):
		# User data may contain arbitrary character sequences that may affect
		# JSON extraction with regex, e.g. when '};' is contained the second
		# regex won't capture the whole JSON. Yet working around by trying more
		# concrete regex first keeping in mind proper quoted string handling
		# to be implemented in future that will replace this workaround (see
		# https://github.com/rg3/youtube-dl/issues/7468,
		# https://github.com/rg3/youtube-dl/pull/7599)
		patterns = [
			r';ytplayer\.config\s*=\s*({.+?});ytplayer',
			r';ytplayer\.config\s*=\s*({.+?});',
		]
		for pattern in patterns:
			config = self._search_regex(pattern, webpage)
			if config:
				return loads(uppercase_escape(config))

	def extract(self, video_id):
		gl = config.plugins.YouTube.searchRegion.value
		hl = config.plugins.YouTube.searchLanguage.value

		url = 'https://www.youtube.com/watch?v=%s&gl=%s&hl=%s&has_verified=1&bpctr=9999999999' % (video_id, gl, hl)

		# Get video webpage
		video_webpage, urlh = self._download_webpage_handle(url)

		qs = compat_parse_qs(compat_urlparse(urlh.geturl()).query)
		video_id = qs.get('v', [None])[0] or video_id

		if not video_webpage:
			raise Exception('Video webpage not found!')

		def extract_player_response(player_response):
			if not player_response:
				return
			pl_response = loads(player_response)
			if isinstance(pl_response, dict):
				return pl_response

		is_live = None
		player_response = {}

		# Get video info
		video_info = {}
		embed_webpage = None
		if re.search(r'player-age-gate-content">', video_webpage) is not None or self._html_search_meta('og:restrictions:age', video_webpage) == "18+":
			age_gate = True
			# We simulate the access to the video from www.youtube.com/v/{video_id}
			# this can be viewed without login into Youtube
			url = 'https://www.youtube.com/embed/%s' % video_id
			embed_webpage = self._download_webpage(url)
			data = compat_urlencode({
					'video_id': video_id,
					'eurl': 'https://youtube.googleapis.com/v/' + video_id,
					'sts': self._search_regex(r'"sts"\s*:\s*(\d+)', embed_webpage),
				})
			video_info_url = 'https://www.youtube.com/get_video_info?' + data
			try:
				video_info_webpage = self._download_webpage(video_info_url)
			except ExtractorError:
				video_info_webpage = None
			if video_info_webpage:
				video_info = compat_parse_qs(video_info_webpage)
				pl_response = video_info.get('player_response', [None])[0]
				player_response = extract_player_response(pl_response)
		else:
			age_gate = False
			args = {}
			# Try looking directly into the video webpage
			ytplayer_config = self._get_ytplayer_config(video_webpage)
			if ytplayer_config:
				args = ytplayer_config.get("args")
				if args is not None:
					if args.get('url_encoded_fmt_stream_map') or args.get('hlsvp'):
						# Convert to the same format returned by compat_parse_qs
						video_info = dict((k, [v]) for k, v in list(args.items()))
					if args.get('livestream') == '1' or args.get('live_playback') == 1:
						is_live = True
					if not player_response:
						player_response = extract_player_response(args.get('player_response'))
				elif not player_response:
					player_response = ytplayer_config

		video_details = try_get(
			player_response, lambda x: x['videoDetails'], dict) or {}

		if is_live is None:
			is_live = video_details.get('isLive')

		# Start extracting information
		url = ''
		streaming_formats = try_get(player_response, lambda x: x['streamingData']['formats'], list) or []
		streaming_formats.extend(try_get(player_response, lambda x: x['streamingData']['adaptiveFormats'], list) or [])

		if 'conn' in video_info and video_info['conn'][0][:4] == 'rtmp':
			url = video_info['conn'][0]
		elif not is_live and (streaming_formats or len(video_info.get('url_encoded_fmt_stream_map', [''])[0]) >= 1 or \
			len(video_info.get('adaptive_fmts', [''])[0]) >= 1):
			encoded_url_map = video_info.get('url_encoded_fmt_stream_map', [''])[0] + \
				',' + video_info.get('adaptive_fmts', [''])[0]
			if 'rtmpe%3Dyes' in encoded_url_map:
				raise Exception('rtmpe downloads are not supported, see https://github.com/rg3/youtube-dl/issues/343')

			formats = []
			url_map_str = []

			for fmt in streaming_formats:
				url_map = {
						'url': None,
						'format_id': None,
						'cipher': None,
						'url_data': None
					}
				if fmt.get('drmFamilies') or fmt.get('drm_families'):
					continue
				url_map['url'] = url_or_none(fmt.get('url'))

				if not url_map['url']:
					url_map['cipher'] = fmt.get('cipher') or fmt.get('signatureCipher')
					if not url_map['cipher']:
						continue
					url_map['url_data'] = compat_parse_qs(url_map['cipher'])
					url_map['url'] = url_or_none(try_get(url_map['url_data'], lambda x: x['url'][0], compat_str))
					if not url_map['url']:
						continue
				else:
					url_map['url_data'] = compat_parse_qs(compat_urlparse(url_map['url']).query)

				stream_type = try_get(url_map['url_data'], lambda x: x['stream_type'][0])
				# Unsupported FORMAT_STREAM_TYPE_OTF
				if stream_type == 3:
					continue

				url_map['format_id'] = fmt.get('itag') or url_map['url_data']['itag'][0]
				if not url_map['format_id']:
					continue
				url_map['format_id'] = compat_str(url_map['format_id'])

				formats.append(url_map)

			# If priority format changed in config, recreate priority list
			if PRIORITY_VIDEO_FORMAT[0] != config.plugins.YouTube.maxResolution.value:
				createPriorityFormats()
			# Find the best format from our format priority map
			for our_format in PRIORITY_VIDEO_FORMAT:
				for url_map in formats:
					if url_map['format_id'] == our_format:
						url_map_str.append(url_map)
						break
				if url_map_str:
					break
			# If DASH MP4 video add link also on Dash MP4 Audio
			if url_map_str and our_format in DASHMP4_FORMAT:
				for our_format in ['141', '140', '139',
						'258', '265', '325', '328']:
					for url_map in formats:
						if url_map['format_id'] == our_format:
							url_map_str.append(url_map)
							break
					if len(url_map_str) > 1:
						break
			# If anything not found, used first in the list if it not in ignore map
			if not url_map_str:
				for url_map in formats:
					if url_map['format_id'] not in IGNORE_VIDEO_FORMAT:
						url_map_str.append(url_map)
						break
			if not url_map_str and formats:
				url_map_str.append(formats[0])

			for url_map in url_map_str:
				if url:
					url += '&suburi='
				url += url_map['url']

				if url_map['cipher']:
					if 's' in url_map['url_data']:
						ASSETS_RE = (
							r'<script[^>]+\bsrc=("[^"]+")[^>]+\bname=["\']player_ias/base',
							r'"jsUrl"\s*:\s*("[^"]+")',
							r'"assets":.+?"js":\s*("[^"]+")')
						jsplayer_url_json = self._search_regex(ASSETS_RE,
							embed_webpage if age_gate else video_webpage)
						if not jsplayer_url_json and not age_gate:
							# We need the embed website after all
							if embed_webpage is None:
								embed_url = 'https://www.youtube.com/embed/%s' % video_id
								embed_webpage = self._download_webpage(embed_url)
							jsplayer_url_json = self._search_regex(ASSETS_RE, embed_webpage)

						player_url = loads(jsplayer_url_json)
						if player_url is None:
							player_url_json = self._search_regex(
								r'ytplayer\.config.*?"url"\s*:\s*("[^"]+")',
								video_webpage)
							player_url = loads(player_url_json)

					if 'sig' in url_map['url_data']:
						url += '&signature=' + url_map['url_data']['sig'][0]
					elif 's' in url_map['url_data']:
						encrypted_sig = url_map['url_data']['s'][0]
						signature = self._decrypt_signature(encrypted_sig, player_url)
						sp = try_get(url_map['url_data'], lambda x: x['sp'][0], compat_str) or 'signature'
						url += '&%s=%s' % (sp, signature)
				if 'ratebypass' not in url_map['url']:
					url += '&ratebypass=yes'
		else:
			manifest_url = (
				url_or_none(try_get(
					player_response,
					lambda x: x['streamingData']['hlsManifestUrl'],
					compat_str))
				or url_or_none(try_get(
					video_info, lambda x: x['hlsvp'][0], compat_str)))
			if manifest_url:
				url_map = self._extract_from_m3u8(manifest_url)

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
			error_message = clean_html(try_get(
					player_response,
					lambda x: x['playabilityStatus']['reason'],
					compat_str))
			if not error_message:
				error_message = clean_html(try_get(
					video_info, lambda x: x['reason'][0], compat_str))
			if not error_message and try_get(
					player_response,
					lambda x: x['streamingData']['licenseInfos'],
					compat_str):
				error_message = 'This video is DRM protected!'
			if not error_message:
				error_message = 'No supported formats found in video info!'
			raise Exception(error_message)

		return str(url)
