# -*- coding: UTF-8 -*-
# This video extraction code based on youtube-dl: https://github.com/rg3/youtube-dl

from __future__ import print_function
import codecs
import json
import re

from urllib import urlencode
from urllib2 import urlopen, URLError, HTTPError
from urlparse import urljoin, urlparse

from Components.config import config

from . import sslContext
from jsinterp import JSInterpreter


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
	unicode_escape = codecs.getdecoder('unicode_escape')
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
	if not url or not isinstance(url, unicode):
		return None
	url = url.strip()
	return url if re.match(r'^(?:[a-zA-Z][\da-zA-Z.+-]*:)?//', url) else None


def compat_urllib_parse_unquote(string):
	if string == '':
		return string
	res = string.split('%')
	if len(res) == 1:
		return string
	# pct_sequence: contiguous sequence of percent-encoded bytes, decoded
	pct_sequence = b''
	string = res[0]
	for item in res[1:]:
		try:
			if not item:
				raise ValueError
			pct_sequence += item[:2].decode('hex')
			rest = item[2:]
			if not rest:
				# This segment was just a single percent-encoded character.
				# May be part of a sequence of code units, so delay decoding.
				# (Stored in pct_sequence).
				continue
		except ValueError:
			rest = '%' + item
		# Encountered non-percent-encoded characters. Flush the current
		# pct_sequence.
		string += pct_sequence.decode('utf-8', 'replace') + rest
		pct_sequence = b''
	if pct_sequence:
		# Flush the final pct_sequence
		string += pct_sequence.decode('utf-8', 'replace')
	return string


def _parse_qsl(qs):
	qs, _coerce_result = qs, unicode
	pairs = [s2 for s1 in qs.split('&') for s2 in s1.split(';')]
	r = []
	for name_value in pairs:
		if not name_value:
			continue
		nv = name_value.split('=', 1)
		if len(nv) != 2:
			# Handle case of a control-name with no equal sign
			continue
		if len(nv[1]):
			name = nv[0].replace('+', ' ')
			name = compat_urllib_parse_unquote(name)
			name = _coerce_result(name)
			value = nv[1].replace('+', ' ')
			value = compat_urllib_parse_unquote(value)
			value = _coerce_result(value)
			r.append((name, value))
	return r


def compat_parse_qs(qs):
	parsed_result = {}
	pairs = _parse_qsl(qs)
	for name, value in pairs:
		if name in parsed_result:
			parsed_result[name].append(value)
		else:
			parsed_result[name] = [value]
	return parsed_result


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
		""" Returns a tuple (page content as string, URL handle) """
		try:
			if sslContext:
				urlh = urlopen(url, context=sslContext)
			else:
				urlh = urlopen(url)
		except URLError as e:
			raise Exception(e.reason)
		return urlh.read()

	def _download_webpage_handle(self, url_or_request):
		""" Returns a tuple (page content as string, URL handle) """

		# Strip hashes from the URL (#1038)
		if isinstance(url_or_request, (unicode, str)):
			url_or_request = url_or_request.partition('#')[0]

		try:
			if sslContext:
				urlh = urlopen(url_or_request, context=sslContext)
			else:
				urlh = urlopen(url_or_request)
		except URLError as e:
			raise Exception(e.reason)

		content = urlh.read()
		return (content, urlh)

	def _search_regex(self, pattern, string, group=None):
		"""
		Perform a regex search on the given string, using a single or a list of
		patterns returning the first matching group.
		"""
		if isinstance(pattern, (str, unicode, type(re.compile('')))):
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
			player_url = urljoin('https://www.youtube.com', player_url)
		try:
			func = self._extract_signature_function(player_url)
			return func(s)
		except Exception as e:
			raise Exception('Signature extraction failed!\n%s' % str(e))

	def _extract_player_info(self, player_url):
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
				r'\b(?P<sig>[a-zA-Z0-9$]{2})\s*=\s*function\(\s*a\s*\)\s*{\s*a\s*=\s*a\.split\(\s*""\s*\)',
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
			urls = filter(lambda l: l and not l.startswith('#'), lines)
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
				return json.loads(uppercase_escape(config))

	def extract(self, video_id):
		gl = config.plugins.YouTube.searchRegion.value
		hl = config.plugins.YouTube.searchLanguage.value

		url = 'https://www.youtube.com/watch?v=%s&gl=%s&hl=%s&has_verified=1&bpctr=9999999999' % (video_id, gl, hl)

		# Get video webpage
		video_webpage, urlh = self._download_webpage_handle(url)

		qs = compat_parse_qs(urlparse(urlh.geturl()).query)
		video_id = qs.get('v', [None])[0] or video_id

		if not video_webpage:
			raise Exception('Video webpage not found!')

		def extract_player_response(player_response):
			if not player_response:
				return
			pl_response = json.loads(player_response)
			if isinstance(pl_response, dict):
				return pl_response

		is_live = None
		player_response = {}

		# Get video info
		video_info = {}
		embed_webpage = None
		if re.search(r'player-age-gate-content">', video_webpage) is not None:
			age_gate = True
			# We simulate the access to the video from www.youtube.com/v/{video_id}
			# this can be viewed without login into Youtube
			url = 'https://www.youtube.com/embed/%s' % video_id
			embed_webpage = self._download_webpage(url)
			data = urlencode({
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
				args = ytplayer_config['args']
				if args.get('url_encoded_fmt_stream_map'):
					# Convert to the same format returned by compat_parse_qs
					video_info = dict((k, [v]) for k, v in args.items())
				if args.get('livestream') == '1' or args.get('live_playback') == 1:
					is_live = True
				if not player_response:
					player_response = extract_player_response(args.get('player_response'))

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
					url_map['url'] = url_or_none(try_get(url_map['url_data'], lambda x: x['url'][0], unicode))
					if not url_map['url']:
						continue
				else:
					url_map['url_data'] = compat_parse_qs(urlparse(url_map['url']).query)

				stream_type = try_get(url_map['url_data'], lambda x: x['stream_type'][0])
				# Unsupported FORMAT_STREAM_TYPE_OTF
				if stream_type == 3:
					continue

				url_map['format_id'] = fmt.get('itag') or url_map['url_data']['itag'][0]
				if not url_map['format_id']:
					continue
				url_map['format_id'] = unicode(url_map['format_id'])

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
						ASSETS_RE = r'"assets":.+?"js":\s*("[^"]+")'
						jsplayer_url_json = self._search_regex(ASSETS_RE,
							embed_webpage if age_gate else video_webpage)
						if not jsplayer_url_json and not age_gate:
							# We need the embed website after all
							if embed_webpage is None:
								embed_url = 'https://www.youtube.com/embed/%s' % video_id
								embed_webpage = self._download_webpage(embed_url)
							jsplayer_url_json = self._search_regex(ASSETS_RE, embed_webpage)

						player_url = json.loads(jsplayer_url_json)
						if player_url is None:
							player_url_json = self._search_regex(
								r'ytplayer\.config.*?"url"\s*:\s*("[^"]+")',
								video_webpage)
							player_url = json.loads(player_url_json)

					if 'sig' in url_map['url_data']:
						url += '&signature=' + url_map['url_data']['sig'][0]
					elif 's' in url_map['url_data']:
						encrypted_sig = url_map['url_data']['s'][0]
						signature = self._decrypt_signature(encrypted_sig, player_url)
						sp = try_get(url_map['url_data'], lambda x: x['sp'][0], unicode) or 'signature'
						url += '&%s=%s' % (sp, signature)
				if 'ratebypass' not in url_map['url']:
					url += '&ratebypass=yes'
		else:
			manifest_url = (
				url_or_none(try_get(
					player_response,
					lambda x: x['streamingData']['hlsManifestUrl'],
					unicode))
				or url_or_none(try_get(
					video_info, lambda x: x['hlsvp'][0], unicode)))
			if manifest_url:
				url_map = self._extract_from_m3u8(manifest_url)

				# Find the best format from our format priority map
				for our_format in PRIORITY_VIDEO_FORMAT:
					if url_map.get(our_format):
						url = url_map[our_format]
						break
				# If anything not found, used first in the list if it not in ignore map
				if not url:
					for url_map_key in url_map.keys():
						if url_map_key not in IGNORE_VIDEO_FORMAT:
							url = url_map[url_map_key]
							break
				if not url:
					url = url_map.values()[0]
		if not url:
			error_message = clean_html(try_get(
					player_response,
					lambda x: x['playabilityStatus']['reason'],
					unicode))
			if not error_message:
				error_message = clean_html(try_get(
					video_info, lambda x: x['reason'][0], unicode))
			if not error_message and try_get(
					player_response,
					lambda x: x['streamingData']['licenseInfos'],
					unicode):
				error_message = 'This video is DRM protected!'
			if not error_message:
				error_message = 'No supported formats found in video info!'
			raise Exception(error_message)

		return str(url)
