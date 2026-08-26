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
| Paramètres Color Palette | `localStorage` clé `stills-palette-settings` |
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
- `shuffleSel()` / `invertSel()` — randomise / inverse l'ordre de la sélection active (icônes header du panneau Selection)
- `divideByScene()` — groupe les images de la sélection active par `getImageScene()` et crée un nouvel onglet par scène (`Scene [Scene]`, dédupliqué via suffixe `(2)`, `(3)`… en cas de collision de nom ; scène manquante → `Scene Unknown`) ; sélection initiale intacte, icône header (à gauche de shuffle)
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
- `exportPalette(fmt)` — Color Palette ('jpg'|'png'|'pdf') : bande de couleurs dominantes (3 par image, `extractDominantColors()`, fallback `avgColor()`) de la sélection active, ratio fixe 2.39:1. Rendu partagé preview/export via `paletteRender(canvas, W, H)`. Onglet `setTabPalette` dans la modale Export, chemin d'export partagé avec `contactSheet`. Ne dépend pas de `clipsMetadata`
- `exportPrint(fmt)` — Print ('jpg'|'png'|'pdf') : contact sheet prêt à imprimer, taille papier réelle (mm) + DPI réel, marges T/B/L/R en mm, crop global (ratio cible ou trim pixels T/B/L/R) appliqué à toutes les images avant mise en grille. Rendu partagé preview/export via `printRender(canvas, W, preloadedImgs, pageIndex, overrideH)`, grille calculée avec `csCalcGrid()` (réutilisé, aspect uniforme après crop). Pane `setPanePrint` dans la modale Export, chemin d'export dédié `print` (onglet Paths). Pas de titre/watermark/prod-info/color-band — volontairement minimal, contrairement à Contact Sheet

### EDL — logique de matching
`exported_filename` est `null` dans les métadonnées actuelles.  
Matching via `clip_name` + `source_tc` extraits du nom du fichier still :  
Pattern filename : `{scene}_{shot}_{take}_{ClipName.mxf}_{HH}_{MM}_{SS}_{FF}.jpg`  
→ lookup dans `markers_metadata` → champ `timeline_tc` utilisé pour le record TC.  
Format EDL : `source 00:00:00:00 00:00:00:01 | record tcIn tcOut`.

### Export / Contact Sheet
- `initCsSettings()` — charge depuis localStorage au démarrage
- `saveCsSettings()` — appelé à chaque changement via `csChanged()`
- `CS_SETTING_IDS` — liste des 14 IDs de champs CS à persister

### Export / Color Palette
- Pane `setPanePalette`, listé comme "Color Palette" dans `#expListModal`, même niveau que Contact Sheet, Stills et Print
- `initPaletteSettings()` / `savePaletteSettings()` — `PALETTE_SETTING_IDS` (résolution d'export), clé localStorage `stills-palette-settings`
- `generatePalettePreview()` / `paletteQueuePreview()` — aperçu live (debounce 450ms), même pattern que `generateCSPreview()`

### Export / Print
- Pane `setPanePrint`, listé comme "Print" dans `#expListModal` (entre Color Palette et EDL Marker), taille `exp-lg`
- `printGetPageDims()` — résout le preset papier (`printPreset` : a4p/a4l/letterp/custom) + DPI (`printDpi`) en `{wmm, hmm, dpi, W, H}`
- `printGetCropRect(img)` — crop global (mode `printCropMode` : `aspect` = ratio cible centré, `pixels` = trim T/B/L/R en px source) appliqué identiquement à chaque image avant mise en grille — pas de pan par photo (hors scope, contrairement à l'outil de référence externe dont cette feature s'inspire)
- `printRender(canvas, W, preloadedImgs, pageIndex, overrideH, forcedImages, pageTitle)` — même schéma que `csRender`, y compris les 2 derniers params scene-override : `W` sert à la fois pour l'aperçu basse-résolution (fit-to-container via `printCalcPreviewDims()`) et l'export plein DPI ; marges/gap convertis mm→px via `W / dims.wmm`.
  - Colonnes ET rows fixés (ou grille 100% auto) → grille uniforme via `csCalcGrid()`, comme Contact Sheet.
  - Colonnes fixées + **Rows = Auto** (cas courant, ex. colonne unique) → chemin dédié : hauteur de ligne dérivée de l'aspect réel de la première image, lignes empilées au gap configuré puis bloc centré verticalement (`vOffset`). Si le contenu dépasse `availH`, tout est réduit uniformément (`rowGap`/hauteur de ligne) — jamais de chevauchement même avec beaucoup d'images
  - `printAlign` (left/center/right) ne joue que sur le positionnement horizontal dans la cellule
- `printCalcPreviewDims(dims)` — ajuste la taille de preview pour qu'elle tienne entièrement dans `.cs-preview-area` (mode contain), au lieu d'une largeur fixe qui débordait pour les presets portrait (A4/Letter)
- **Title** (`printTitle`/`printTitleColor`/`printTitleSize`/`printTitleBgColor`/`printTitleBgOpacity`) — pastille dessinée en haut à gauche (réutilise `hexToRgba()`/`ctxRoundRect()`), dessinée sur **chaque page** (pas seulement la première, contrairement à Contact Sheet) car le texte peut varier par page via les tokens `[page]`/`[pages]`. `printTitleSize` en **points** (unité traditionnelle, défaut 14pt, slider 6–72) plutôt qu'en % de la largeur de page (choix explicite de l'utilisateur) : converti en px via `titleSizePt * (25.4/72) * pxPerMm`, le même `pxPerMm` (= `W / dims.wmm`) que marges/gap — donc taille physique réelle constante sur le papier, cohérente entre aperçu basse-résolution et export plein DPI, peu importe le preset papier
  - Résolution du titre en 2 temps : `printResolveTitle(sceneValue)` remplace le token littéral `[Scene]` (appelé par les *callers* — `exportPrint`/`generatePrintPreview`/`navigatePrintPreview` — puisqu'eux seuls connaissent le groupe courant) ; puis `printRender` lui-même remplace `[page]`/`[pages]` une fois la pagination de CE rendu connue (page courante / nombre total de pages **dans le groupe scène courant**, pas dans tout l'export). `[Scene]` est un token à taper manuellement dans `printTitle` (pas de checkbox dédiée ni d'auto-insertion — le hint sous le champ Title liste les tokens disponibles)
- `printSortScene` ("Sort by scene", placé juste après le bloc Title, avant Columns) — **regroupe par scène, une page (ou plus) par scène**, comme Contact Sheet : `csGetSceneGroups()` (réutilisée telle quelle) donne `[{scene, images}]` ; `exportPrint`/`generatePrintPreview` itèrent les groupes et appellent `printRender(..., forcedImages, printResolveTitle(group.scene))` par groupe, avec pagination interne si un groupe dépasse une page. Sans `clipsMetadata`, retombe silencieusement sur l'export standard (non groupé)
  - Navigation preview en mode scène : `generatePrintPreview()` précharge toutes les images de tous les groupes puis fait un rendu à blanc (`scratch` canvas) de chaque groupe pour connaître son `totalPages` réel, et construit `printPreviewFlat` — une entrée par **page rendue** (pas une entrée par scène) — pour que `navigatePrintPreview()` parcoure bien toutes les pages de toutes les scènes, y compris une scène qui déborde sur plusieurs pages (au lieu de rester bloqué sur sa page 1). `printPageLabel()` affiche alors `Scene X (pY/Z) — n/total`. Contact Sheet a la même limitation non corrigée (`csPreviewGroups`, une entrée par scène) — si on corrige un jour, dupliquer ce pattern côté `generateCSPreview`/`navigateCSPreview`
- Fond de page **volontairement non configurable, toujours blanc** (`#ffffff` en dur dans `printRender`) — décision explicite de l'utilisateur, ne pas réintroduire un champ `printBg`. Pas de watermark, info prod ni bande couleur (contrairement à Contact Sheet)
- `initPrintSettings()` / `savePrintSettings()` — `PRINT_SETTING_IDS` (gère les checkboxes via `el.type === 'checkbox'`, comme `CS_SETTING_IDS`), clé localStorage `stills-print-settings`
- Chemin d'export dédié `path_print` (onglet Paths, `PATH_IDS`)
- `.cs-settings` du pane Print élargi à 340px en inline style (au lieu des 260px par défaut de la classe) pour que les labels de marges ("Margin top/bottom/left/right (mm)") ne soient pas coupés

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
- Un seul bouton `#mainExportBtn` ("Export") dans `#selFooter` (panneau droit) ouvre la modale liste des exports (`openExpList()`).
- Trois modales distinctes, à ne pas confondre :
  - `#wmModal` ("Settings", `Cmd+;`) — réglages généraux : Production, Watermark, Paths, Live Mode (`openWm()`/`openProd()`/`openPaths()`, `closeWm()`, `switchSettingsTab()`).
  - `#expListModal` — modale liste intermédiaire : PDF, Stills, Contact Sheet, Color Palette, EDL Marker, chacun cliquable (`openExpList()`/`closeExpList()`). Cliquer une ligne appelle `openExportDetail(tab)`.
  - `#mainExportModal` — modale de détail **sans onglets**, n'affiche que le pane de l'export choisi (`EXPORT_PANES`), avec un bouton retour (`expBackBtn` → `backToExpList()`) vers la liste et un titre dynamique (`EXPORT_TITLES`). Sa taille (classe `.exp-sm` / `.exp-md` / `.exp-lg` sur `#expDetailBox`, définie par `EXPORT_SIZES`) s'adapte au contenu du pane : compacte pour PDF/EDL (texte + bouton), moyenne pour Stills (formulaire), large pour Contact Sheet/Color Palette (réglages + preview live). `closeMainExport()` ferme tout (détail + liste).
  - `#exportModal` (Clips Report, `Cmd+E`) — reste inchangée : Shoot Report, Clips Report, QC Report, ALE, CSV (`openExportModal()`/`closeExportModal()`/`runExports()`). **Attention aux noms de fonctions proches mais distincts** : `openExportDetail`/`closeMainExport` (nouvelle modale Export) vs `openExportModal`/`closeExportModal` (Clips Report).
- Le bouton `+` d'onglet appelle `addNewSel()` qui duplique la sélection courante.

---

## Utilisateur

Film/DIT professionnel, francophone. Utilise DaVinci Resolve. Nommage clips : `A207C001_260504K9.mxf` (convention ARRI/Sony). Timecodes au format `HH:MM:SS:FF`.

## Version actuelle : v1.3.1
