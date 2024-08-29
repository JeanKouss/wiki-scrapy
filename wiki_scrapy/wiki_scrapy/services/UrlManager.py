import threading
from collections import deque

class UrlManager:
    _instance = None
    _lock = threading.RLock()  # Lock for synchronizing access to the singleton instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:  # Ensure that only one thread can create the instance
                if cls._instance is None:
                    cls._instance = super(UrlManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, file_to_scrap="scraping-datas/urls_to_scrap.txt", scraped_file="scraping-datas/scraped_urls.txt"):
        if self._initialized:
            return
        self.file_to_scrap = file_to_scrap
        self.scraped_file = scraped_file
        self.urls_to_scrap = deque()
        self.scraped_urls = []
        self.current_persistence_count = 0
        self.max_persistence_count = 100
        self._initialized = True
        self._data_lock = threading.RLock()  # Lock for synchronizing data access
        self.load_urls_to_scrap()
        self.load_scraped_urls()

    def load_urls_to_scrap(self):
        with self._data_lock:
            with open(self.file_to_scrap, 'r', encoding='utf-8') as to_scrap:
                content = to_scrap.read()
                for url in content.split('\n'):
                    self.urls_to_scrap.append(url)

    def persist_urls_to_scrap(self):
        with self._data_lock:
            to_text = "\n".join(self.urls_to_scrap)
            with open(self.file_to_scrap, 'w', encoding='utf-8') as to_scrap:
                to_scrap.write(to_text)

    def load_scraped_urls(self):
        with self._data_lock:
            try:
                with open(self.scraped_file, 'r', encoding='utf-8') as scraped:
                    content = scraped.read()
                    self.scraped_urls = content.split('\n')
            except FileNotFoundError:
                self.scraped_urls = []
                self.persist_scraped_urls()

    def persist_scraped_urls(self):
        with self._data_lock:
            to_text = "\n".join(self.scraped_urls)
            with open(self.scraped_file, 'w', encoding='utf-8') as scraped:
                scraped.write(to_text)

    def request_urls_persistence(self):
        with self._data_lock:
            self.current_persistence_count += 1
            if self.current_persistence_count >= self.max_persistence_count:
                self.persist_scraped_urls()
                self.persist_urls_to_scrap()
                self.current_persistence_count = 0

    def add_scraped_url(self, url):
        with self._data_lock:
            self.scraped_urls.append(url)

    def get_next_url_to_scrap(self):
        with self._data_lock:
            while self.urls_to_scrap:
                next_url = self.urls_to_scrap.popleft()
                if next_url not in self.scraped_urls:
                    return next_url
            return None

    def add_url_to_scrap(self, url):
        with self._data_lock:
            if url not in self.scraped_urls:
                self.urls_to_scrap.append(url)
