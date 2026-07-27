# Stills Manager — CLAUDE.md

## Architecture

Single-page Flask app. **Tout le code UI est dans `index.html`** (~4750 lignes). Pas de build step, pas de framework JS.

```
Stills-Manager/
├── server.py        # Flask backend — API + file-save endpoint
├── index.html       # HTML + CSS + JS (tout en un)
├── vendor/
│   ├── sortable.min.js
│   └── jspdf.umd.min.js
└── requirements.txt
```

Le serveur tourne sur `http://localhost:5000`. Lancer avec `python server.py`.

---

## État global (JS)

```javascript
allImages   // filenames dans le dossier ouvert
selections  // { tabName: [filename, ...] }
selOrder    // ordre des onglets
activeSel   // onglet actif

lbImages / lbIdx / lbContext  // état du lightbox
lbMultiSel  // Set() de filenames pour le déplacement en groupe (lightbox)
lbCompareMode / lbCompareNameA  // mode A/B

clipsMetadata   // objet chargé depuis ._stills_metadata.json ou ._clips.json
folderName      // nom du dossier ouvert
mainView        // 'gallery' | 'report'

cumulMode       // boolean — mode over-selection (galerie des sélections agrégées)
allImagesBase   // liste non-triée (source de vérité avant sort)
sortMode        // 'none' | 'alpha' | 'scene' | 'date'
fileDates       // { relPath: mtime } chargé depuis /api/file-dates pour le tri Date
```

---

## Persistence

| Donnée | Stockage |
|--------|----------|
| Sélections | `.stills-selections.json` dans le dossier ouvert (auto-save 350ms) |
| Paramètres Contact Sheet | `localStorage` clé `stills-cs-settings` |
| Chemins d'export | `localStorage` clé `stills-paths` |
| Données production | `localStorage` clé `stills-production` |
| Options export modal | `localStorage` clé `stills-export-opts` |
| Thème | `localStorage` clé `stills-theme` |
| Préférences thumbs clips | `localStorage` clé `stills-thumb-prefs` |

---

## Fonctions clés par domaine

### Sélections / onglets
- `curSel()` — tableau de la sélection active
- `toggleInSel(name)` / `removeFromSel(name)` / `clearSel()`
- `addNewSel()` — crée un onglet en **dupliquant** la sélection courante
- `switchSel(name)` / `renameSel()` / `deleteSel()`
- `pushHistory()` / `undo()` / `redo()` — undo/redo complet

### Rendu
- `renderAll()` → `renderTabs()` + `renderGallery()` + `renderSelection()`
- `queueSave()` — debounce 350ms → POST `/api/selections`

### Sort & Cumul
- `setSortMode(mode)` — trie `allImages` à partir de `allImagesBase` ; clic sur le bouton actif désélectionne
- `getImageScene(filepath)` — matching filename → marker → `metadata.Scene` via `getMarkerLookup()`
- `enterCumulMode()` / `exitCumulMode()` / `toggleCumulMode()` — mode over-selection
- `updateCumulUI(folderCount, imageCount)` / `updateSortUI()` — mise à jour de l'UI des boutons
- `parseStillNameUtil(filename)` — extrait clipName + sourceTc du nom de fichier (pattern ARRI/Sony)

### Lightbox
- `openLightbox(images, idx, context)` / `closeLb()`
- `updateLb()` — met à jour tout l'UI du lightbox
- `renderCarousel()` — 7 slots (±3 autour de lbIdx) ; Shift+click → `lbMultiSel`
- `lbMoveGroup(dir)` — déplace le groupe lbMultiSel (ou l'image courante si vide) de ±1 position
- `syncLightboxToSel()` — resync lbImages/lbIdx après mutation externe

### Export
- `exportPDF()` — PDF stills, 16:9 paysage
- `exportCS(fmt)` — Contact Sheet ('jpg'|'png'|'pdf')
- `exportEDL()` — DaVinci Resolve Markers EDL, sélection active uniquement
- `exportALE()` / `exportCSV()` — métadonnées clips
- `exportShootReport()` / `exportClipsReport()` / `exportQCReport()` — rapports PDF

### EDL — logique de matching
`exported_filename` est `null` dans les métadonnées actuelles.  
Matching via `clip_name` + `source_tc` extraits du nom du fichier still :  
Pattern filename : `{scene}_{shot}_{take}_{ClipName.mxf}_{HH}_{MM}_{SS}_{FF}.jpg`  
→ lookup dans `markers_metadata` → champ `timeline_tc` utilisé pour le record TC.  
Format EDL : `source 00:00:00:00 00:00:00:01 | record tcIn tcOut`.

### Settings / Contact Sheet
- `initCsSettings()` — charge depuis localStorage au démarrage
- `saveCsSettings()` — appelé à chaque changement via `csChanged()`
- `CS_SETTING_IDS` — liste des 14 IDs de champs CS à persister

### Live Mode (crop sensor)
- `getLiveCropDims()` / `getLiveTransform()` / `cropImgEl()`
- `loadImgForExport(url)` — charge + applique le crop pour l'export

---

## Métadonnées clips (._stills_metadata.json)

```json
{
  "timeline": "20260504_D34",
  "frame_rate": 24.0,
  "markers_metadata": {
    "87042": {
      "timeline_frame": 87042,
      "timeline_tc": "01:00:26:18",
      "clip_name": "A207C001_260504K9.mxf",
      "source_tc": "09:50:24:02",
      "exported_filename": null,
      "metadata": { ... },
      "clip_properties": { ... }
    }
  }
}
```

Généré par le script DaVinci Resolve **DaVinci-Resolve-Stills-Markers**.

---

## Conventions importantes

- **Pas de build** — éditer `index.html` directement.
- `$(id)` est un alias de `document.getElementById`.
- `imgUrl(p)` construit l'URL `/api/image/{path}`.
- `pushHistory()` **avant** toute mutation de `selections` pour que undo/redo fonctionne.
- Les boutons Export PDF / Contact Sheet / EDL Marker sont dans `#selFooter` (panneau droit).
- La modale Export (`Cmd+E`) concerne uniquement les exports Clips Report (Shoot, Clips, QC, ALE, CSV).
- Le bouton `+` d'onglet appelle `addNewSel()` qui duplique la sélection courante.

---

## Utilisateur

Film/DIT professionnel, francophone. Utilise DaVinci Resolve. Nommage clips : `A207C001_260504K9.mxf` (convention ARRI/Sony). Timecodes au format `HH:MM:SS:FF`.

## Version actuelle : v1.3.1
