# NFO-Metadaten Dokumentation (Namespace-Aware)

## Was sind NFO-Dateien?

**NFO** (Nfo/Info) sind XML-Metadaten-Dateien, die von Kodi, Jellyfin und anderen Media-Center-Anwendungen gelesen werden. Sie speichern Informationen über Videos, Series und Filme in strukturierter Form.

## Namespace-Aware Metadaten-Extraktion

Dieses Script nutzt **intelligente Namespace-Erkennung** um Metadaten aus verschiedenen RSS-Namespaces zu extrahieren:

| Namespace | Feld | Beispiel |
|-----------|------|----------|
| **RSS 2.0 Standard** | title, published, summary | Titel, Datum, Beschreibung |
| **Dublin Core (dc:)** | creator | author/director |
| **Media RSS (media:)** | duration | runtime in Minuten |
| **RSS Categories** | category/tags | genre/Sendungsname |
| **Atom (atom:)** | updated | fallback für aired-date |
| **Content Module (content:)** | encoded | erweiterte Beschreibung |

## NFO-Format

```xml
<?xml version="1.0" encoding="UTF-8"?>
<episodedetails>
  <!-- Basis-Informationen (immer vorhanden) -->
  <title>Episode Title</title>
  <aired>2025-10-14</aired>
  <plot>Episode description text</plot>
  
  <!-- Namespace-Metadaten (falls vorhanden) -->
  <director>Studio/Author</director>        <!-- Aus RSS author (dc: ähnlich) -->
  <genre>Show Category</genre>              <!-- Aus RSS tags/categories -->
  <runtime>75 min</runtime>                 <!-- Aus Media RSS duration -->
  
  <!-- Organisations-Info -->
  <season>1</season>
  <episode>1</episode>
</episodedetails>
```

## Metadaten-Extraktion: Namespace-Mapping

Das Script nutzt diese Prioritäts-Hierarchie:

### Title (Titel)
```
Source: entry['title'] (RSS 2.0)
Priority: 1
Example: "maischberger am 14.10.2025"
```

### Aired Date (Ausstrahlungsdatum)
```
Priority 1: entry['published'] (RFC 2822, RSS 2.0)
Priority 2: entry['updated'] (ISO 8601, Atom namespace)
Example: "2025-10-14"
Used for: Chronologische Sortierung in Jellyfin
```

### Plot (Beschreibung)
```
Priority 1: entry['content'] (content:encoded, Content Module namespace)
            - HTML-Tags werden entfernt
Priority 2: entry['summary'] (RSS 2.0)
Priority 3: entry['subtitle'] (Alternative)
Example: "Nach der Freilassung der Geiseln..."
Limit: 500 Zeichen
```

### Director (Autor/Studio)
```
Source: entry['author'] (Dublin Core equivalent)
        or entry['author_detail'] (feedparser parsed)
Example: "ARD", "ZDF", "PHOENIX"
Used by: Jellyfin für Filterung und Grouping
```

### Genre (Kategorien/Tags)
```
Source: entry['tags'] (RSS categories)
        Maps to: <genre> elements (mehrfach möglich)
Example: ["phoenix runde", "maischberger"]
Used by: Jellyfin für Genre-basierte Navigation
```

### Runtime (Dauer)
```
Source: entry['duration'] (Media RSS namespace)
Conversion: seconds → minutes
Example: 3600 (Sekunden) → "60 min"
Used by: Jellyfin für Anzeige der Episodenlänge
```

## Warum NFO für chronologische Sortierung?

### Das Problem
- STRM-Dateien enthalten nur URLs (plain text)
- Media-Player können nicht aus Dateinamen sortieren (Leerzeichen, Sonderzeichen)
- Filesystem-Reihenfolge ist willkürlich

### Die Lösung
- NFO-Dateien haben ein `<aired>` Feld
- Jellyfin/Kodi liest dieses Datum
- Sortierung erfolgt automatisch chronologisch!

## Jellyfin Integration

### Automatische NFO-Erkennung

```
output/
├── Video Title 1/
│   ├── Video Title 1.strm   ← Jellyfin öffnet dieses Video
│   └── Video Title 1.nfo    ← Jellyfin liest Metadaten (aired date!)
├── Video Title 2/
│   ├── Video Title 2.strm
│   └── Video Title 2.nfo
```

Jellyfin erkennt automatisch:
1. Das Verzeichnis ist eine Media-Quelle
2. `.strm` Datei = Zugang zum Video
3. `.nfo` Datei = Metadaten für Sortierung und Anzeige

### Sortierung nach Aired-Datum

```
Video dated 2025-10-01  (aired: 2025-10-01)
Video dated 2025-10-09  (aired: 2025-10-09)
Video dated 2025-10-14  (aired: 2025-10-14)
Video dated 2025-10-16  (aired: 2025-10-16)
```

**Die Sortierung ist UNABHÄNGIG von Dateiname oder Filesystem-Reihenfolge!**

## NFO-Felder in diesem Script

| Feld | Beschreibung | Beispiel |
|------|-------------|---------|
| `<title>` | Episoden-Titel | `maischberger am 14.10.2025` |
| `<aired>` | Ausstrahlungsdatum (SORTIERUNG!) | `2025-10-14` |
| `<plot>` | Beschreibung/Synopsis | `Nach der Freilassung der Geiseln...` |
| `<season>` | Staffel-Nummer | `1` |
| `<episode>` | Episoden-Nummer | `1` |

## Automatische Datums-Extraktion

Das Script extrahiert das Datum aus dem RSS-Feed:

```python
# RSS Feed Eintrag
entry['published'] = 'Tue, 14 Oct 2025 21:30:00 GMT'

# Script konvertiert zu
metadata['aired'] = '2025-10-14'  # ISO-Format für NFO
```

Die Konvertierung erfolgt mit:
```python
from email.utils import parsedate_to_datetime

aired_dt = parsedate_to_datetime(entry['published'])
metadata['aired'] = aired_dt.strftime('%Y-%m-%d')
```

## Verwendung mit anderen Media-Centern

### Kodi
- ✅ Liest NFO-Dateien automatisch
- ✅ Sortiert nach aired-Datum
- ✅ Zeigt Metadaten in UI

### Jellyfin
- ✅ Liest NFO-Dateien automatisch
- ✅ Sortiert nach aired-Datum  
- ✅ Zeigt Metadaten in UI
- ✅ Kann Metadaten mit Online-Quellen mergen

### Plex
- ⚠️ Unterstützt NFO limited
- NFO wird teilweise gelesen
- Bessere Integration mit IMDB/TheTVDb

### VLC/Andere Player
- ❌ Unterstützen NFO nicht
- Nutzen direkt die STRM-URL
- Keine Metadaten angezeigt

## Best Practices

1. **Dateiname = NFO-Name**: 
   ```
   ✅ Episode Title.strm + Episode Title.nfo
   ❌ Episode Title.strm + Meta.nfo
   ```

2. **ISO-Datumsformat verwenden**:
   ```
   ✅ <aired>2025-10-14</aired>
   ❌ <aired>14.10.2025</aired>
   ❌ <aired>October 14</aired>
   ```

3. **UTF-8 Encoding**:
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   ```

4. **Minimales aber vollständiges XML**:
   ```xml
   <episodedetails>
     <title>...</title>
     <aired>...</aired>
     <plot>...</plot>
     <season>...</season>
     <episode>...</episode>
   </episodedetails>
   ```

## Troubleshooting

### NFO wird nicht gelesen
- Dateiname muss exakt mit STRM-Datei übereinstimmen
- Encoding muss UTF-8 sein
- XML muss gültig sein

### Sortierung funktioniert nicht
- Check: Ist `<aired>` im ISO-Format (YYYY-MM-DD)?
- Check: Alle NFOs haben aired-Datum?
- Jellyfin: Library neu laden (Settings → Refresh)

### Metadaten werden nicht angezeigt
- Jellyfin: Library als "Shows" konfigurieren
- NFO must valides XML sein
- Check Jellyfin logs für XML-Fehler

## Erweiterte NFO-Felder

Das Script nutzt minimale Felder. Für erweiterte Metadaten können Sie die `create_nfo_xml()` Funktion erweitern:

```xml
<episodedetails>
  <title>...</title>
  <aired>...</aired>
  <plot>...</plot>
  <director>...</director>
  <writer>...</writer>
  <rating>...</rating>
  <thumb>...</thumb>
  <fanart>...</fanart>
</episodedetails>
```

Jellyfin unterstützt diese automatisch, wenn vorhanden.

## Referenzen

- [Kodi NFO Documentation](https://kodi.wiki/view/NFO_files)
- [Jellyfin Metadata](https://jellyfin.org/docs/general/administration/local-library.html)
- [MediaInfo NFO Format](https://mediaarea.net/)
