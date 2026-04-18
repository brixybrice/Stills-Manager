from flask import Flask, jsonify, request, send_from_directory
import os, json, re, threading, webbrowser

app = Flask(__name__, static_folder='.', static_url_path='')
current_dir  = None
IMAGE_EXTS   = {'.jpg', '.jpeg', '.png', '.tif', '.tiff'}
JSON_FILE    = 'stills-selections.json'

def nat_key(s):
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]

# ── Static ────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# ── Browse filesystem ─────────────────────────────────────────────────────
@app.route('/api/browse')
def browse():
    path = request.args.get('path', os.path.expanduser('~'))
    path = os.path.abspath(os.path.expanduser(path))
    if not os.path.isdir(path):
        path = os.path.dirname(path)
    try:
        dirs = []
        for name in sorted(os.listdir(path), key=nat_key):
            if name.startswith('.'): continue
            full = os.path.join(path, name)
            if os.path.isdir(full):
                dirs.append({'name': name, 'path': full})
        parent = os.path.dirname(path)
        return jsonify({'path': path, 'parent': parent if parent != path else None, 'dirs': dirs})
    except PermissionError:
        return jsonify({'path': path, 'parent': os.path.dirname(path), 'dirs': [], 'error': 'Permission denied'})

# ── Open folder ───────────────────────────────────────────────────────────
@app.route('/api/open', methods=['POST'])
def open_dir():
    global current_dir
    path = os.path.abspath(os.path.expanduser(request.json.get('path', '')))
    if not os.path.isdir(path):
        return jsonify({'error': 'Not a directory'}), 400
    current_dir = path
    return jsonify({'ok': True, 'path': path, 'name': os.path.basename(path)})

# ── List images ───────────────────────────────────────────────────────────
@app.route('/api/images')
def list_images():
    if not current_dir:
        return jsonify({'error': 'No folder open'}), 400
    images = [n for n in os.listdir(current_dir)
              if os.path.splitext(n)[1].lower() in IMAGE_EXTS]
    images.sort(key=nat_key)
    return jsonify({'images': images, 'folder': current_dir, 'name': os.path.basename(current_dir)})

# ── Serve image ───────────────────────────────────────────────────────────
@app.route('/api/image/<path:filename>')
def get_image(filename):
    if not current_dir:
        return jsonify({'error': 'No folder open'}), 400
    return send_from_directory(current_dir, filename)

# ── Selections ────────────────────────────────────────────────────────────
@app.route('/api/selections', methods=['GET'])
def get_selections():
    if not current_dir:
        return jsonify({}), 200
    p = os.path.join(current_dir, JSON_FILE)
    if os.path.exists(p):
        try:
            with open(p, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        except Exception:
            pass
    return jsonify({})

@app.route('/api/selections', methods=['POST'])
def save_selections():
    if not current_dir:
        return jsonify({'error': 'No folder open'}), 400
    p = os.path.join(current_dir, JSON_FILE)
    try:
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(request.json, f, indent=2, ensure_ascii=False)
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── Start ─────────────────────────────────────────────────────────────────
def _open_browser():
    import time; time.sleep(0.9)
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    print('\n  Stills Manager → http://localhost:5000\n  Ctrl+C to stop\n')
    threading.Thread(target=_open_browser, daemon=True).start()
    app.run(host='127.0.0.1', port=5000, debug=False)
