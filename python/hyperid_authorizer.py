import os
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from flask import Flask, redirect, request, render_template

class eConfig:
	def __init__(self, _clientId, _clientSecret, _redirectUri, _scope, _endpoint):
		self.clientId = _clientId
		self.clientSecret = _clientSecret
		self.redirectUri = _redirectUri
		self.scope = _scope
		self.endpoint = _endpoint

class eClient:
	def __init__(self, _config):
		self.config = _config
		self.authEndpoint = None
		self.tokenEndpoint = None
		self.discoverUrls()

	def discoverUrls(self):
		headers =	{
						'User-Agent': 'HyperID Tester/1.0',
						'Accept': 'application/json'
					}
		req = Request(self.config.endpoint + '/.well-known/openid-configuration', None, headers)
		res = urlopen(req)
		data = json.loads(res.read())
		self.authEndpoint = data['authorization_endpoint']
		self.tokenEndpoint = data['token_endpoint']

	def authorize(self):
		if self.authEndpoint is None:
			self.renderError('authEndpoint is empty')
			return
		requestArgs =	{
							'response_type': 'code',
							'client_id': self.config.clientId,
							'redirect_uri': self.config.redirectUri,
							'scope':self.config.scope,
							'flow_mode': 4,
							'wallet_get_mode': 3
						}
		url = "%s?%s" % (self.authEndpoint, urlencode(requestArgs))
		return redirect(url)

	def onAuthorized(self, _request):
		if 'code' not in request.args:
			return self.renderError('No code in response')
		return self.getTokensByCode(request.args['code'])

	def getTokensByCode(self, _code):
		if self.tokenEndpoint is None:
			return self.renderError('tokenEndpoint is empty')
		headers =	{
						'User-Agent': 'HyperID Tester/1.0',
						'Accept': 'application/json'
					}
		params =	{
						'grant_type': 'authorization_code',
						'code': _code,
						'redirect_uri': self.config.redirectUri,
						'client_id': self.config.clientId,
						'client_secret': self.config.clientSecret
					}
		req = Request(self.tokenEndpoint, urlencode(params).encode('ascii'), headers)
		res = urlopen(req)
		data = json.loads(res.read())
		if 'access_token' not in data:
			return self.renderError('No access_token in response')
		if 'refresh_token' not in data:
			return self.renderError('No refresh_token in response')
		return self.renderTokens(data['refresh_token'], data['access_token'])

	def renderTokens(self, _refreshToken, _accessToken):
		return '<html><body><b>refresh_token:</b>&nbsp;' + _refreshToken + '<br><b>access_token:</b>&nbsp;' + _accessToken + '<body><html>'

	def renderError(self, _error):
		return '<html><body><b>Error:</b>&nbsp;' + _error + '<body><html>'


config = eConfig('server-test', 'fFPiQrjCpkWQmrKW6Nsxx0Cwfn2wNkj7', 'http://127.0.0.1:8082/callback', 'openid email', 'https://login-stage.hypersecureid.com/auth/realms/HyperID')
client = eClient(config)
app = Flask('hyperid_tester')

@app.route('/')
def index():
	return client.authorize()

@app.route('/callback')
def callback():
	return client.onAuthorized(request)

app.run('0.0.0.0', port=8082)