from prometheus_client import start_http_server, Counter, Summary


class PrometheusHelper:
    def __init__(self):
        self.request_counter = Counter('app_requests_total', 'Total number of requests')
        self.successful_requests_counter = Counter('app_successful_requests_total', 'Total number of successful requests')
        self.failed_requests_counter = Counter('app_failed_requests_total', 'Total number of failed requests')
        self.request_duration_summary = Summary('app_request_duration_seconds', 'Time spent processing request')

    def record_request(self, success: bool):
        self.request_counter.inc()
        if success:
            self.successful_requests_counter.inc()
        else:
            self.failed_requests_counter.inc()

    def setup_prometheus(self):
        start_http_server(8000)

    def start_request_timer(self):
        self.start_time = time.time()
    
    def stop_request_timer(self):
        self.request_duration_summary.observe(time.time() - self.start_time)