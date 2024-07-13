import scrapy
from collections import deque

class WikiPageSpider(scrapy.Spider) :
    name = "wiki_page_spider"
    
    file_to_scrap = "../data/urls_to_scrap.txt" # starts from 'https://fr.wikipedia.org/wiki/Web_scraping'
    scraped_file = "../data/scraped_urls.txt"

    scraped_urls = []
    urls_to_scrap = deque([])

    def load_urls_to_scrap(self) :
        with open(self.file_to_scrap, 'r') as to_scrap :
            content = to_scrap.read()
            for url in content.split('\n') :
                self.urls_to_scrap.append(url)
    
    def persist_urls_to_scrap(self) :
        to_text = "\n".join(self.urls_to_scrap)
        with open(self.file_to_scrap, 'w') as to_scrap :
            to_scrap.write(to_text)
    
    def load_sraped_urls(self) :
        try :
            with open(self.scraped_urls, 'r') as scraped :
                content = scraped.read()
                self.scraped_urls = content.split('\n')
        except FileNotFoundError :
            self.scraped_urls = []
            self.persist_scraped_urls()
    
    def persist_scraped_urls(self) :
        to_text = "\n".join(self.scraped_urls)
        with open(self.scraped_file, 'w') as scraped :
            scraped.write(to_text)

    def start_requests(self):
        self.load_urls_to_scrap()
        self.load_sraped_urls()
        while self.urls_to_scrap :
            next_url = self.urls_to_scrap.popleft()
            if next_url not in self.scraped_urls :
                yield scrapy.Request(url = next_url, callback=self.parse)
    

    def parse(self, response) :
        next_urls = self.extact_response_data(response)
        for url in next_urls :
            self.urls_to_scrap.append(url)
        # TODO : Persist urls_to_scrap and scraped_urls
        while self.urls_to_scrap :
            next_url = self.urls_to_scrap.popleft()
            if next_url not in self.scraped_urls :
                yield scrapy.Request(url = next_url, callback=self.parse)
        

    def extact_response_data(self, response) :
        content  = " ".join(response.css('#bodyContent p ::text').extract())
        title = response.css('title::text').extract()[0]
        url = response.url
        linked_pages = response.css('#bodyContent a::attr(href)').extract()
        linked_pages_url = []
        for link in linked_pages :
            link_url = response.urljoin(link)
            linked_pages_url.append(link_url)
        # TODO : Store craped data
        print({
            "url" : url,
            "title" : title,
            "content" : content,
            "linked_pages_url" : linked_pages_url,
        })
        return linked_pages_url

        

