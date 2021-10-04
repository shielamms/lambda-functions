from bs4 import BeautifulSoup
import requests

class IMDBScraper():
    _start_url = ""
    _soup = None
    output = []

    def _extract_details(self, item):
        title = self._soup.select_one('')
        url = self._soup.select_one('')
        description = self._soup.select_one('')
        rating = self._soup.select_one('')

        return {
            'title': title,
            'url': url,
            'description': description,
            'rating': rating,
        }

    def scrape(self):
        response = requests.get(self._start_url)
        self._soup = BeautifulSoup(response.content)
        items = self._soup.select('')
        
        for item in items:
            self.output.append(_extract_details(item))

    def upload_to_s3(self, bucket_name):
        pass


def handler(event, args):
    scraper = IMDBScraper()
    scraper.scrape()

    bucket_name = ""
    scraper.upload_to_s3(bucket_name)