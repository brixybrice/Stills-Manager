# Stills Manager

A local web app for browsing and curating image stills from a shoot. Runs entirely on your machine — no cloud, no upload.

![Python](https://img.shields.io/badge/Python-3.9%2B-grey) ![Flask](https://img.shields.io/badge/Flask-3.0-grey)

---

## Features

- **Browse** any local folder containing JPG, PNG or TIF images
- **Gallery** view with 16:9 thumbnails, up to 6 columns
- **Fullscreen lightbox** — Cmd+click to view full size; vertical carousel shows surrounding images
- **Selections** — click a thumbnail to add/remove it; spacebar works in fullscreen
- **Multiple selections** via tabs — add, rename (double-click), reorder and delete
- **Drag & drop** reordering of images within a selection
- **Reorder from fullscreen** — move the current image up or down in the selection without leaving fullscreen
- **Contact sheet** — configurable grid export (JPG, PNG or PDF) with live preview
- **Watermark** — tiled text overlay with font, size, opacity and angle controls; applied to PDF and contact sheet exports
- **Export to PDF** — one image per page, 16:9 landscape
- **Undo / Redo** — full history for all selection edits (Cmd+Z / Cmd+Shift+Z)
- **Auto-save** — selections written as `stills-selections.json` in the open folder, debounced at 350 ms
- **URL persistence** — the open folder is encoded in the URL; reloading the page reopens it automatically

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

> Works best in **Firefox** or any modern browser. All file operations go through the local Flask server — no browser File System Access API required.

---

## Keyboard shortcuts

| Key | Action |
|-----|--------|
| `←` / `↑` | Previous image (fullscreen) |
| `→` / `↓` | Next image (fullscreen) |
| `Space` | Add / remove from selection (fullscreen) |
| `Cmd+↑` | Move image up in selection (fullscreen) |
| `Cmd+↓` | Move image down in selection (fullscreen) |
| `Escape` | Close fullscreen or modal |
| `Cmd+Z` | Undo |
| `Cmd+Shift+Z` | Redo |
| `Cmd+click` | Open image in fullscreen (gallery) |

---

## Data

Selections are saved as a JSON file (`stills-selections.json`) in the open folder:

```json
{
  "selections": {
    "Folder name": ["img_001.jpg", "img_004.jpg"],
    "Selection 2": ["img_010.jpg"]
  },
  "selOrder": ["Folder name", "Selection 2"],
  "activeSel": "Folder name"
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
