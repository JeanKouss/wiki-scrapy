import scrapy

class WikiPageSpider(scrapy.Spider) :
    name = "wiki_page_spider"
    # url = 'https://fr.wikipedia.org/wiki/Web_scraping'
    url = 'https://en.wikipedia.org/wiki/Geography_of_Togo'

    def start_requests(self):
        yield scrapy.Request(url = self.url, callback=self.parse)
    
    def parse(self, response) :
        content  = " ".join(response.css('#bodyContent p ::text').extract())
        

