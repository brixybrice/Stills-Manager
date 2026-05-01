from flask import Flask, jsonify, request, send_from_directory, send_file
import os, json, re, threading, webbrowser, base64, io, subprocess, sys

try:
    from PIL import Image
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'Pillow'], stdout=subprocess.DEVNULL)
    from PIL import Image

app = Flask(__name__, static_folder='.', static_url_path='')
current_dir    = None
recursive_mode = False
IMAGE_EXTS     = {'.jpg', '.jpeg', '.png', '.tif', '.tiff'}
JSON_FILE      = '.stills-selections.json'

def nat_key(s):
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]

# ── Static ────────────────────────────────────────────────────────────────
@app.route('/')
@app.route('/stills')
@app.route('/report')
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
        img_count = sum(1 for f in os.listdir(path)
                        if os.path.splitext(f)[1].lower() in IMAGE_EXTS)
        return jsonify({'path': path, 'parent': parent if parent != path else None,
                        'dirs': dirs, 'image_count': img_count})
    except PermissionError:
        return jsonify({'path': path, 'parent': os.path.dirname(path), 'dirs': [], 'error': 'Permission denied'})

# ── Open folder ───────────────────────────────────────────────────────────
@app.route('/api/open', methods=['POST'])
def open_dir():
    global current_dir, recursive_mode
    path = os.path.abspath(os.path.expanduser(request.json.get('path', '')))
    if not os.path.isdir(path):
        return jsonify({'error': 'Not a directory'}), 400
    current_dir    = path
    recursive_mode = bool(request.json.get('recursive', False))
    return jsonify({'ok': True, 'path': path, 'name': os.path.basename(path), 'recursive': recursive_mode})

# ── List images ───────────────────────────────────────────────────────────
@app.route('/api/images')
def list_images():
    if not current_dir:
        return jsonify({'error': 'No folder open'}), 400
    images = []
    if recursive_mode:
        for root, dirs, files in os.walk(current_dir):
            dirs[:] = sorted([d for d in dirs if not d.startswith('.')], key=nat_key)
            for name in sorted(files, key=nat_key):
                if os.path.splitext(name)[1].lower() in IMAGE_EXTS:
                    rel = os.path.relpath(os.path.join(root, name), current_dir)
                    images.append(rel)
    else:
        images = [n for n in os.listdir(current_dir)
                  if os.path.splitext(n)[1].lower() in IMAGE_EXTS]
        images.sort(key=nat_key)
    return jsonify({'images': images, 'folder': current_dir, 'name': os.path.basename(current_dir)})

# ── Serve image ───────────────────────────────────────────────────────────
@app.route('/api/image/<path:filename>')
def get_image(filename):
    if not current_dir:
        return jsonify({'error': 'No folder open'}), 400
    ext = os.path.splitext(filename)[1].lower()
    if ext in ('.tif', '.tiff'):
        try:
            full = os.path.join(current_dir, filename)
            with Image.open(full) as img:
                img = img.convert('RGB')
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=92)
                buf.seek(0)
            return send_file(buf, mimetype='image/jpeg')
        except Exception as e:
            return jsonify({'error': str(e)}), 500
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

# ── Stills metadata ──────────────────────────────────────────────────────
@app.route('/api/metadata')
def get_metadata():
    if not current_dir:
        return jsonify(None), 200
    combined = {}
    walk_dirs = []
    if recursive_mode:
        for root, dirs, _ in os.walk(current_dir):
            dirs[:] = sorted([d for d in dirs if not d.startswith('.')], key=nat_key)
            walk_dirs.append(root)
    else:
        walk_dirs = [current_dir]
    try:
        for dirpath in walk_dirs:
            for name in sorted(os.listdir(dirpath)):
                if not name.startswith('.'):
                    continue
                if not (name.endswith('_clips.json') or name.endswith('_stills_metadata.json')):
                    continue
                p = os.path.join(dirpath, name)
                try:
                    with open(p, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if 'clips' in data:
                        combined.setdefault('clips', []).extend(data['clips'])
                        if 'timeline' not in combined:
                            combined['timeline'] = data.get('timeline', '')
                    if 'markers_metadata' in data:
                        combined.setdefault('markers_metadata', {}).update(data['markers_metadata'])
                except Exception:
                    pass
    except Exception:
        pass
    return jsonify(combined if combined else None), 200

# ── Save exported file ───────────────────────────────────────────────────
@app.route('/api/save-file', methods=['POST'])
def save_file():
    data     = request.json or {}
    dir_path = os.path.expanduser(data.get('path', ''))
    filename = data.get('filename', '')
    data_uri = data.get('data', '')
    subfolder= data.get('subfolder', '').strip()

    if not dir_path or not filename:
        return jsonify({'error': 'Missing path or filename'}), 400

    target = os.path.join(dir_path, subfolder) if subfolder else dir_path
    try:
        os.makedirs(target, exist_ok=True)
        full_path = os.path.join(target, filename)
        if ',' in data_uri:
            raw = base64.b64decode(data_uri.split(',', 1)[1])
        else:
            raw = base64.b64decode(data_uri)
        with open(full_path, 'wb') as f:
            f.write(raw)
        return jsonify({'ok': True, 'path': full_path})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── Start ─────────────────────────────────────────────────────────────────
def _open_browser():
    import time; time.sleep(0.9)
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    print('\n  Stills Manager → http://127.0.0.1:5000\n  Ctrl+C to stop\n')
    threading.Thread(target=_open_browser, daemon=True).start()
    app.run(host='127.0.0.1', port=5000, debug=False)
