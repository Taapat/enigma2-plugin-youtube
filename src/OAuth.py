from __future__ import print_function
# This autentification code based on: https://github.com/guyc/py-gaugette/blob/master/gaugette/oauth.py
# https://developers.google.com/accounts/docs/OAuth2ForDevices

from urllib import urlencode
from httplib import HTTPSConnection
from json import loads
from time import sleep

from . import sslContext


class OAuth:
	def __init__(self, client_id, client_secret):
		self.client_id = client_id
		self.client_secret = client_secret
		self.device_code = ''
		self.verification_url = ''
		self.set_connection()

	# this setup is isolated because it eventually generates a BadStatusLine
	# exception, after which we always get httplib.CannotSendRequest errors.
	#  When this happens, we try re-creating the exception.
	def set_connection(self):
		# HTTPConnection.debuglevel = 1
		if sslContext:
			self.conn = HTTPSConnection('accounts.google.com', context=sslContext)
		else:
			self.conn = HTTPSConnection('accounts.google.com')

	def get_user_code(self):
		try:
			self.conn.request(
					"POST",
					"/o/oauth2/device/code",
					urlencode({
						'client_id': self.client_id,
						'scope'	: 'https://www.googleapis.com/auth/youtube'
						}),
					{"Content-type": "application/x-www-form-urlencoded"}
				)
			response = self.conn.getresponse()
			if (response.status == 200):
				data = loads(response.read())
				self.device_code = data['device_code']
				self.verification_url = data['verification_url']
				self.retry_interval = data['interval']
				return data['user_code']
			else:
				print(response.status)
				print(response.read())
		except:
			pass
		return ''

	def get_new_token(self):
		try:
			self.conn.request(
					"POST",
					"/o/oauth2/token",
					urlencode({
							'client_id': self.client_id,
							'client_secret': self.client_secret,
							'code': self.device_code,
							'grant_type': 'http://oauth.net/grant_type/device/1.0'
						}),
					{"Content-type": "application/x-www-form-urlencoded"}
				)
			response = self.conn.getresponse()
			if (response.status == 200):
				data = loads(response.read())
				if 'access_token' in data:
					self.conn.close()
					return data['refresh_token'], 1
		except:
			pass
		return None, self.retry_interval + 2

	def get_access_token(self, refresh_token):
		try:
			self.conn.request(
					"POST",
					"/o/oauth2/token",
					urlencode({
							'client_id': self.client_id,
							'client_secret': self.client_secret,
							'refresh_token': refresh_token,
							'grant_type': 'refresh_token'
						}),
					{"Content-type": "application/x-www-form-urlencoded"}
				)
			response = self.conn.getresponse()
			if (response.status == 200):
				data = loads(response.read())
				self.conn.close()
				return data['access_token']
			else:
				print("Unexpected response %d" % response.status)
				print(response.read())
				self.conn.close()
		except:
			pass
		return None
