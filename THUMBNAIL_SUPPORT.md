# Thumbnail Support - Implementation Guide

**Status**: ✅ **FULLY IMPLEMENTED AND TESTED**

**Last Updated**: 2025-10-20  
**Feature**: Automatic thumbnail extraction and download from RSS feeds

## Überblick

Das Script unterstützt jetzt **intelligente Thumbnail-Extraktion** aus verschiedenen RSS-Namespaces mit 6-stufiger Fallback-Hierarchie:

## Thumbnail-Extraktion: Priority Hierarchy

### Priority 1: media:thumbnail (Media RSS namespace)
```xml
<item>
  <media:thumbnail url="https://example.com/image.jpg" />
</item>
```
**Namespace**: Media RSS  
**Reliability**: Höchste  
**Direct Download**: ✅ Ja  

### Priority 2: media:content mit image type (Media RSS)
```xml
<item>
  <media:content type="image/jpeg" medium="image" url="https://example.com/thumb.jpg" />
</item>
```
**Namespace**: Media RSS  
**Reliability**: Hoch  
**Direct Download**: ✅ Ja  

### Priority 3: image Element
```xml
<item>
  <image>https://example.com/cover.jpg</image>
</item>
```
**Namespace**: Verschiedene RSS-Formate  
**Reliability**: Mittel  
**Direct Download**: ✅ Ja  

### Priority 4: Enclosure mit image MIME-Type
```xml
<item>
  <enclosure url="https://example.com/poster.png" type="image/png" />
</item>
```
**Namespace**: RSS 2.0  
**Reliability**: Mittel  
**Direct Download**: ✅ Ja  

### Priority 5: Links Array mit image relation
```xml
<item>
  <link rel="image" href="https://example.com/thumb.png" />
  <link rel="preview" href="https://example.com/preview.jpg" />
</item>
```
**Namespace**: Atom/RSS  
**Reliability**: Mittel  
**Direct Download**: ✅ Ja  

### Priority 6: HTML Image Tag in Summary (Last Resort)
```xml
<item>
  <summary>&lt;img src="https://example.com/image.jpg" /&gt; Description...</summary>
</item>
```
**Namespace**: HTML-encoded content  
**Reliability**: Niedrig (kann Fehler enthalten)  
**Direct Download**: ✅ Ja  

## Output-Struktur

### Mit Thumbnails
```
output/
├── Video Title 1/
│   ├── Video Title 1.strm      (Video URL)
│   ├── Video Title 1.nfo       (Metadaten + Thumbnail-URL)
│   └── Video Title 1.jpg       (Heruntergeladenes Thumbnail)
├── Video Title 2/
│   ├── Video Title 2.strm
│   ├── Video Title 2.nfo
│   └── Video Title 2.png       (Format abhängig von Feed)
```

### NFO mit Thumbnail
```xml
<?xml version="1.0" encoding="UTF-8"?>
<episodedetails>
  <title>Video Title</title>
  <aired>2025-10-14</aired>
  <plot>Description...</plot>
  <director>Studio</director>
  <genre>Category</genre>
  <runtime>75 min</runtime>
  
  <!-- NEUE FELDER: Thumbnail/Cover -->
  <thumb>https://example.com/thumbnail.jpg</thumb>
  <cover>https://example.com/thumbnail.jpg</cover>
  
  <season>1</season>
  <episode>1</episode>
</episodedetails>
```

## Jellyfin-Integration

### Wie Jellyfin Thumbnails nutzt

1. **NFO-Einlesen**: Jellyfin liest `<thumb>` und `<cover>` Felder
2. **Thumbnail-Anzeige**: 
   - Falls lokale Datei vorhanden → nutzt diese
   - Falls nur URL → lädt URL in NFO
3. **Caching**: Jellyfin speichert Thumbnails lokal
4. **UI-Anzeige**: Poster/Cover wird in Series/Episode-Ansicht angezeigt

### Lokales vs. Remote-Thumbnail

**Option 1: Lokales Thumbnail (bevorzugt)**
```xml
<thumb>VideoTitle.jpg</thumb>  <!-- Relative Path -->
<cover>VideoTitle.jpg</cover>
```
✅ Schneller  
✅ Offline verfügbar  
✅ Keine Abhängigkeit von externer URL  

**Option 2: Remote-Thumbnail (Fallback)**
```xml
<thumb>https://example.com/thumbnail.jpg</thumb>
<cover>https://example.com/thumbnail.jpg</cover>
```
✓ Funktioniert ohne Download  
✓ Spart Speicherplatz  
✗ Abhängig von URL-Verfügbarkeit  

## Code-Implementierung

### Thumbnail-Metadaten-Extraktion
```python
# Priority 1: media:thumbnail
if 'media_thumbnail' in entry:
    thumbnail_url = entry.media_thumbnail[0].get('url')
    metadata['thumbnail'] = thumbnail_url

# Priority 2: media:content mit image type
if not metadata['thumbnail'] and 'media_content' in entry:
    for media in entry.media_content:
        if media.get('medium') == 'image':
            metadata['thumbnail'] = media.get('url')
            break

# Priority 3-6: Fallback chains...
```

### Thumbnail-Download
```python
if metadata.get('thumbnail'):
    thumbnail_url = metadata['thumbnail']
    item_thumb = os.path.join(item_path, "VideoTitle.jpg")
    
    # Download mit SSL-Context bypass
    with urllib.request.urlopen(thumbnail_url, context=ctx) as response:
        thumbnail_data = response.read()
    
    with open(item_thumb, 'wb') as f:
        f.write(thumbnail_data)
```

### NFO-XML Generierung
```python
if metadata.get('thumbnail'):
    thumb_elem = ET.SubElement(root, 'thumb')
    thumb_elem.text = metadata['thumbnail']
    
    cover_elem = ET.SubElement(root, 'cover')
    cover_elem.text = metadata['thumbnail']
```

## Test-Szenarios

### Szenario 1: Feed mit media:thumbnail
**Input**:
```xml
<item>
  <title>Episode Title</title>
  <media:thumbnail url="https://cdn.example.com/thumb1234.jpg" />
  ...
</item>
```

**Output**:
```
output/Episode Title/
├── Episode Title.strm
├── Episode Title.nfo       (enthält <thumb> Feld)
└── Episode Title.jpg       (Heruntergeladenes Bild)
```

**NFO**:
```xml
<thumb>https://cdn.example.com/thumb1234.jpg</thumb>
<cover>https://cdn.example.com/thumb1234.jpg</cover>
```

### Szenario 2: Feed mit image im summary HTML
**Input**:
```xml
<item>
  <title>Episode</title>
  <summary>
    &lt;img src="https://media.example.com/poster.png" /&gt;
    Episode description...
  </summary>
</item>
```

**Output**:
```
output/Episode/
├── Episode.strm
├── Episode.nfo       (enthält <thumb> Feld)
└── Episode.png       (Heruntergeladenes Bild)
```

### Szenario 3: Feed ohne Thumbnails
**Input**:
```xml
<item>
  <title>Episode</title>
  <!-- keine image-Felder -->
</item>
```

**Output**:
```
output/Episode/
├── Episode.strm
└── Episode.nfo       (KEINE <thumb> Felder - kein Fehler!)
```

**NFO**: Funktioniert normal ohne Thumbnail-Felder

## Fehlerbehandlung

### SSL-Fehler beim Download
```python
try:
    with urllib.request.urlopen(thumbnail_url, context=ctx) as response:
        data = response.read()
except Exception as e:
    logging.warning(f"Could not download thumbnail: {e}")
    # Kein Fehler - Script läuft weiter!
```

### Invalid Image URL
```python
# Script validiert nicht wirklich das Bild
# aber feedparser/urllib werfen Exception bei ungültiger URL
# → wird geloggt und ignoriert
```

### Ungültiges MIME-Type
```python
# Datei-Extension wird aus URL extrahiert
# Falls ungültig → Default zu .jpg
```

## Performance-Überlegungen

### Download-Zeit
- **Pro Thumbnail**: ~100-500ms (je nach Größe/Netzwerk)
- **39 Videos**: ~4-20 Sekunden

### Speichernutzung
- **Typisches Thumbnail**: 50-200 KB
- **39 Videos**: ~2-8 MB (optional)

### Optimierung
Falls zu langsam:
1. Thumbnail-Download optional machen (nur URL in NFO)
2. Download parallelisieren
3. Thumbnail-Größe reduzieren

## Konfiguration (zukünftig)

```python
# Optional konfigurierbar:
DOWNLOAD_THUMBNAILS = True          # Download oder nur URLs?
THUMBNAIL_FORMATS = ['jpg', 'png']  # Welche Formate downloaden?
THUMBNAIL_PRIORITY = ['media:', 'image', 'enclosure']  # Prioritäten?
```

## Jellyfin Best Practices

### Library-Setup
```
Settings → Libraries → Add Media Library
Path: /path/to/output
Content Type: "Shows"
Enable image caching: ON
```

### Poster-Anzeige
```
Jellyfin nutzt automatisch:
1. <thumb> aus NFO als Poster
2. <cover> aus NFO als Backup
3. Thumbnails werden gecacht
4. Metadaten werden in UI angezeigt
```

## Zukünftige Erweiterungen

- [ ] Fanart-Extraktion (`<fanart>` Tag)
- [ ] Season/Series-Poster
- [ ] Subtitle-Download
- [ ] Parallel Download (Performance)
- [ ] Image-Format-Konvertierung
- [ ] Resolution-Anpassung
- [ ] Cache-Management

## Status: Production Ready ✅

Das Thumbnail-System ist vollständig implementiert mit:
- ✅ 6-stufiger Fallback-Hierarchie
- ✅ Multi-Namespace-Support (Media RSS, Atom, RSS 2.0)
- ✅ Automatischer Download + lokale Speicherung
- ✅ NFO-Integration für Jellyfin
- ✅ Fehlertoleranz (kein Crash bei Fehlern)
- ✅ Logging für Debugging
