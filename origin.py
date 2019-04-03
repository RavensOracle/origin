import requests
import re
import json
from random import randint

def random_string(length):
	alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXTZabcdefghiklmnopqrstuvwxyz"
	return "".join([alphabet[randint(0,len(alphabet)-1)] for i in range(length)])

class Origin():
	def __init__(self, login, password):
		self.login = login
		self.password = password
		self.cid = random_string(32)
		self.fid = None
		self.jssessionid = None
		self.sid = None
		self.code = None
		self.AWSELB = None
		self.access_token = None
		self.userid = None
		self.user_agent  = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
		self.headers["User-Agent"] = self.user_agent

	def GET(self, url, params=None, headers=None):
		headers = headers or {}
		headers["User-Agent"] = self.user_agent

		response = requests.get(url, params=params, headers=headers, allow_redirects=False)

		return response

	def POST(self, url, data=None, headers=None):
		headers = headers or {}
		headers["User-Agent"] = self.user_agent

		response = requests.post(url, data=data, headers=headers)

		return response

	def OPTIONS(self, url, headers=None):
		headers = headers or {}
		headers["User-Agent"] = self.user_agent

		response = requests.options(url, headers=headers)

		return response
	def __get_fid(self):
		url = "https://accounts.ea.com/connect/auth?response_type=code&client_id=ORIGIN_SPA_ID&display=originXWeb/login&locale=ru_RU&release_type=prod&redirect_uri=https://www.origin.com/views/login.html"

		response = self.GET(url)

		if response.code == 302:
			self.fid = re.search('''(?<=fid=)[a-zA-Z0-9]+?(?=&|$)''', response.headers["Location"]).group(0)

			location = response.headers["Location"]

			return location

	def __get_JS_sessionid(self, location):

		response = self.GET(location)

		if response.code == 302:
			self.jssessionid = re.search('''(?<=JSESSIONID=)[\S]+?(?=;)''', response.headers["Set-Cookie"]).group(0)

			location = response.headers["Location"]

			return f"https://signin.ea.com{location}"

	def __visit_auth_page(self, location):

		headers = {
			"Cookie": f"JSESSIONID=self.jssessionid"
		}

		response = self.GET(location, headers=headers)

		if response.code == 302:
			self.jssessionid = re.search('''(?<=JSESSIONID=)[\S]+?(?=;)''', response.headers["Set-Cookie"]).group(0)

			location = response.headers["Location"]

			return location


	def __post_auth_data(self, location):

		headers = {
			"Cookie": f"JSESSIONID={self.jssessionid}"
		}

		data = {
			"email": self.login,
			"password": self.password,
			"_eventId": "submit",
			"cid": self.cid,
			"showAgeUp": "true",
			"googleCaptchaResponse": "",
			"_rememberMe": "on"
		}

		response = self.POST(location, data=data, headers=headers)

		if response.code == 200:
			location = re.search('''(?<=window\.location = \")\S+(?=\";)''', response.text).group(0)

			return location

	def __get_sid(self, location):

		response = self.GET(location)

		if response.code == 302:
			self.sid = re.search('''(?<=sid=)[\S]+?(?=;)''', response.headers["Set-Cookie"]).group(0)

			self.code = re.search('''(?<=code=)[\S]+?(?=&|$)''', response.headers["Location"]).group(0)
			
			location = response.headers["Location"]

			return location

	def __get_AWSELB(self, location):

		response = self.GET(location)

		if response.code == 200:
			self.AWSELB = re.search('''(?<=AWSELB=)[\S]+?(?=;)''', response.headers["Set-Cookie"]).group(0)

	def __get_access_token(self):
		url = "https://accounts.ea.com/connect/auth?client_id=ORIGIN_JS_SDK&response_type=token&redirect_uri=nucleus:rest&prompt=none&release_type=prod"

		headers = {
			"Cookie": f"sid={self.sid}"
		}

		response = self.GET(url, headers=headers)

		response_json = json.loads(response.text)

		if response.code == 200:
			self.access_token = {
				"access_token": response_json["access_token"],
				"token_type": response_json["token_type"]
				}

	def auth(self):

		location = self.__get_fid()

		location = self.__get_JS_sessionid(location)

		self.__visit_auth_page(location)

		location = self.__post_auth_data(location)

		location = self.__get_sid(location)

		self.__get_AWSELB(location)

		self.__get_access_token()


	def view_profile(self):
		url = "https://www.origin.com/views/profile.html"

		headers = {
			"AWSELB": f"AWSELB={self.AWSELB}"
		}

		response = self.GET(url, headers=headers)

		return response.text

	def get_userid(self):
		url = "https://gateway.ea.com/proxy/identity/pids/me"

		self.OPTIONS(url)

		token_type = self.access_token["token_type"]
		access_token = self.access_token["access_token"]

		headers = {
			"Authorization": f"{token_type} {access_token}"
		}

		response = self.GET(url, headers=headers)

		return response.text

	def get_games(self, userid):
		url = f"https://api4.origin.com/ecommerce2/consolidatedentitlements/{userid}?machine_hash=1"

		access_token = self.access_token["access_token"]

		headers = {
			"AuthToken": f"{access_token}",
			"Accept": "application/vnd.origin.v3+json; x-cache/force-write"
		}

		response = self.GET(url, headers=headers)

		return response.text


	def users(self, userid):
		url = f"https://api3.origin.com/atom/users?userIds={userid}"

		response = self.OPTIONS(url)

		headers = {
			"AuthToken": self.access_token["access_token"]
		}

		response = self.GET(url, headers=headers)

		return response.text


login = "nick_crichton@hotmail.com"
password = "Defence123"

origin = Origin(login, password)

origin.auth()

print(origin.__dict__)

#origin.view_profile()

#origin.access_token["token_type"] = "QVQxOjEuMDozLjA6NjA6OE1oRlRBZXI2MmI3aHpMWlNiUjY2RUNnZ0NwU09uaTV0b3o6NTk2Mzg6b2ppMDk"

origin.get_userid()

origin.get_games("2258446805")
