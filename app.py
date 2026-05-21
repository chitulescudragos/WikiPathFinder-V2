import requests
import os
import json
from collections import deque
from flask import Flask, render_template, request, send_from_directory, redirect, url_for
from pyvis.network import Network

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')

if not os.path.exists(TEMPLATES_DIR): os.makedirs(TEMPLATES_DIR)

HISTORY_FILE = os.path.join(BASE_DIR, 'history.json')
blacklist = ("Category:", "File:", "Image:", "Help:", "Special:", "Template:", "Portal:", "Wikipedia:")

cache = {}
verified_backedges = set()
back_cache = {}

state = {
    "queue_s": deque(), "queue_t": deque(),
    "visited_s": {}, "visited_t": {},
    "start": "", "target": "",
    "nodes_counter": 0, "active": False
}


def load_history():
    if not os.path.exists(HISTORY_FILE): return []
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []


def save_to_history(start, target, path):
    history = load_history()
    for item in history:
        if item['start'].lower() == start.lower() and item['target'].lower() == target.lower(): return

    history.insert(0, {"start": start, "target": target, "path": path})
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history[:15], f, ensure_ascii=False, indent=4)


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
        data = response.json()
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
        data = response.json()
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
    net = Network(height="800px", width="100%", directed=True, bgcolor="#ffffff", font_color="black")
    path_set = set(path)
    added_nodes = set()

    for index, node in enumerate(path):
        net.add_node(node, label=node, color="#00ff66", size=40, borderWidth=4, shape="ellipse", level=index)
        added_nodes.add(node)

    for i in range(len(path) - 1): net.add_edge(path[i], path[i + 1], color="#00ff66", width=6)

    current_level_red_nodes = []

    for index, node in enumerate(path):
        if index == len(path) - 1: break
        next_level_red_nodes = []

        try:
            for nbh in [n for n in get_links(node) if n not in path_set and n not in added_nodes][:5]:
                net.add_node(nbh, label=nbh, color="#e63946", size=20, shape="dot", level=index + 1)
                net.add_edge(node, nbh, color="#e63946", width=1, dashes=True)
                next_level_red_nodes.append(nbh);
                added_nodes.add(nbh)
        except:
            pass

        for red_node in current_level_red_nodes:
            try:
                for nbh in [n for n in get_links(red_node) if n not in path_set and n not in added_nodes][:5]:
                    net.add_node(nbh, label=nbh, color="#e63946", size=20, shape="dot", level=index + 1)
                    net.add_edge(red_node, nbh, color="#e63946", width=1, dashes=True)
                    next_level_red_nodes.append(nbh);
                    added_nodes.add(nbh)
            except:
                pass
        current_level_red_nodes = next_level_red_nodes

    net.set_options(
        '{"layout":{"hierarchical":{"enabled":true,"levelSeparation":150,"nodeSpacing":80,"treeSpacing":100,"blockShifting":true,"edgeMinimization":true,"parentCentralization":true,"direction":"UD","sortMethod":"directed"}},"physics":{"enabled":false}}')
    net.save_graph(os.path.join(TEMPLATES_DIR, 'wiki_graph.html'))


@app.route('/')
def index(): return render_template('index.html', loading=False, history=load_history())


@app.route('/history')
def history_page(): return render_template('history.html', history=load_history())


@app.route('/find', methods=['POST'])
def find():
    state.update({"start": request.form.get('start'), "target": request.form.get('target'),
                  "queue_s": deque([request.form.get('start')]), "queue_t": deque([request.form.get('target')]),
                  "visited_s": {request.form.get('start'): None}, "visited_t": {request.form.get('target'): None},
                  "nodes_counter": 2, "active": True})
    return redirect(url_for('step'))


@app.route('/step')
def step():
    if not state["active"]: return redirect(url_for('index'))
    if not state["queue_s"] and not state["queue_t"]:
        state["active"] = False
        return render_template('index.html', error="Nu s-a găsit drumul.", loading=False, history=load_history())

    if state["queue_s"] and (not state["queue_t"] or len(state["queue_s"]) <= len(state["queue_t"])):
        current = state["queue_s"].popleft()
        if not is_disambiguation(current):
            print(f"[START -> TARGET] Current: {current} | Total: {state['nodes_counter']}", flush=True)
            try:
                for nbh in get_links(current):
                    if nbh not in state["visited_s"]:
                        state["visited_s"][nbh] = current
                        state["queue_s"].append(nbh)
                        state["nodes_counter"] += 1
                        print(f"  [+] Găsit link: {nbh} | Total: {state['nodes_counter']}", flush=True)

                        if nbh in state["visited_t"]:
                            path = intersection(nbh, state["visited_s"], state["visited_t"])
                            save_to_history(state["start"], state["target"], path)
                            state["active"] = False
                            generate_visual_graph(path)
                            return render_template('result.html', path=path)
            except:
                pass
    else:
        current = state["queue_t"].popleft()
        if not is_disambiguation(current):
            print(f"[TARGET -> START] Current: {current} | Total: {state['nodes_counter']}", flush=True)

            try:
                for bnbh in get_backlinks(current):


                    if (bnbh, current) in verified_backedges or current in set(get_links(bnbh)):
                        verified_backedges.add((bnbh, current))
                        if bnbh not in state["visited_t"]:
                            state["visited_t"][bnbh] = current
                            state["queue_t"].append(bnbh)
                            state["nodes_counter"] += 1
                            print(f"  [+] Găsit backlink: {bnbh} | Total: {state['nodes_counter']}", flush=True)

                            if bnbh in state["visited_s"]:
                                path = intersection(bnbh, state["visited_s"], state["visited_t"])
                                save_to_history(state["start"], state["target"], path)
                                state["active"] = False
                                generate_visual_graph(path)
                                return render_template('result.html', path=path)
            except:
                pass

    return render_template('index.html', loading=True, counter=state["nodes_counter"], history=load_history())


@app.route('/view_history/<int:item_index>')
def view_history(item_index):
    history = load_history()
    if 0 <= item_index < len(history):
        generate_visual_graph(history[item_index]['path'])
        return render_template('result.html', path=history[item_index]['path'])
    return redirect(url_for('index'))


@app.route('/graph')
def graph(): return send_from_directory(TEMPLATES_DIR, 'wiki_graph.html')


if __name__ == '__main__': app.run(debug=True)