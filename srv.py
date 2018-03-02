import http.server
import socketserver


class TestingServer(http.server.BaseHTTPRequestHandler):

    def do_POST(self):
        print("{dtstring}: {reqline}".format(
            dtstring=self.date_time_string(),
            reqline=self.requestline
        ))
        print("Request Data:")
        print("{}".format(self.rfile.peek()))
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        # self.wfile.write(b"Data Received successfully\n")
        # self.wfile.close()

    def do_GET(self):
        print("{dtstring}: {http} {reqline}".format(
            dtstring=self.date_time_string(),
            http=self.request_version,
            reqline=self.requestline
        ))
        print("Does not handle {}".format(self.command))
        self.send_error(405, "Only send POST Requests")
        self.end_headers()

    def do_PUT(self):
        self.do_GET()

    def do_HEAD(self):
        self.do_GET()


with socketserver.TCPServer(("", 8000), TestingServer) as httpd:
    print("Test server operating on {port}".format(port=8000))
    httpd.serve_forever()
