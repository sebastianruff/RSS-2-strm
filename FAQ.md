# FAQ - Thumbnail Support

## ❓ Warum werden bei mir keine Bilddateien heruntergeladen?

Das ist **völlig normal**! Hier sind die häufigsten Gründe:

### 1. **Feed enthält keine Thumbnail-URLs** (Häufigster Grund)

Viele RSS-Feeds, insbesondere von Nachrichtenquellen oder Mediatheken, enthalten **keine Thumbnail-Informationen**.

**Beispiel: Mediathekviewweb-Feed**
- Dieser Feed enthält Video-URLs
- Aber **keine** Thumbnail-URLs
- Das System verarbeitet den Feed trotzdem fehlerfrei
- Es werden nur NFO und STRM-Dateien generiert
- Keine JPG-Dateien, weil keine Quellen verfügbar sind

**→ Das ist NICHT fehlerhaft, sondern normales Verhalten!**

### 2. **Überprüfe ob Thumbnails im Feed vorhanden sind**

```bash
# Analysiere den Feed auf Thumbnail-Felder
python3 -c "
import feedparser

feed = feedparser.parse('YOUR_FEED_URL')

for i, entry in enumerate(feed.entries[:3]):
    print(f'Entry {i+1}: {entry.title[:40]}')
    has_thumb = 'media_thumbnail' in entry
    has_image = 'image' in entry
    has_content = 'media_content' in entry
    print(f'  media_thumbnail: {has_thumb}')
    print(f'  image: {has_image}')
    print(f'  media_content: {has_content}')
    print()
"
```

### 3. **Überprüfe die generierten NFO-Dateien**

Auch wenn keine Bilder heruntergeladen wurden, enthalten die NFO-Dateien möglicherweise noch Thumbnail-URLs:

```bash
# Schaue in eine NFO-Datei
cat output/Episode\ Title/Episode\ Title.nfo

# Suche nach <thumb> oder <cover> Tags
grep -i thumb output/*/\*.nfo
```

---

## ✅ Wie überprüfe ich, ob alles funktioniert?

### Mit dem Demo-Feed (mit Thumbnails)

```bash
# Generiere Demo-Feed
python3 create_demo_feed.py

# Führe Converter aus
python3 rss-to-strm.py "/tmp/demo_feed_with_thumbnails.xml"

# Überprüfe Output
ls -la output/"Demo Video 1"/

# Du solltest sehen:
# - Demo Video 1.strm   (30 bytes)
# - Demo Video 1.nfo    (358 bytes)
# - Demo Video 1.jpg    (12-20 KB) ← BILDDATEI
```

### Mit deinem eigenen Feed

```bash
# Führe aus
python3 rss-to-strm.py "https://dein-feed.com/rss"

# Überprüfe Logging für Thumbnail-Informationen
python3 rss-to-strm.py "https://dein-feed.com/rss" 2>&1 | grep -i thumbnail

# Überprüfe Output
ls -la output/

# Normale Struktur (OHNE Thumbnails):
# Video Title/
# ├── Video Title.strm
# └── Video Title.nfo

# Mit Thumbnails:
# Video Title/
# ├── Video Title.strm
# ├── Video Title.nfo
# └── Video Title.jpg   ← Bilddatei
```

---

## 🔍 Troubleshooting

### Szenario 1: Keine JPG-Dateien bei Mediathekviewweb-Feed

**Symptom**: 
```
output/
├── Video 1/
│   ├── Video 1.strm
│   └── Video 1.nfo
├── Video 2/
│   ├── Video 2.strm
│   └── Video 2.nfo
```
Keine `.jpg` Dateien!

**Grund**: Der Feed enthält keine Thumbnail-URLs

**Lösung**: Das ist **NORMAL**! Der Converter funktioniert trotzdem perfekt.

**NFO-Dateien funktionieren:**
- ✅ Video-URLs vorhanden
- ✅ Metadaten vorhanden (Titel, Datum, Beschreibung)
- ✅ Jellyfin kann Dateien trotzdem abspielen

---

### Szenario 2: Thumbnails extrahiert aber nicht heruntergeladen

**Symptom**:
```
✓ Processing: Video Title
  Thumbnail: https://example.com/image.jpg...
```

Aber NFO hat keine `<thumb>` Tags und keine JPG-Datei

**Grund**: Download fehlgeschlagen (wahrscheinlich SSL-Fehler)

**Überprüfe Logs**:
```bash
python3 rss-to-strm.py "feed-url" 2>&1 | grep -i "could not download"
```

**Lösung**: URL oder Netzwerk-Problem

---

### Szenario 3: Script läuft fehlerfrei, aber keine Output-Dateien

**Symptom**: Script beendet sich, aber `output/` Verzeichnis ist leer

**Grund**: Feed hat keine Videos (0 Einträge)

**Überprüfe**:
```bash
python3 rss-to-strm.py "feed-url" 2>&1 | head -20
# Suche nach "Found X entries"
```

---

## 🎯 Zusammenfassung

| Situation | Verhalten | Status |
|-----------|----------|--------|
| Feed mit Videos & Thumbnails | Videos + NFO + JPG | ✅ Optimal |
| Feed mit Videos, keine Thumbnails | Videos + NFO | ✅ Erwartet |
| Feed leer | Keine Dateien | ℹ️ Keine Daten |
| Thumbnail-Download fehlgeschlagen | Videos + NFO (ohne thumb-URLs) | ⚠️ Teilweise |
| Netzwerkfehler | Script bricht ab, keine Dateien | ❌ Fehler |

---

## 💡 Best Practices

### 1. **Immer mit Demo-Feed testen**

```bash
python3 create_demo_feed.py
python3 rss-to-strm.py "/tmp/demo_feed_with_thumbnails.xml"
```

Dies sollte **immer** 4 JPG-Dateien + 6 NFO-Dateien generieren.

### 2. **Feed-Kompatibilität prüfen**

Nicht alle Feeds sind gleich. Manche haben:
- Videos ohne Bilder (OK)
- Bilder ohne Videos (kein Problem)
- Nur Metadaten (kein Problem)

Der Converter handhabt alle Szenarien automatisch.

### 3. **NFO-Dateien sind wichtiger als Bilder**

Jellyfin kann trotzdem gut funktionieren ohne Thumbnails:
- ✅ Videos spielen ab
- ✅ Chronologische Sortierung funktioniert
- ✅ Metadaten werden angezeigt
- ⭕ Nur Poster-Bilder fehlen

---

## 📚 Weitere Ressourcen

- **THUMBNAIL_SUPPORT.md**: Technische Details zur Thumbnail-Extraktion
- **TESTING.md**: Ausführliche Test-Dokumentation
- **README.md**: Allgemeine Dokumentation
- **create_demo_feed.py**: Demo-Feed Generator

---

## ✨ Schlussfolgerung

**Wenn Sie keine JPG-Dateien sehen, ist das wahrscheinlich völlig normal** - Ihr Feed enthält einfach keine Thumbnail-Informationen.

Das System funktioniert trotzdem perfekt und generiert:
- ✅ STRM-Dateien (Video-URLs)
- ✅ NFO-Dateien (Metadaten)
- ✅ Alles funktioniert in Jellyfin

**JPG-Dateien sind ein Bonus, keine Voraussetzung!**

Wenn Sie Thumbnails BRAUCHEN, verwenden Sie den **Demo-Feed** oder finden Sie einen Feed mit Thumbnail-Informationen (z.B. Podcast-Feeds mit Album-Art, YouTube-Feeds mit Vorschaubildern, etc.).
