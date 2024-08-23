import scrapy
from collections import deque
from wiki_scrapy.items import WikiScrapyItem
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError, TimeoutError, TCPTimedOutError
import re
from scrapy.linkextractors import LinkExtractor

class WikiPageSpider(scrapy.Spider) :
    name = "wiki_page_spider"
    allowed_domains = ['en.wikipedia.org']
    
    # Check readme.md to know why those are boring or intersting for this project
    interesting_url_pattern = r"https://en\.wikipedia\.org/wiki/.+"
    boring_url_pattern = r"https://en\.wikipedia\.org/wiki/[^/]+:" # example r"https://en\.wikipedia\.org/wiki/(Category|Wikipedia|Help|File|Template|Special|User):"
    
    file_to_scrap = "scraping-datas/urls_to_scrap.txt" # starts from 'https://en.wikipedia.org/wiki/Web_scraping'
    scraped_file = "scraping-datas/scraped_urls.txt"

    scraped_urls = []
    urls_to_scrap = deque([])

    current_persistence_count = 0
    max_persistence_count = 10

    link_extractor = LinkExtractor(
        allow=interesting_url_pattern,
        deny=boring_url_pattern, 
        unique=True, 
        restrict_css="#bodyContent",
        canonicalize=True
    )

    def load_urls_to_scrap(self) :
        with open(self.file_to_scrap, 'r', encoding='utf-8') as to_scrap :
            content = to_scrap.read()
            for url in content.split('\n') :
                self.urls_to_scrap.append(url)
    
    def persist_urls_to_scrap(self) :
        to_text = "\n".join(self.urls_to_scrap)
        with open(self.file_to_scrap, 'w', encoding='utf-8') as to_scrap :
            to_scrap.write(to_text)
    
    def load_sraped_urls(self) :
        try :
            with open(self.scraped_file, 'r', encoding='utf-8') as scraped :
                content = scraped.read()
                self.scraped_urls = content.split('\n')
        except FileNotFoundError :
            self.scraped_urls = []
            self.persist_scraped_urls()
    
    def persist_scraped_urls(self) :
        to_text = "\n".join(self.scraped_urls)
        with open(self.scraped_file, 'w', encoding='utf-8') as scraped :
            scraped.write(to_text)

    def request_urls_persitence(self) :
        self.current_persistence_count += 1
        if self.current_persistence_count <= self.max_persistence_count :
            return
        self.persist_scraped_urls()
        self.persist_urls_to_scrap()
        self.current_persistence_count = 0
        self.logger.info('Persisting urls')


    def should_scrap(self, url) :
        if url in self.scraped_urls :
            return False
        return True

    def start_requests(self):
        self.load_urls_to_scrap()
        self.load_sraped_urls()
        while self.urls_to_scrap :
            next_url = self.urls_to_scrap.popleft()
            if self.should_scrap(next_url) :
                yield scrapy.Request(url = next_url, callback=self.parse)
    

    def parse(self, response) :
        next_urls, response_data = self.extact_response_data(response)
        yield response_data
        self.scraped_urls.append(response.url)
        for url in next_urls :
            self.urls_to_scrap.append(url)
        self.request_urls_persitence()
        while self.urls_to_scrap :
            next_url = self.urls_to_scrap.popleft()
            if self.should_scrap(next_url) :
                yield scrapy.Request(url = next_url, callback=self.parse)
        

    def extact_response_data(self, response) :
        content  = " ".join(response.css('#bodyContent p ::text').extract())
        title = response.css('title::text').extract()[0]
        url = response.url
        linked_pages = self.link_extractor.extract_links(response)
        linked_pages_url = []
        for link in linked_pages :
            link_url = response.urljoin(link.url)
            linked_pages_url.append(link_url)
        response_data = {
            "url" : url,
            "title" : title,
            "content" : content,
            "linked_articles_url" : linked_pages_url,
        }
        return linked_pages_url, response_data


    def spider_closed(self, spider):
        self.persist_scraped_urls()
        self.persist_urls_to_scrap()


    def errback_httpbin(self, failure):
        # Log all failures
        self.logger.error(repr(failure))

        # Check if it's an HTTP error
        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)
            if response.status == 429:
                self.logger.error('Received 429 Too Many Requests. Stopping crawler.')
                self.crawler.engine.close_spider(self, 'Received 429 Too Many Requests')

        # Check if it's a DNS error
        elif failure.check(DNSLookupError):
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)

        # Check if it's a Timeout error
        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)

