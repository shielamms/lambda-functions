import boto3
from bs4 import BeautifulSoup
import requests
import datetime


class IMDBScraper():
    _start_url = ""
    _soup = None
    output = []

    def _extract_movie_details(self, item):
        title = item.select_one('.title')
        url = item.select_one('.titleLink')
        description = item.select_one('.description')
        rating = item.select_one('.rating')

        return {
            'title': title,
            'url': url,
            'description': description,
            'rating': rating,
        }

    def scrape(self):
        response = requests.get(self._start_url)
        self._soup = BeautifulSoup(response.content)
        items = self._soup.select('.items li')
        
        for item in items:
            self.output.append(_extract_movie_details(item))

    def upload_to_s3(self, data, bucket_name, key):
        s3 = boto3.client('s3')
        s3.upload_file(data, bucket_name, key)


def handler(event, args):
    scraper = IMDBScraper()
    scraper.scrape()
    data = {'movies': scraper.output}
    today = datetime.date.today().strftime('%Y-%m-%d')

    scraper.upload_to_s3(data, event.get('bucket_name'), key=today)