import requests
import time
import os
from collections import deque
from flask import Flask, render_template, request, send_from_directory
from pyvis.network import Network

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
if not os.path.exists(TEMPLATES_DIR):
    os.makedirs(TEMPLATES_DIR)

blacklist = (
    "Category:", "File:", "Image:", "Help:", "Special:", "Template:", "Portal:", "Wikipedia:"
)

cache = {}
verified_backedges = set()
back_cache = {}


def get_links(page):
    if page in cache:
        return cache[page]
    cache[page] = valid_links(page)
    return cache[page]


def get_backlinks(page):
    if page in back_cache:
        return back_cache[page]
    back_cache[page] = valid_backlinks(page)
    return back_cache[page]


def valid_links(page_title):
    URL = "https://en.wikipedia.org/w/api.php"
    header = {"User-Agent": "WikiFinderBot/0.1"}

    links = []
    param = {"action": "query", "titles": page_title, "prop": "links", "plnamespace": 0, "pllimit": "max",
             "format": "json"}

    while True:
        try:
            response = requests.get(URL, params=param, headers=header, timeout=5)
        except Exception as e:
            print("Request failed:", e)
            break

        if response.status_code != 200:
            print("Bad status:", response.status_code)
            break

        try:
            data = response.json()
        except Exception as e:
            print("JSON error:", e)
            break

        query = data.get("query")
        if not query: break

        pages = query.get("pages", {})
        for page in pages.values():
            if "links" in page:
                for link in page["links"]:
                    title = link["title"].split("#")[0]
                    if title.startswith(blacklist) or title.startswith("."):
                        continue
                    links.append(title)

        cont = data.get("continue")
        if not cont: break
        param.update(cont)

    return list(set(links))


def is_disambiguation(page_title):
    URL = "https://en.wikipedia.org/w/api.php"
    header = {"User-Agent": "WikiFinderBot/0.1"}
    param = {"action": "query", "titles": page_title, "prop": "categories", "cllimit": "max", "format": "json"}

    try:
        response = requests.get(URL, params=param, headers=header, timeout=5)
        data = response.json()
    except:
        return False

    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        categs = page.get("categories", [])
        for categ in categs:
            if "disambiguation pages" in categ["title"].lower():
                return True
    return False


def valid_backlinks(page_title):
    URL = "https://en.wikipedia.org/w/api.php"
    header = {"User-Agent": "WikiFinderBot/0.1"}
    backlinks = []
    param = {"action": "query", "bltitle": page_title, "list": "backlinks", "blnamespace": 0,
             "blfilterredir": "nonredirects", "bllimit": "max", "format": "json"}

    while True:
        try:
            response = requests.get(URL, params=param, headers=header, timeout=5)
        except Exception as e:
            print("Request failed:", e)
            break

        if response.status_code != 200:
            print("Bad status:", response.status_code)
            break

        try:
            data = response.json()
        except Exception as e:
            print("JSON error:", e)
            break

        query = data.get("query")
        if not query: break

        for backlink in query.get("backlinks", []):
            title = backlink["title"].split("#")[0]
            if title.startswith(blacklist) or title.startswith("."):
                continue
            backlinks.append(title)

        cont = data.get("continue")
        if not cont: break
        param.update(cont)

    return list(set(backlinks))


def find_path(start, target):
    queue_s = deque([start])
    queue_t = deque([target])
    visited_s = {start: None}
    visited_t = {target: None}

    while queue_t and queue_s:
        if len(queue_s) <= len(queue_t):
            current = queue_s.popleft()

            if is_disambiguation(current):
                continue

            # AFIȘARE ÎN CONSOLĂ INSTANT (flush=True)
            print(f"[START -> TARGET] Current: {current}", flush=True)

            try:
                for nbh in get_links(current):
                    if nbh not in visited_s:
                        visited_s[nbh] = current
                        queue_s.append(nbh)
                        if nbh in visited_t:
                            return intersection(nbh, visited_s, visited_t)
            except TypeError:
                pass
        else:
            current = queue_t.popleft()

            if is_disambiguation(current):
                continue

            # AFIȘARE ÎN CONSOLĂ INSTANT (flush=True)
            print(f"[TARGET -> START] Current: {current}", flush=True)

            try:
                for bnbh in get_backlinks(current):
                    # print(bnbh, flush=True) # Opțional, dacă vrei să afișezi și backlink-urile parcurse
                    pair = (bnbh, current)
                    if pair in verified_backedges:
                        is_true_backedge = True
                    else:
                        try:
                            fwd_links = get_links(bnbh)
                            if current in set(fwd_links):
                                verified_backedges.add(pair)
                                is_true_backedge = True
                            else:
                                is_true_backedge = False
                        except TypeError:
                            continue

                    if not is_true_backedge: continue

                    if bnbh not in visited_t:
                        visited_t[bnbh] = current
                        queue_t.append(bnbh)
                        if bnbh in visited_s:
                            return intersection(bnbh, visited_s, visited_t)
            except TypeError:
                pass
    return None


def intersection(meet_point, visited_s, visited_t):
    path_s = []
    node = meet_point
    while node is not None:
        path_s.append(node)
        node = visited_s[node]
    path_s.reverse()

    path_t = []
    node = visited_t[meet_point]
    while node is not None:
        path_t.append(node)
        node = visited_t[node]

    return path_s + path_t


def generate_visual_graph(path):
    net = Network(height="600px", width="100%", directed=True, bgcolor="#ffffff", font_color="black")
    for node in path:
        net.add_node(node, label=node, color="#0d6efd", size=25)
    for i in range(len(path) - 1):
        net.add_edge(path[i], path[i + 1], color="#adb5bd")
    net.save_graph(os.path.join(TEMPLATES_DIR, 'wiki_graph.html'))


# --- RUTELE FLASK ---
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/find', methods=['POST'])
def find():
    start = request.form.get('start')
    target = request.form.get('target')

    print(f"\n=== SE CAUTĂ DRUMUL: {start} -> {target} ===", flush=True)

    path = find_path(start, target)

    if path:
        print(f"\n=== DRUM GĂSIT ===\n{path}\n", flush=True)
        generate_visual_graph(path)
        return render_template('result.html', path=path, start=start, target=target)

    print("\n=== NU S-A GĂSIT NICIUN DRUM ===\n", flush=True)
    return render_template('index.html', error="Nu s-a găsit niciun drum. Verifică datele introduse.")


@app.route('/graph')
def graph():
    return send_from_directory(TEMPLATES_DIR, 'wiki_graph.html')


if __name__ == '__main__':
    app.run(debug=True)