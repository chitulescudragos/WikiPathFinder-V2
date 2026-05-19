import requests
import os
from collections import deque
from flask import Flask, render_template, request, send_from_directory, redirect, url_for
from pyvis.network import Network

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
if not os.path.exists(TEMPLATES_DIR):
    os.makedirs(TEMPLATES_DIR)

blacklist = ("Category:", "File:", "Image:", "Help:", "Special:", "Template:", "Portal:", "Wikipedia:")

cache = {}
verified_backedges = set()
back_cache = {}


state = {
    "queue_s": deque(),
    "queue_t": deque(),
    "visited_s": {},
    "visited_t": {},
    "start": "",
    "target": "",
    "nodes_counter": 0,
    "active": False
}


def get_links(page):
    if page in cache: return cache[page]
    cache[page] = valid_links(page)
    return cache[page]


def get_backlinks(page):
    if page in back_cache: return back_cache[page]
    back_cache[page] = valid_backlinks(page)
    return back_cache[page]


def valid_links(page_title):
    URL = "https://en.wikipedia.org/w/api.php"
    header = {"User-Agent": "WikiFinderBot/0.1 (EDU project; student; chitulescudragos@gmail.com)"}
    links = []
    param = {"action": "query", "titles": page_title, "prop": "links", "plnamespace": 0, "pllimit": "max",
             "format": "json"}
    while True:
        try:
            response = requests.get(URL, params=param, headers=header, timeout=5)
        except:
            break
        if response.status_code != 200: break
        try:
            data = response.json()
        except:
            break
        query = data.get("query")
        if not query: break
        for page in query.get("pages", {}).values():
            if "links" in page:
                for link in page["links"]:
                    title = link["title"].split("#")[0]
                    if title.startswith(blacklist) or title.startswith("."): continue
                    links.append(title)
        cont = data.get("continue")
        if not cont: break
        param.update(cont)
    return list(set(links))


def is_disambiguation(page_title):
    URL = "https://en.wikipedia.org/w/api.php"
    header = {"User-Agent": "WikiFinderBot/0.1 (EDU project; student; chitulescudragos@gmail.com)"}
    param = {"action": "query", "titles": page_title, "prop": "categories", "cllimit": "max", "format": "json"}
    try:
        response = requests.get(URL, params=param, headers=header, timeout=5)
        pages = response.json().get("query", {}).get("pages", {})
        for page in pages.values():
            for categ in page.get("categories", []):
                if "disambiguation pages" in categ["title"].lower(): return True
    except:
        pass
    return False


def valid_backlinks(page_title):
    URL = "https://en.wikipedia.org/w/api.php"
    header = {"User-Agent": "WikiFinderBot/0.1 (EDU project; student; chitulescudragos@gmail.com)"}
    backlinks = []
    param = {"action": "query", "bltitle": page_title, "list": "backlinks", "blnamespace": 0,
             "blfilterredir": "nonredirects", "bllimit": "max", "format": "json"}
    while True:
        try:
            response = requests.get(URL, params=param, headers=header, timeout=5)
        except:
            break
        if response.status_code != 200: break
        try:
            data = response.json()
        except:
            break
        query = data.get("query")
        if not query: break
        for backlink in query.get("backlinks", []):
            title = backlink["title"].split("#")[0]
            if title.startswith(blacklist) or title.startswith("."): continue
            backlinks.append(title)
        cont = data.get("continue")
        if not cont: break
        param.update(cont)
    return list(set(backlinks))


def intersection(meet_point, visited_s, visited_t):
    path_s, node = [], meet_point
    while node: path_s.append(node); node = visited_s[node]
    path_s.reverse()
    path_t, node = [], visited_t[meet_point]
    while node: path_t.append(node); node = visited_t[node]
    return path_s + path_t


def generate_visual_graph(path):
    net = Network(height="600px", width="100%", directed=True, bgcolor="#ffffff", font_color="black")
    for node in path: net.add_node(node, label=node, color="#0d6efd", size=25)
    for i in range(len(path) - 1): net.add_edge(path[i], path[i + 1], color="#adb5bd")
    net.save_graph(os.path.join(TEMPLATES_DIR, 'wiki_graph.html'))


@app.route('/')
def index():
    return render_template('index.html', loading=False)


@app.route('/find', methods=['POST'])
def find():
    state["start"] = request.form.get('start')
    state["target"] = request.form.get('target')
    state["queue_s"] = deque([state["start"]])
    state["queue_t"] = deque([state["target"]])
    state["visited_s"] = {state["start"]: None}
    state["visited_t"] = {state["target"]: None}
    state["nodes_counter"] = 0
    state["active"] = True

    return redirect(url_for('step'))


@app.route('/step')
def step():
    if not state["active"]:
        return redirect(url_for('index'))


    if not state["queue_s"] and not state["queue_t"]:
        state["active"] = False
        return render_template('index.html', error="Nu s-a găsit niciun drum.", loading=False)


    if state["queue_s"] and (not state["queue_t"] or len(state["queue_s"]) <= len(state["queue_t"])):
        current = state["queue_s"].popleft()
        if not is_disambiguation(current):
            state["nodes_counter"] += 1
            print(f"[START -> TARGET] Current: {current} | Total: {state['nodes_counter']}", flush=True)

            try:
                for nbh in get_links(current):
                    if nbh not in state["visited_s"]:
                        state["visited_s"][nbh] = current
                        state["queue_s"].append(nbh)
                        print(f"  [+] Găsit link: {nbh}", flush=True)
                        if nbh in state["visited_t"]:
                            state["active"] = False
                            path = intersection(nbh, state["visited_s"], state["visited_t"])
                            generate_visual_graph(path)
                            return render_template('result.html', path=path)
            except TypeError:
                pass
    else:
        current = state["queue_t"].popleft()
        if not is_disambiguation(current):
            state["nodes_counter"] += 1
            print(f"[TARGET -> START] Current: {current} | Total: {state['nodes_counter']}", flush=True)

            try:
                for bnbh in get_backlinks(current):
                    print(f"  [-] Verificăm backlink: {bnbh}", flush=True)
                    pair = (bnbh, current)
                    if pair in verified_backedges:
                        is_true = True
                    else:
                        try:
                            if current in set(get_links(bnbh)):
                                verified_backedges.add(pair)
                                is_true = True
                            else:
                                is_true = False
                        except TypeError:
                            continue
                    if not is_true: continue

                    if bnbh not in state["visited_t"]:
                        state["visited_t"][bnbh] = current
                        state["queue_t"].append(bnbh)
                        if bnbh in state["visited_s"]:
                            state["active"] = False
                            path = intersection(bnbh, state["visited_s"], state["visited_t"])
                            generate_visual_graph(path)
                            return render_template('result.html', path=path)
            except TypeError:
                pass


    return render_template('index.html', loading=True, counter=state["nodes_counter"])


@app.route('/graph')
def graph():
    return send_from_directory(TEMPLATES_DIR, 'wiki_graph.html')


if __name__ == '__main__':
    app.run(debug=True)