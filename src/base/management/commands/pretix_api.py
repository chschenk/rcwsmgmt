import requests

class PretixAPI:

	def __init__(self, url, token, organizer, event):
		self.url = url
		self.organizer = organizer
		self.event = event
		self.headers = {
			"Accept": "application/json, text/javascript",
			"Authorization": f"Token {token}"
		}

	def get_json(self, url):
		response = requests.get(url, headers=self.headers)
		try:
			response.raise_for_status()
		except requests.HTTPError as exc:
			raise requests.HTTPError(
				f"Pretix API request failed for {url}: {response.status_code} {response.text}",
				response=response,
				request=response.request,
			) from exc
		return response.json()

	def get_paginated_result(self, url):
		results = list()
		response = self.get_json(url)
		results.extend(response['results'])
		while response['next'] is not None:
			response = self.get_json(response['next'])
			results.extend(response['results'])
		return results

	def get_orders(self):
		url = f"{self.url}/api/v1/organizers/{self.organizer}/events/{self.event}/orders/"
		return self.get_paginated_result(url)

	def get_products(self):
		url = f"{self.url}/api/v1/organizers/{self.organizer}/events/{self.event}/items/"
		return self.get_paginated_result(url)