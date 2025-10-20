# Quick Start - Thumbnail Support Testing

## 🚀 In 2 Minuten Thumbnails testen

### Schritt 1: Demo-Feed generieren

```bash
python3 create_demo_feed.py
```

Output:
```
✅ Demo RSS Feed erstellt: /tmp/demo_feed_with_thumbnails.xml
```

### Schritt 2: Converter ausführen

```bash
rm -rf output
python3 rss-to-strm.py "/tmp/demo_feed_with_thumbnails.xml"
```

### Schritt 3: Ergebnis überprüfen

```bash
# Überprüfe Output-Verzeichnis
ls -lah output/

# Du solltest 6 Verzeichnisse sehen:
# Demo Video 1/  Demo Video 2/  ... Demo Video 6/

# Überprüfe ein Video-Verzeichnis
ls -lah output/"Demo Video 1"/
```

**Erwartetes Ergebnis:**
```
Demo Video 1.strm       30 bytes   (Video-URL)
Demo Video 1.nfo        358 bytes  (Metadaten)
Demo Video 1.jpg        14 KB      ✅ THUMBNAIL!
```

---

## 📊 Erwartete Ergebnisse

| Video | Thumbnail-Quelle | Bild heruntergeladen |
|-------|-----------------|------------------|
| Demo Video 1 | media:thumbnail | ✅ JA (.jpg) |
| Demo Video 2 | media:content | ✅ JA (.jpg) |
| Demo Video 3 | enclosure | ✅ JA (.jpg) |
| Demo Video 4 | HTML img-Tag (keine URL) | ❌ NEIN |
| Demo Video 5 | media:thumbnail | ✅ JA (.jpg) |
| Demo Video 6 | Keine Quelle | ❌ NEIN |

**Total:**
- ✅ 6 STRM-Dateien (100%)
- ✅ 6 NFO-Dateien (100%)
- ✅ 4 JPG-Dateien (67% - so viele haben Thumbnails)

---

## 🔍 Inspiziere die generierten Dateien

### STRM-Datei (Video-URL)

```bash
cat output/"Demo Video 1"/"Demo Video 1.strm"

# Output: https://example.com/video1.mp4
```

### NFO-Datei (Metadaten)

```bash
cat output/"Demo Video 1"/"Demo Video 1.nfo"

# Output:
# <?xml version="1.0" encoding="UTF-8"?>
# <episodedetails>
#   <title>Demo Video 1</title>
#   <plot>Video mit media:thumbnail</plot>
#   <director>Test Creator</director>
#   <genre>Demo</genre>
#   <thumb>https://picsum.photos/300/400?random=1</thumb>
#   <cover>https://picsum.photos/300/400?random=1</cover>
#   <season>1</season>
#   <episode>1</episode>
# </episodedetails>
```

### JPG-Bild (Thumbnail)

```bash
# Überprüfe Dateityp
file output/"Demo Video 1"/"Demo Video 1.jpg"

# Output: JPEG image data, 300x400, progressive

# Öffne das Bild
open output/"Demo Video 1"/"Demo Video 1.jpg"  # macOS
# oder
xdg-open output/"Demo Video 1"/"Demo Video 1.jpg"  # Linux
```

---

## ⚙️ Detailliertere Tests

### Test 1: Alle Verzeichnisse auflisten

```bash
ls -1d output/*/
```

### Test 2: Zähle Dateien nach Typ

```bash
find output -type f -name "*.strm" | wc -l  # sollte 6 sein
find output -type f -name "*.nfo" | wc -l   # sollte 6 sein
find output -type f -name "*.jpg" | wc -l   # sollte 4 sein
```

### Test 3: Überprüfe Bild-Integrität

```bash
# Alle JPGs als valide Bilder?
for jpg in output/*/*.jpg; do
    file "$jpg" | grep -q "JPEG" && echo "✅ $jpg" || echo "❌ $jpg"
done
```

### Test 4: Überprüfe Thumbnail-URLs in NFO

```bash
# Suche alle <thumb> Tags
grep -h "<thumb>" output/*/*.nfo

# Output sollte URLs enthalten:
# <thumb>https://picsum.photos/300/400?random=1</thumb>
# <thumb>https://picsum.photos/300/400?random=2</thumb>
# etc.
```

### Test 5: Überprüfe Bild-Dateigröße

```bash
find output -name "*.jpg" -exec du -h {} \;

# Output sollte sein:
# 12K   Demo Video 1.jpg
# 18K   Demo Video 2.jpg
# 23K   Demo Video 3.jpg
# 23K   Demo Video 5.jpg
```

---

## 🐛 Wenn etwas nicht stimmt

### Kein JPG vorhanden?

```bash
# 1. Überprüfe ob Thumbnail-Extraktion funktioniert
python3 rss-to-strm.py "/tmp/demo_feed_with_thumbnails.xml" 2>&1 | grep -i "downloading"

# 2. Überprüfe NFO-Datei auf <thumb> Tags
grep "thumb" output/"Demo Video 1"/"Demo Video 1.nfo"

# 3. Überprüfe Logging für Fehler
python3 rss-to-strm.py "/tmp/demo_feed_with_thumbnails.xml" 2>&1 | grep -i "error"
```

### Script läuft aber generating keine Dateien?

```bash
# Überprüfe ob Feed korrekt verarbeitet wird
python3 rss-to-strm.py "/tmp/demo_feed_with_thumbnails.xml" 2>&1 | head -20

# Sollte "Found 6 entries" anzeigen
```

### Thumbnails scheinen nicht zu werden?

```bash
# Überprüfe ob Python-Syntax OK ist
python3 -m py_compile rss-to-strm.py && echo "✅ Syntax OK"

# Überprüfe feedparser Installation
python3 -c "import feedparser; print(feedparser.__version__)"
```

---

## 📚 Nächste Schritte

Nach erfolgreichem Test mit Demo-Feed:

### 1. Mit eigenem Feed testen

```bash
python3 rss-to-strm.py "https://your-feed.com/rss.xml"
```

### 2. Mit Jellyfin integrieren

```bash
# Kopiere output/ Verzeichnis zu Jellyfin
cp -r output/* /path/to/jellyfin/media/
```

### 3. Automatisiert ausführen

```bash
# Via Cron (täglich um 6 Uhr)
0 6 * * * cd /path/to/rss-to-strm && python3 rss-to-strm.py

# Via Systemd Timer
# (siehe Dokumentation für Details)
```

---

## 🆘 Hilfe erhalten

- **Allgemeine Fragen**: Siehe [FAQ.md](FAQ.md)
- **Technische Details**: Siehe [THUMBNAIL_SUPPORT.md](THUMBNAIL_SUPPORT.md)
- **Test-Dokumentation**: Siehe [TESTING.md](TESTING.md)
- **Namespace-Info**: Siehe [NAMESPACE_AWARENESS.md](NAMESPACE_AWARENESS.md)

---

## ✨ Success Criteria

Sie können das System als "erfolgreich funktionierend" betrachten, wenn:

- ✅ Demo-Feed verarbeitet wird (6 Videos)
- ✅ 6 STRM-Dateien generiert werden
- ✅ 6 NFO-Dateien generiert werden
- ✅ 4 JPG-Dateien heruntergeladen werden
- ✅ Keine Fehler im Logging
- ✅ Alle Dateien sichtbar sind

**Gratulation! Das System funktioniert perfekt! 🎉**
