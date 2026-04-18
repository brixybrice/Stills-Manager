# Stills Manager

A local web app for browsing and selecting image stills from a shoot. Runs entirely on your machine — no cloud, no upload.

![Python](https://img.shields.io/badge/Python-3.9%2B-grey) ![Flask](https://img.shields.io/badge/Flask-3.0-grey)

---

## Features

- **Browse** any local folder containing JPG, PNG or TIF images
- **Gallery** view with 16:9 thumbnails, up to 6 columns
- **Lightbox** — Cmd+click (or the ⤢ button) to view full size; navigate with arrow keys
- **Selections** — click a thumbnail to add/remove it; spacebar works in lightbox
- **Multiple selections** via tabs — add, rename (double-click), reorder and delete
- **Drag & drop** reordering of images within a selection
- **Export to PDF** — one image per page, 16:9 landscape, page sized to the image
- **Auto-save** — selections are written as `stills-selections.json` directly in the open folder, debounced at 350 ms
- Remembers the last browsed folder between sessions

---

## Requirements

- Python 3.9+
- Flask 3.0+

---

## Installation

```bash
git clone <repo>
cd Stills-Manager
pip install -r requirements.txt
```

---

## Usage

```bash
python server.py
```

The app opens automatically at `http://localhost:5000`. Stop the server with **Ctrl+C**.

> Works best in **Firefox** or any modern browser. The Safari / Chrome File System Access API is not used — all file operations go through the local Flask server.

---

## Keyboard shortcuts

| Key | Action |
|-----|--------|
| `Space` | Add / remove current image from selection (lightbox) |
| `←` / `→` | Navigate images (lightbox) |
| `Escape` | Close lightbox |
| `Cmd+click` | Open image in lightbox (gallery) |

---

## Data

Selections are saved as a JSON file (`stills-selections.json`) in the open folder:

```json
{
  "Folder name": ["img_001.jpg", "img_004.jpg"],
  "Selection 2": ["img_010.jpg"]
}
```

The file is created automatically when a folder is opened and updated on every change.

---

## Project structure

```
Stills-Manager/
├── server.py        # Flask server — API + static serving
├── index.html       # Single-page app (HTML + CSS + JS)
└── requirements.txt
```
