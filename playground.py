import scrapy
from scrapy.crawler import CrawlerProcess

class WikiScrapy(scrapy.Spider) :
    name = "wiki_scraper"
    # url = 'https://fr.wikipedia.org/wiki/Web_scraping'
    # url = 'https://en.wikipedia.org/wiki/Abraham_Lincoln'
    url = '  https://en.wikipedia.org/wiki/Geography_of_Togo'
    # url = 'https://www.te38.fr/comprendre-la-rodp-en-3-minutes/'
    allowed_domains = ['wikipedia.org']

    def start_requests(self):
        yield scrapy.Request(url = self.url, callback=self.parse)
    
    def parse(self, response) :
        content  = " ".join(response.css('#bodyContent p ::text').extract())
        title = response.css('title::text').extract()[0]
        url = response.url
        linked_pages = response.css('#bodyContent a::attr(href)').extract()
        linked_pages_url = []
        for link in linked_pages :
            link_url = response.urljoin(link)
            linked_pages_url.append(link_url)
        print(linked_pages)
        print({
            "url" : url,
            "title" : title,
            "content" : content,
            "linked_pages_url" : linked_pages_url,
        })
        
    
    def old_parse(self, response) :
        text  = response.css('main *::text').extract()
        print(" ".join(text))
        pass

process = CrawlerProcess()
process.crawl(WikiScrapy)
process.start()
