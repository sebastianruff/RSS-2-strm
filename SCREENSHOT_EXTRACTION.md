# Screenshot-Extraktion aus Video-Streams - Machbarkeitsstudie

## 🎬 Die Frage

"Kann man aus dem Video-Stream ein Screenshot für das Thumbnail benutzen?"

---

## ✅ Ja, aber mit Einschränkungen

### Option 1: Mit FFmpeg (Empfohlen)

**Funktioniert:** ✅ JA  
**Komplexität:** Mittel  
**Abhängigkeiten:** FFmpeg installieren

```bash
# Installation
brew install ffmpeg          # macOS
apt install ffmpeg           # Linux
choco install ffmpeg         # Windows
```

**Konzept:**
```python
import subprocess

def extract_screenshot(video_url, output_file, time_offset="00:00:05"):
    """Extrahiere Screenshot aus Video nach 5 Sekunden"""
    cmd = [
        'ffmpeg',
        '-i', video_url,
        '-ss', time_offset,
        '-vframes', '1',
        '-vf', 'scale=300:400',  # Skaliere auf 300x400
        '-y',  # Überschreibe existierende Datei
        output_file
    ]
    subprocess.run(cmd, capture_output=True)
```

**Vor- und Nachteile:**
- ✅ Funktioniert mit jedem Video-Format
- ✅ Beliebiger Zeitpunkt wählbar (z.B. 5 Sekunden)
- ✅ Qualität und Größe steuerbar
- ❌ Braucht FFmpeg Installation
- ❌ Langsam (5-15 Sekunden pro Video)
- ❌ Funktioniert nur bei downloadbaren Videos
- ❌ Bei Streaming/Protected Videos oft unmöglich
- ❌ Lizenz-Fragen bei gekoppelten Videos

---

### Option 2: Mit OpenCV + Python

**Funktioniert:** ✅ JA (ähnlich wie FFmpeg)  
**Komplexität:** Mittel  
**Abhängigkeiten:** opencv-python

```bash
pip install opencv-python
```

```python
import cv2

def extract_screenshot_opencv(video_url, output_file, second=5):
    """Extrahiere Screenshot mit OpenCV"""
    cap = cv2.VideoCapture(video_url)
    cap.set(cv2.CAP_PROP_POS_MSEC, second * 1000)
    
    ret, frame = cap.read()
    if ret:
        # Skaliere Bild
        resized = cv2.resize(frame, (300, 400))
        cv2.imwrite(output_file, resized)
    
    cap.release()
```

---

### Option 3: Mit yt-dlp (für YouTube/Plattformen)

**Funktioniert:** ✅ JA (aber speziell für Streaming-Plattformen)  
**Komplexität:** Einfach  
**Abhängigkeiten:** yt-dlp

```bash
pip install yt-dlp
```

```python
import yt_dlp

def extract_thumbnail_ytdlp(video_url):
    """Extrahiere Thumbnail mit yt-dlp"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'writethumbnail': True,
        'outtmpl': 'thumbnail',
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        return info.get('thumbnail')
```

---

## ⚠️ Praktische Probleme

### 1. **Streaming-URLs**

Viele moderne Videos sind **Streaming-URLs** (HLS, DASH), nicht einfache MP4s:

```
https://example.com/videos/video.mp4
  ↓ (funktioniert mit FFmpeg/OpenCV)

https://stream.example.com/hls/playlist.m3u8
  ↓ (funktioniert auch, aber langsamer)

https://stream.example.com/dash/manifest.mpd
  ↓ (funktioniert, aber kompliziert)
```

### 2. **DRM/Urheberrecht**

- ❌ YouTube: Videos geschützt, Screenshot illegal
- ❌ Netflix: Videos verschlüsselt, Screenshot unmöglich
- ❌ Mediatheken: Je nach Lizenz unterschiedlich
- ✅ Selbst gehostete Videos: Meist OK

### 3. **Performance**

```
Pro Video:
  - Extraktion: 5-15 Sekunden
  - Bei 40 Videos: 3-10 Minuten!
```

Das würde das Script massiv verlangsamen!

### 4. **Netzwerk**

- FFmpeg muss Video streamen → Bandbreite
- Bei fehlender Netzwerkverbindung: Fehler
- Bei großen Video-Dateien: Viel Traffic

---

## 🎯 Alternative: Intelligente Fallback-Hierarchie

**Besser als Screenshots:** Kombination verwenden!

```
1. Vorhandenes Thumbnail aus RSS nutzen (schnell!)
   └─ Falls vorhanden: media:thumbnail, media:content, etc.

2. Falls kein Thumbnail: Externe Dienste
   └─ TMDB, IMDb, Poster-Datenbanken

3. Falls auch das nicht: Screenshot extrahieren
   └─ Nur wenn alles andere fehlschlägt
```

**Vorteil:** Meistens schnell, nur bei Bedarf Screenshot!

---

## 💡 Empfehlungen

### Für Ihr RSS-2-STRM Projekt

**NICHT empfohlen:** Screenshot-Extraktion als Standard
- ❌ Zu langsam (würde 40 Videos × 10 Sekunden = 6+ Minuten dauern)
- ❌ Braucht FFmpeg-Installation
- ❌ Funktioniert bei DRM-geschützten Videos nicht
- ❌ Lizenz-Probleme bei gekoppelten Inhalten

**EMPFOHLEN:** Aktueller Ansatz beibehalten
- ✅ RSS-Thumbnails wenn vorhanden (schnell)
- ✅ Externe Services als Fallback
- ✅ Keine zusätzlichen Abhängigkeiten nötig
- ✅ Zuverlässig und legal

---

## 🚀 Zukunfts-Features (Optional)

Falls Sie Screenshot-Extraktion WOLLEN:

### Konfigurierbar machen:

```python
# Neue Einstellungen
EXTRACT_SCREENSHOTS = False  # Standard: deaktiviert
SCREENSHOT_TIME = 5          # Nach 5 Sekunden
SCREENSHOT_QUALITY = "medium"  # Qualität
```

### Nur wenn RSS-Thumbnail fehlt:

```python
# Nur als LETZTES Resort
if not metadata['thumbnail']:
    if EXTRACT_SCREENSHOTS:
        try:
            metadata['thumbnail'] = extract_screenshot(video_url)
        except:
            logging.warning("Screenshot extraction failed")
```

### Mit Parallelisierung (für schneller):

```python
# Mehrere Videos parallel
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(extract_screenshot, url)
        for url in video_urls
    ]
```

---

## 📊 Vergleich: RSS-Thumbnail vs. Screenshot

| Aspekt | RSS-Thumbnail | Screenshot |
|--------|---------------|-----------| 
| Geschwindigkeit | ⚡ Sofort | 🐢 5-15 sec/Video |
| Abhängigkeiten | Keine | FFmpeg |
| Funktioniert mit DRM | ✅ Nein | ❌ Nein |
| Qualität | Variable | Konsistent |
| Lizenz-Fragen | Keine | Potenzielle Probleme |
| Verfügbarkeit | Feed-abhängig | Immer möglich |

---

## 🎓 Konkrete Implementierung

Falls Sie TROTZDEM Screenshots wollen, hier ein Beispiel:

### 1. Installation

```bash
pip install ffmpeg-python
```

### 2. Code hinzufügen

```python
import ffmpeg
import os

def extract_thumbnail_from_video(video_url, output_path, time_seconds=5):
    """Extrahiere Thumbnail aus Video-Stream"""
    try:
        # FFmpeg Stream extrahieren
        stream = ffmpeg.input(video_url, ss=time_seconds)
        stream = ffmpeg.filter(stream, 'scale', 300, 400)
        stream = ffmpeg.output(stream, output_path, vframes=1)
        
        # Ausführen (mit Timeout)
        ffmpeg.run(stream, capture_stdout=True, capture_stderr=True, timeout=30)
        
        logging.info(f"✓ Screenshot extrahiert: {output_path}")
        return True
    except Exception as e:
        logging.warning(f"Screenshot extraction failed: {e}")
        return False
```

### 3. In write_strm_files() integrieren

```python
# Nach existierendem Thumbnail-Download:
if not thumbnail_downloaded and EXTRACT_SCREENSHOTS:
    if extract_thumbnail_from_video(video_url, item_thumb):
        logging.info("Screenshot used as thumbnail")
```

---

## ✨ Fazit

**Kurze Antwort:** Ja, es ist möglich, aber:
- ⚠️ Sehr langsam
- ⚠️ Braucht zusätzliche Software (FFmpeg)
- ⚠️ Funktioniert nicht bei DRM-geschützten Videos
- ⚠️ Potenzielle Lizenz-Probleme

**Besser:** Aktueller Ansatz mit RSS-Thumbnails und Fallbacks verwenden!

Falls gewünscht, kann ich die Screenshot-Funktionalität später als **optionales Feature** hinzufügen!

---

## 🤔 Für Ihr Projekt

Möchten Sie, dass ich:

1. ✅ **Nichts ändern** - Aktueller Ansatz ist OK
2. 📋 **Optional-Features dokumentieren** - Wie man es machen könnte
3. 🔧 **Screenshot-Funktion hinzufügen** - Als disabled-by-default Option
4. 🚀 **Andere Fallback-Optionen** - z.B. TMDB/IMDb Integration

**Was bevorzugen Sie?**
