import urllib.request

class HTTPRedirectHandler(urllib.request.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        print("302 Redirection")
        print(headers['Location'])
        #return urllib.request.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)
        return headers['Location']

    #http_error_301 = http_error_303 = http_error_307 = http_error_302

