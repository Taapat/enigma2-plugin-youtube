# -*- coding: UTF-8 -*-
from __future__ import print_function

from json import loads
from os import path

from .compat import compat_urlencode
from .compat import compat_urlopen
from .compat import compat_Request


def get_key(x):
	p = 3
	while True:
		if p > len(x):
			break
		pl = len(str(p))
		x = x[:p] + x[p + pl:]
		p += 12 - pl
	x = x.replace('w_OizD', 'a')
	x = x.replace('Xhi_Lo', 'A')
	return x


API_KEY = get_key('Xhi3_LoIzw_OizD15SyCNReMvKL27nw_OizDWRR395T5uGWpvn451I2VYc78Gy463')
CLIENT_ID = get_key('4113447027255-v15bgs05u1o3m278mpjs2vcd0394w_OizDfrg5160drbw_Oiz63D.w_OizDpp75s.googleus87ercontent.99com')
CLIENT_SECRET = get_key('Zf93pqd2rxgY2ro159rK20BMxif27')

if path.exists('/etc/enigma2/YouTube.key'):  # pragma: no cover
	try:
		for line in open('/etc/enigma2/YouTube.key').readlines():
			line = line.strip().replace(' ', '')
			if len(line) < 30 or line[0] == '#' or '=' not in line:
				continue
			line = line.split('=', 1)
			if line[1].startswith('"') or line[1].startswith("'"):
				line[1] = line[1][1:]
			if line[1].endswith('"') or line[1].endswith("'"):
				line[1] = line[1][:-1]
			if line[1].startswith('GET_'):
				line[1] = get_key(line[1][4:])
			if 'API_KEY' in line[0]:
				API_KEY = line[1]
			elif 'CLIENT_ID' in line[0]:
				CLIENT_ID = line[1]
			elif 'CLIENT_SECRET' in line[0]:
				CLIENT_SECRET = line[1]
	except Exception as e:
		print('[OAuth] Error in read YouTube.key', e)


class OAuth:
	def __init__(self):
		self.device_code = ''
		self.retry_interval = 2

	def get_oauth_response(self, url, data):
		data = compat_urlencode(data).encode()
		headers = {'Content-type': 'application/x-www-form-urlencoded'}
		request = compat_Request(url, data=data, headers=headers)
		request.get_method = lambda: 'POST'
		response = None
		try:
			response = compat_urlopen(request, timeout=5)
		except Exception as e:
			print('[OAuth] Error in auth response', e)
		else:
			if response:
				status_code = response.getcode()
				if status_code == 200:
					return loads(response.read())
				else:  # pragma: no cover
					print('[OAuth] Error in auth response, errorcode', status_code)
					print(response.read())
		return {}

	def get_user_code(self):  # pragma: no cover
		url = 'https://accounts.google.com/o/oauth2/device/code'
		data = {'client_id': CLIENT_ID,
				'scope': 'https://www.googleapis.com/auth/youtube'}
		data = self.get_oauth_response(url, data)
		self.device_code = data.get('device_code', '')
		self.retry_interval = data.get('interval', 2)
		return str(data.get('verification_url', '')), str(data.get('user_code', ''))

	def get_new_token(self):  # pragma: no cover
		url = 'https://accounts.google.com/o/oauth2/token'
		data = {'client_id': CLIENT_ID,
				'client_secret': CLIENT_SECRET,
				'code': self.device_code,
				'grant_type': 'http://oauth.net/grant_type/device/1.0'}
		data = self.get_oauth_response(url, data)
		if 'access_token' in data and 'refresh_token' in data:
			return data['refresh_token'], 1
		return None, self.retry_interval + 2

	def get_access_token(self, refresh_token):
		url = 'https://accounts.google.com/o/oauth2/token'
		data = {'client_id': CLIENT_ID,
				'client_secret': CLIENT_SECRET,
				'refresh_token': refresh_token,
				'grant_type': 'refresh_token'}
		res = self.get_oauth_response(url, data)
		if 'access_token' in res:
			yt_auth = '%s %s' % (res['token_type'], res['access_token']) if 'token_type' in res else None
			return res['access_token'], yt_auth
		print('[OAuth] Error in get access token')
		return None, None
