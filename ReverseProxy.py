from flask import Flask, request, Response
import requests

TARGET_SERVER = "http://127.0.0.1:5000"


app = Flask(__name__,  static_folder=None) #dulezite - vypnete static folder

cache = {} # cache jako dictionary

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):

    url = f"{TARGET_SERVER}/{path}"
    method = request.method
    key = f"{method}:{url}"

    if key in cache:
        content, headers, status = cache[key]
        resp = Response(content, status=status)
        resp.headers.update(headers)
        resp.headers['X-Cache'] = 'HIT'
        return resp

    if method == 'GET':
        r = requests.get(url, params=request.args)
    else:
        raise NotImplemented()

    cache[key] = (r.content, dict(r.headers), r.status_code)
    
    # Vrátíme klientovi s X-Cache: MISS
    resp = Response(r.content, status=r.status_code)
    resp.headers.update(r.headers)
    resp.headers['X-Cache'] = 'MISS'
    return resp

if __name__ == "__main__":
    app.run(port=5001)