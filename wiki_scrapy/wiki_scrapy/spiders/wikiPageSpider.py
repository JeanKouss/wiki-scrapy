import scrapy
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError, TimeoutError, TCPTimedOutError
import re
from scrapy.linkextractors import LinkExtractor
from wiki_scrapy.services.UrlManager import UrlManager

class WikiPageSpider(scrapy.Spider) :
    name = "wiki_page_spider"
    allowed_domains = ['en.wikipedia.org']
    
    # Check readme.md to know why those are boring or intersting for this project
    interesting_url_pattern = r"https://en\.wikipedia\.org/wiki/.+"
    boring_url_pattern = r"https://en\.wikipedia\.org/wiki/[^/]+:" # example r"https://en\.wikipedia\.org/wiki/(Category|Wikipedia|Help|File|Template|Special|User):"
    
    file_to_scrap = "scraping-datas/urls_to_scrap.txt" # starts from 'https://en.wikipedia.org/wiki/Web_scraping'
    scraped_file = "scraping-datas/scraped_urls.txt"

    def __init__(self):
        super().__init__()
        self.url_manager = UrlManager(self.file_to_scrap, self.scraped_file)


    link_extractor = LinkExtractor(
        allow=interesting_url_pattern,
        deny=boring_url_pattern, 
        unique=True, 
        restrict_css="#bodyContent",
        canonicalize=True
    )


    def should_scrap(self, url) :
        if url in self.scraped_urls :
            return False
        return True

    def start_requests(self):
        while True:
            next_url = self.url_manager.get_next_url_to_scrap()
            if next_url:
                yield scrapy.Request(url=next_url, callback=self.parse, errback=self.errback_httpbin)
            else:
                break
    

    def parse(self, response) :
        next_urls, response_data = self.extact_response_data(response)
        yield response_data
        self.url_manager.add_scraped_url(response.url)
        for url in next_urls :
            self.url_manager.add_url_to_scrap(url)
        self.url_manager.request_urls_persistence()
        next_url = self.url_manager.get_next_url_to_scrap()
        if next_url:
            yield scrapy.Request(url=next_url, callback=self.parse, errback=self.errback_httpbin)
        

    def extact_response_data(self, response) :
        content  = " ".join(response.css('#bodyContent p ::text').extract())
        title = response.css('title::text').extract()[0]
        url = response.url
        linked_pages = self.link_extractor.extract_links(response)
        linked_pages_url = [response.urljoin(link.url) for link in linked_pages]
        response_data = {
            "url" : url,
            "title" : title,
            "content" : content,
            "linked_articles_url" : linked_pages_url,
        }
        return linked_pages_url, response_data


    def spider_closed(self, spider):
        self.url_manager.persist_scraped_urls()
        self.url_manager.persist_urls_to_scrap()


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

