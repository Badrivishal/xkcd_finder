from prometheus_client import start_http_server, Counter, Summary, Histogram
import time

class PrometheusHelper:
    def __init__(self):
        self.request_counter = Counter('app_requests_total', 'Total number of requests')
        self.successful_requests_counter = Counter('app_successful_requests_total', 'Total number of successful requests')
        self.failed_requests_counter = Counter('app_failed_requests_total', 'Total number of failed requests')
        self.request_duration_summary = Summary('app_request_duration_seconds', 'Time spent processing request')
        self.comic_frequency = Counter('comic_frequency', 'Frequency of comics being selected', ['comic_id'])
        self.index_build_start_time = None
        self.index_build_duration = Summary('index_build_duration_seconds', 'Time spent building the index')
        self.faiss_index_search_start_time = None
        self.faiss_index_search_duration = Summary('faiss_index_search_duration_seconds', 'Time spent searching the index')
        self.chat_model_call_start_time = None
        self.chat_model_call_duration = Summary('chat_model_call_duration_seconds', 'Time spent calling the chat model')
        # self.frequency_histogram = Histogram('comic_frequency', 'Frequency of comics being selected')


    def start_faiss_index_search_timer(self):
        self.faiss_index_search_start_time = time.time()
    
    def stop_faiss_index_search_timer(self):
        self.faiss_index_search_duration.observe(time.time() - self.faiss_index_search_start_time)

    def start_chat_model_call_timer(self):
        self.chat_model_call_start_time = time.time()
    
    def stop_chat_model_call_timer(self):
        self.chat_model_call_duration.observe(time.time() - self.chat_model_call_start_time)

    def record_request(self, success: bool):
        self.request_counter.inc()
        if success:
            self.successful_requests_counter.inc()
        else:
            self.failed_requests_counter.inc()

    def start_index_build_timer(self):
        self.index_build_start_time = time.time()

    def stop_index_build_timer(self):
        self.index_build_duration.observe(time.time() - self.index_build_start_time)

    def setup_prometheus(self):
        start_http_server(8000)

    def start_request_timer(self):
        self.start_time = time.time()
    
    def stop_request_timer(self):
        self.request_duration_summary.observe(time.time() - self.start_time)

    def record_frequency(self, comic_id: int):
        self.comic_frequency.labels(comic_id=comic_id).inc()
    
