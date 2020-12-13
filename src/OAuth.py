# -*- coding: UTF-8 -*-
from __future__ import print_function

from json import loads
from time import sleep

from .compat import compat_urlencode
from .compat import compat_urlopen
from .compat import compat_Request


class OAuth:
	def __init__(self, client_id, client_secret):
		self.client_id = client_id
		self.client_secret = client_secret
		self.device_code = ''
		self.verification_url = ''

	def get_oauth_response(self, url, data):
		headers = {'Content-type': 'application/x-www-form-urlencoded'}
		try:
			request = compat_Request(url, data=data, headers=headers)
			request.get_method = lambda: 'POST'
			response = compat_urlopen(request)
			status_code = response.getcode()
			if status_code == 200:
				return loads(response.read())
			else:
				print('[OAuth] Error in auth response, errorcode', status_code)
				print(response.read())
		except Exception as e:
			print('[OAuth] Error in auth response', e)
		return {}

	def get_user_code(self):
		url = 'https://accounts.google.com/o/oauth2/device/code'
		data = compat_urlencode({
				'client_id': self.client_id,
				'scope'	: 'https://www.googleapis.com/auth/youtube'
				}).encode()
		data = self.get_oauth_response(url, data)
		self.device_code = data.get('device_code', '')
		self.verification_url = data.get('verification_url', '')
		self.retry_interval = data.get('interval', 2)
		return data.get('user_code', '')

	def get_new_token(self):
		url = 'https://accounts.google.com/o/oauth2/token'
		data = compat_urlencode({
				'client_id': self.client_id,
				'client_secret': self.client_secret,
				'code': self.device_code,
				'grant_type': 'http://oauth.net/grant_type/device/1.0'
				}).encode()
		data = self.get_oauth_response(url, data)
		if 'access_token' in data and 'refresh_token' in data:
			return data['refresh_token'], 1
		return None, self.retry_interval + 2

	def get_access_token(self, refresh_token):
		url = 'https://accounts.google.com/o/oauth2/token'
		data = compat_urlencode({
				'client_id': self.client_id,
				'client_secret': self.client_secret,
				'refresh_token': refresh_token,
				'grant_type': 'refresh_token'
				}).encode()
		data = self.get_oauth_response(url, data)
		if 'access_token' in data:
			return data['access_token']
		print('[OAuth] Error in get access token')
		return None
