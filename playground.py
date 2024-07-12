import scrapy
from scrapy.crawler import CrawlerProcess

class WikiScrapy(scrapy.Spider) :
    name = "wiki_scraper"
    # url = 'https://fr.wikipedia.org/wiki/Web_scraping'
    # url = 'https://en.wikipedia.org/wiki/Abraham_Lincoln'
    url = 'https://en.wikipedia.org/wiki/Geography_of_Togo'

    def start_requests(self):
        yield scrapy.Request(url = self.url, callback=self.parse)
    
    def parse(self, response) :
        text  = response.css('#bodyContent p ::text').extract()
        print(" ".join(text))
        pass
    
    def old_parse(self, response) :
        text  = response.css('main *::text').extract()
        print(" ".join(text))
        pass

process = CrawlerProcess()
process.crawl(WikiScrapy)
process.start()
