from flask import Flask, request, Response
import requests
import time

TARGET_SERVER = "http://127.0.0.1:5000"
CACHE_TTL = 30  # sekund

# Hlavičky, které nesmíme přeposílat klientovi (způsobují konflikty)
HOP_BY_HOP_HEADERS = {
    'transfer-encoding', 'connection', 'keep-alive',
    'proxy-authenticate', 'proxy-authorization', 'te',
    'trailers', 'upgrade', 'content-encoding'
}

app = Flask(__name__, static_folder=None)  # dulezite - vypnete static folder

# cache jako dictionary: key -> (content, headers, status_code, timestamp)
cache = {}


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):

    url = f"{TARGET_SERVER}/{path}"
    method = request.method
    key = f"{method}:{url}"

    if key in cache:
        content, headers, status, timestamp = cache[key]
        age = time.time() - timestamp

        if age <= CACHE_TTL:
            # Zaznam je stale platny - HIT
            resp = Response(content, status=status)
            resp.headers.update(headers)
            resp.headers['X-Cache'] = 'HIT'
            resp.headers['X-Cache-Age'] = str(int(age))
            return resp
        else:
            # Zaznam expiroval - smazeme ho a nacteme cerstva data
            del cache[key]

    if method == 'GET':
        r = requests.get(url, params=request.args)
    else:
        raise NotImplementedError(f"Metoda {method} není podporována")

    # Filtrujeme problematicke hop-by-hop hlavicky
    filtered_headers = {
        k: v for k, v in r.headers.items()
        if k.lower() not in HOP_BY_HOP_HEADERS
    }

    # Ulozime do cache i cas ulozeni
    cache[key] = (r.content, filtered_headers, r.status_code, time.time())

    # Vratime klientovi s X-Cache: MISS a X-Cache-Age: 0
    resp = Response(r.content, status=r.status_code)
    resp.headers.update(filtered_headers)
    resp.headers['X-Cache'] = 'MISS'
    resp.headers['X-Cache-Age'] = '0'
    return resp


if __name__ == "__main__":
    app.run(port=5001, debug=True)