# -*- coding: UTF-8 -*-
# This video extraction code based on youtube-dl: https://github.com/rg3/youtube-dl

import codecs
import json
import re

from urllib import urlencode
from urllib2 import urlopen, URLError
from urlparse import urljoin

from Components.config import config

from . import sslContext
from jsinterp import JSInterpreter
from swfinterp import SWFInterpreter


PRIORITY_VIDEO_FORMAT = []


def createPriorityFormats():
	global PRIORITY_VIDEO_FORMAT
	video_format = {
			'38':['38'],  # 4096x3072
			'37':['37', '137', '299', '96'],  # 1920x1080
			'22':['22', '136', '298', '95'],  # 1280x720
			'35':['35', '135', '94'],  # 854x480
			'18':['18', '134', '93', '34'],  # 640x360
			'5':['5', '36', '92', '133', '132'],  # 400x240
			'17':['17', '160']  # 176x144
		}
	PRIORITY_VIDEO_FORMAT = video_format[config.plugins.YouTube.maxResolution.value]
	for itag_value in ['5', '22', '136', '298', '95',
			'35', '135', '94', '18', '134', '93', '34',
			'36', '92', '132', '133', '6', '13', '151',
			'160', '17', '37', '46', '137', '299', '96',
			'38', '138', '264', '266', '141', '140', '139']:
		if itag_value not in PRIORITY_VIDEO_FORMAT:
			PRIORITY_VIDEO_FORMAT.append(itag_value)

createPriorityFormats()

DASHMP4_FORMAT = [
		'133', '134', '135', '136', '137', '138',
		'160', '264', '266', '298', '299'
	]

IGNORE_VIDEO_FORMAT = [
		'43', '44', '45', '46',  # webm
		'82', '83', '84', '85',  # 3D
		'100', '101', '102',  # 3D
		'167', '168', '169',  # webm
		'170', '171', '172',  # webm
		'218', '219',  # webm
		'242', '243', '244', '245', '246', '247', '248',  # webm
		'271', '272',  # webm
		'302', '303', '308',  # webm
		'313', '315',  # webm
	]


def uppercase_escape(s):
	unicode_escape = codecs.getdecoder('unicode_escape')
	return re.sub(
		r'\\U[0-9a-fA-F]{8}',
		lambda m: unicode_escape(m.group(0))[0],
		s)


def compat_urllib_parse_unquote(string, encoding='utf-8', errors='replace'):
	if string == '':
		return string
	res = string.split('%')
	if len(res) == 1:
		return string
	if encoding is None:
		encoding = 'utf-8'
	if errors is None:
		errors = 'replace'
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
		string += pct_sequence.decode(encoding, errors) + rest
		pct_sequence = b''
	if pct_sequence:
		# Flush the final pct_sequence
		string += pct_sequence.decode(encoding, errors)
	return string


def _parse_qsl(qs, keep_blank_values=False, strict_parsing=False,
			encoding='utf-8', errors='replace'):
	qs, _coerce_result = qs, unicode
	pairs = [s2 for s1 in qs.split('&') for s2 in s1.split(';')]
	r = []
	for name_value in pairs:
		if not name_value and not strict_parsing:
			continue
		nv = name_value.split('=', 1)
		if len(nv) != 2:
			if strict_parsing:
				raise ValueError("bad query field: %r" % (name_value,))
			# Handle case of a control-name with no equal sign
			if keep_blank_values:
				nv.append('')
			else:
				continue
		if len(nv[1]) or keep_blank_values:
			name = nv[0].replace('+', ' ')
			name = compat_urllib_parse_unquote(
				name, encoding=encoding, errors=errors)
			name = _coerce_result(name)
			value = nv[1].replace('+', ' ')
			value = compat_urllib_parse_unquote(
				value, encoding=encoding, errors=errors)
			value = _coerce_result(value)
			r.append((name, value))
	return r


def compat_parse_qs(qs, keep_blank_values=False, strict_parsing=False,
					encoding='utf-8', errors='replace'):
	parsed_result = {}
	pairs = _parse_qsl(qs, keep_blank_values, strict_parsing,
					encoding=encoding, errors=errors)
	for name, value in pairs:
		if name in parsed_result:
			parsed_result[name].append(value)
		else:
			parsed_result[name] = [value]
	return parsed_result


class YouTubeVideoUrl():

	def _download_webpage(self, url, fatal=True):
		""" Returns a tuple (page content as string, URL handle) """
		try:
			if sslContext:
				urlh = urlopen(url, context = sslContext)
			else:
				urlh = urlopen(url)
		except URLError, e:
			if fatal:
				raise Exception(e.reason)
			return False
		return urlh.read()

	def _search_regex(self, pattern, string, group=None):
		"""
		Perform a regex search on the given string, using a single or a list of
		patterns returning the first matching group.
		"""
		if group is None:
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
			raise Exception('Unable extract pattern from string!')

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
		except:
			raise Exception('Signature extraction failed!')

	def _extract_signature_function(self, player_url):
		id_m = re.match(
			r'.*?-(?P<id>[a-zA-Z0-9_-]+)(?:/watch_as3|/html5player(?:-new)?|(?:/[a-z]{2}_[A-Z]{2})?/base)?\.(?P<ext>[a-z]+)$',
			player_url)
		if not id_m:
			raise Exception('Cannot identify player %r!' % player_url)
		player_type = id_m.group('ext')
		code = self._download_webpage(player_url)
		if player_type == 'js':
			return self._parse_sig_js(code)
		elif player_type == 'swf':
			return self._parse_sig_swf(code)
		else:
			raise Exception('Invalid player type %r!' % player_type)

	def _parse_sig_js(self, jscode):
		funcname = self._search_regex(
				(r'(["\'])signature\1\s*,\s*(?P<sig>[a-zA-Z0-9$]+)\(',
				r'\.sig\|\|(?P<sig>[a-zA-Z0-9$]+)\('),
				jscode, group='sig')
		jsi = JSInterpreter(jscode)
		initial_function = jsi.extract_function(funcname)
		return lambda s: initial_function([s])

	def _parse_sig_swf(self, file_contents):
		swfi = SWFInterpreter(file_contents)
		TARGET_CLASSNAME = 'SignatureDecipher'
		searched_class = swfi.extract_class(TARGET_CLASSNAME)
		initial_function = swfi.extract_function(searched_class, 'decipher')
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
		url = 'https://www.youtube.com/watch?v=%s&gl=US&hl=en&has_verified=1&bpctr=9999999999' % video_id

		# Get video webpage
		video_webpage = self._download_webpage(url)
		if not video_webpage:
			raise Exception('Video webpage not found!')

		# Attempt to extract SWF player URL
		mobj = re.search(r'swfConfig.*?"(https?:\\/\\/.*?watch.*?-.*?\.swf)"', video_webpage)
		if mobj is not None:
			player_url = re.sub(r'\\(.)', r'\1', mobj.group(1))
		else:
			player_url = None

		# Get video info
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
			video_info_webpage = self._download_webpage(video_info_url)
			video_info = compat_parse_qs(video_info_webpage)
		else:
			age_gate = False
			video_info = None
			sts = None
			# Try looking directly into the video webpage
			ytplayer_config = self._get_ytplayer_config(video_webpage)
			if ytplayer_config:
				args = ytplayer_config['args']
				if args.get('url_encoded_fmt_stream_map'):
					# Convert to the same format returned by compat_parse_qs
					video_info = dict((k, [v]) for k, v in args.items())
				sts = ytplayer_config.get('sts')

			if not video_info:
				# We also try looking in get_video_info since it may contain different dashmpd
				# URL that points to a DASH manifest with possibly different itag set (some itags
				# are missing from DASH manifest pointed by webpage's dashmpd, some - from DASH
				# manifest pointed by get_video_info's dashmpd).
				# The general idea is to take a union of itags of both DASH manifests (for example
				# video with such 'manifest behavior' see https://github.com/rg3/youtube-dl/issues/6093)
				for el in ('info', 'embedded', 'detailpage', 'vevo', ''):
					query = {
							'video_id': video_id,
							'ps': 'default',
							'eurl': '',
							'gl': 'US',
							'hl': 'en',
						}
					if el:
						query['el'] = el
					if sts:
						query['sts'] = sts
					data = urlencode(query)

					video_info_url = 'https://www.youtube.com/get_video_info?' + data
					video_info_webpage = self._download_webpage(video_info_url, fatal=False)
					if not video_info_webpage:
						continue
					video_info = compat_parse_qs(video_info_webpage)
					if 'token' in video_info:
						break
		if 'token' not in video_info:
			if 'reason' in video_info:
				print '[YouTubeVideoUrl] %s' % video_info['reason'][0]
			else:
				print '[YouTubeVideoUrl] "token" parameter not in video info for unknown reason'

		# Start extracting information
		if 'conn' in video_info and video_info['conn'][0][:4] == 'rtmp':
			url = video_info['conn'][0]
		elif len(video_info.get('url_encoded_fmt_stream_map', [''])[0]) >= 1 or \
			len(video_info.get('adaptive_fmts', [''])[0]) >= 1:
			encoded_url_map = video_info.get('url_encoded_fmt_stream_map', [''])[0] + \
				',' + video_info.get('adaptive_fmts', [''])[0]
			if 'rtmpe%3Dyes' in encoded_url_map:
				raise Exception('rtmpe downloads are not supported, see https://github.com/rg3/youtube-dl/issues/343')

			# Find the best format from our format priority map
			encoded_url_map = encoded_url_map.split(',')
			url_map_str = [None, '']
			# If format changed in config, recreate priority list
			if PRIORITY_VIDEO_FORMAT[0] != config.plugins.YouTube.maxResolution.value:
				createPriorityFormats()
			for our_format in PRIORITY_VIDEO_FORMAT:
				our_format = 'itag=' + our_format
				for encoded_url in encoded_url_map:
					if our_format in encoded_url and 'url=' in encoded_url:
						url_map_str[0] = encoded_url
						break
				if url_map_str[0]:
					break
			# If DASH MP4 video add link also on Dash MP4 Audio
			if url_map_str[0] and our_format[5:] in DASHMP4_FORMAT:
				for our_format in ['itag=141', 'itag=140', 'itag=139']:
					for encoded_url in encoded_url_map:
						if our_format in encoded_url and 'url=' in encoded_url:
							url_map_str[1] = encoded_url
							break
					if url_map_str[1]:
						break
			# If anything not found, used first in the list if it not in ignore map
			if not url_map_str[0]:
				for encoded_url in encoded_url_map:
					if 'url=' in encoded_url:
						url_map_str = encoded_url
						for ignore_format in IGNORE_VIDEO_FORMAT:
							ignore_format = 'itag=' + ignore_format
							if ignore_format in encoded_url:
								url_map_str[0] = None
								break
					if url_map_str[0]:
						break
			if not url_map_str[0]:
				url_map_str[0] = encoded_url_map[0]

			url = ''
			for url_map in url_map_str:
				if not url_map:
					break
				url_data = compat_parse_qs(url_map)
				if url:
					url += '&suburi='
				url += url_data['url'][0]

				if 's' in url_data:
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

				if 'sig' in url_data:
					url += '&signature=' + url_data['sig'][0]
				elif 's' in url_data:
					encrypted_sig = url_data['s'][0]
					signature = self._decrypt_signature(encrypted_sig, player_url)
					url += '&signature=' + signature
				if 'ratebypass' not in url:
					url += '&ratebypass=yes'
		elif video_info.get('hlsvp'):
			url = None
			manifest_url = video_info['hlsvp'][0]
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
		else:
			raise Exception('No supported formats found in video info!')

		return str(url)
