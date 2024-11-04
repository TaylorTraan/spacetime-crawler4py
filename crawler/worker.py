from threading import Thread
from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time
from simhash import Simhash
import re

unwantedTypes = {
    'application/zip', 'image/gif', 'image/jpeg', 'image/png', 
    'video/mp4', 'application/pdf', 'image/svg+xml'
}

class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        super().__init__(daemon=True)
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        
        self.simhashThreshold = config.simhashThreshold
        self.maxFileSize = 1024 * 1024 * 5  # 5 MB

        # Basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
    
    # Hamming Distance(difference between simhash values): lower distance = more similar simhash values
    def getDistance(self, currSimhash, existingSimhash):
        return bin(currSimhash ^ existingSimhash).count('1')
    
    # Considers if simhash of current url is duplicate by comparing it with the other calculated simhash values.
    def isDuplicate(self, simhash):
        for existingSimhash in self.frontier.simhashes:
            if self.getDistance(simhash, existingSimhash) < self.simhashThreshold:
                return True
        self.frontier.simhashes.add(simhash)
        return False

    def isTrap(self, resp, url):
        try:
            # Check for missing or failed response
            if not resp or not resp.raw_response or resp.raw_response.content is None:
                self.logger.info(f"Skipping URL due to download error or missing content: {url}")
                return True

            # Check for unwanted content types
            content_type = resp.raw_response.headers.get('Content-Type', '').split(';')[0].strip().lower()
            if content_type in unwantedTypes:
                self.logger.info(f"Skipping URL due to unwanted content type: {url} (Content-Type: {content_type})")
                return True

            # Check Content-Length to skip overly large files
            content_length = resp.raw_response.headers.get('Content-Length')
            if content_length and content_length.isdigit():
                if int(content_length) > self.maxFileSize:
                    self.logger.info(f"Skipping large file: {url} (Content-Length: {content_length})")
                    return True
            else:
                if content_length:
                    self.logger.info(f"Invalid Content-Length value: {content_length} for {url}")
                    return True

            # Check for unwanted file extensions
            unwanted_extensions = ['.zip', '.mp4', '.png']
            if any(url.lower().endswith(ext) for ext in unwanted_extensions):
                self.logger.info(f"Skipping URL due to unwanted file extension: {url}")
                return True

            # Check for duplicate content using Simhash
            page_simhash = Simhash(resp.raw_response.text).value
            if self.isDuplicate(page_simhash):
                self.logger.info(f"Duplicate content detected: {url}")
                return True

        except Exception as e:
            self.logger.error(f"Error in isTrap: {e}")
            return True

        return False


    def generate_report(self):
        try:
            with open("report.txt", 'a') as file:
                # Number of unique pages visited
                file.write(f'Number of unique pages: {len(self.frontier.visitedURLs)}\n')

                # Longest page information
                file.write(f'Longest page: {self.frontier.highestWordCount[0]}, word count: {self.frontier.highestWordCount[1]}\n')

                # Remove stop words from word frequency
                for word in self.frontier.stopWords:
                    if word in self.frontier.wordCounter:
                        del self.frontier.wordCounter[word]

                # 50 most common words
                file.write(f'50 most common words: {self.frontier.wordCounter.most_common(50)}\n')

                # Number of subdomains and their counts
                file.write(f'Number of subdomains: {len(self.frontier.subdomains)}\n')
                for subdomain, urlSet in sorted(self.frontier.subdomains.items()):
                    file.write(f'{subdomain}: {len(urlSet)}\n')

        except IOError as e:
            self.logger.info(f"Error writing report: {e}")


    def run(self):
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            resp = download(tbd_url, self.config, self.logger)
            if self.isTrap(resp, tbd_url):
                continue
            
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}."
            )
            
            self.frontier.wordCount(tbd_url, resp)
            
            scraped_urls = scraper.scraper(tbd_url, resp, self.frontier.visitedURLs, self.frontier.subdomains)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
            
        self.generate_report()
