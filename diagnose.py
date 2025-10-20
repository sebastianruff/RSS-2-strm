#!/usr/bin/env python3
"""
Diagnostic Tool - Überprüfe ob Thumbnail-Support funktioniert
"""

import os
import subprocess
import sys

def run_command(cmd, description):
    """Führe Befehl aus und zeige Ergebnis"""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print('='*60)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout if result.stdout else result.stderr)
    return result.returncode == 0

def check_environment():
    """Überprüfe Umgebung"""
    print("\n" + "="*60)
    print("📋 SYSTEM-ÜBERPRÜFUNG")
    print("="*60)
    
    # Python Version
    version = subprocess.run("python3 --version", shell=True, capture_output=True, text=True)
    print(f"✅ Python: {version.stdout.strip()}")
    
    # Feedparser
    try:
        import feedparser
        print(f"✅ feedparser: {feedparser.__version__}")
    except:
        print("❌ feedparser: NICHT INSTALLIERT")
        return False
    
    # Dateien
    if os.path.exists("rss-to-strm.py"):
        print("✅ rss-to-strm.py: vorhanden")
    else:
        print("❌ rss-to-strm.py: NICHT GEFUNDEN")
        return False
    
    if os.path.exists("create_demo_feed.py"):
        print("✅ create_demo_feed.py: vorhanden")
    else:
        print("⚠️  create_demo_feed.py: nicht gefunden (Demo nicht möglich)")
    
    return True

def test_demo_feed():
    """Teste mit Demo-Feed"""
    print("\n" + "="*60)
    print("🎬 DEMO-FEED TEST")
    print("="*60)
    
    # Generiere Demo-Feed
    if not os.path.exists("create_demo_feed.py"):
        print("⚠️  create_demo_feed.py nicht gefunden - überspringe Demo")
        return None
    
    print("\n1️⃣  Generiere Demo-Feed...")
    if run_command("python3 create_demo_feed.py", "Demo-Feed erstellen"):
        print("✅ Demo-Feed generiert")
    else:
        print("❌ Demo-Feed-Generierung fehlgeschlagen")
        return False
    
    # Überprüfe ob Feed existiert
    if not os.path.exists("/tmp/demo_feed_with_thumbnails.xml"):
        print("❌ Demo-Feed nicht gefunden")
        return False
    
    print("✅ Demo-Feed existiert")
    
    # Führe Converter aus
    print("\n2️⃣  Führe Converter mit Demo-Feed aus...")
    
    # Cleanup
    subprocess.run("rm -rf output", shell=True)
    
    # Run converter
    result = subprocess.run(
        'python3 rss-to-strm.py "/tmp/demo_feed_with_thumbnails.xml" 2>&1',
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("❌ Converter fehlgeschlagen")
        print(result.stderr)
        return False
    
    print("✅ Converter erfolgreich")
    
    # Überprüfe Output
    print("\n3️⃣  Überprüfe Output...")
    
    # Zähle Dateien
    strm_output = subprocess.run(
        "find output -name '*.strm' -type f",
        shell=True, capture_output=True, text=True
    ).stdout.strip()
    strm_count = len(strm_output.split('\n')) if strm_output else 0
    
    nfo_output = subprocess.run(
        "find output -name '*.nfo' -type f",
        shell=True, capture_output=True, text=True
    ).stdout.strip()
    nfo_count = len(nfo_output.split('\n')) if nfo_output else 0
    
    jpg_output = subprocess.run(
        "find output -name '*.jpg' -type f",
        shell=True, capture_output=True, text=True
    ).stdout.strip()
    jpg_count = len(jpg_output.split('\n')) if jpg_output else 0
    
    print(f"✅ STRM-Dateien: {strm_count} (erwartet: 6)")
    print(f"✅ NFO-Dateien: {nfo_count} (erwartet: 6)")
    print(f"{'✅' if jpg_count >= 4 else '⚠️ '} JPG-Dateien: {jpg_count} (erwartet: 4)")
    
    # Detailueberspruefung
    if strm_count == 6 and nfo_count == 6 and jpg_count >= 4:
        print("\n✅ DEMO TEST ERFOLGREICH!")
        print("   Das System funktioniert perfekt.")
        return True
    else:
        print("\n⚠️  DEMO TEST TEILWEISE")
        return False

def diagnose_output():
    """Diagnostiziere Output-Struktur"""
    print("\n" + "="*60)
    print("📁 OUTPUT-STRUKTUR")
    print("="*60)
    
    if not os.path.exists("output"):
        print("❌ output/ Verzeichnis nicht gefunden")
        print("   → Führe zuerst den Converter aus")
        return False
    
    # Zähle Verzeichnisse
    dirs = subprocess.run(
        "ls -1d output/*/ 2>/dev/null | wc -l",
        shell=True, capture_output=True, text=True
    ).stdout.strip()
    
    print(f"📁 Verzeichnisse: {dirs}")
    
    # Zähle Dateitypen
    for ext in ["strm", "nfo", "jpg", "png", "webp", "gif"]:
        count = subprocess.run(
            f"find output -name '*.{ext}' -type f 2>/dev/null | wc -l",
            shell=True, capture_output=True, text=True
        ).stdout.strip()
        if int(count) > 0:
            print(f"  ✅ .{ext}: {count}")
    
    # Überprüfe erste NFO auf Thumbnail-Tags
    nfo_files = subprocess.run(
        "find output -name '*.nfo' -type f | head -1",
        shell=True, capture_output=True, text=True
    ).stdout.strip()
    
    if nfo_files:
        has_thumb = subprocess.run(
            f"grep -q '<thumb>' '{nfo_files}' && echo 'yes' || echo 'no'",
            shell=True, capture_output=True, text=True
        ).stdout.strip()
        
        if has_thumb == "yes":
            print(f"\n✅ NFO enthält Thumbnail-Tags:")
            subprocess.run(f"grep '<thumb\\|<cover>' '{nfo_files}'", shell=True)
        else:
            print(f"\n⚠️  NFO enthält KEINE Thumbnail-Tags")
            print("   → Feed enthält vermutlich keine Thumbnail-URLs")
    
    return True

def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║          RSS-2-STRM Thumbnail Support Diagnostics          ║
║                                                            ║
║  Dieses Tool überprüft ob das Thumbnail-System            ║
║  funktioniert und hilft bei Problemen.                    ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # 1. Environment
    if not check_environment():
        print("\n❌ Umgebung nicht korrekt eingerichtet")
        return 1
    
    # 2. Demo Test
    demo_result = test_demo_feed()
    
    # 3. Output Diagnose
    diagnose_output()
    
    # 4. Zusammenfassung
    print("\n" + "="*60)
    print("📊 ZUSAMMENFASSUNG")
    print("="*60)
    
    if demo_result is True:
        print("""
✅ ALLES OK!

Das Thumbnail-Support-System funktioniert perfekt:
  ✅ Demo-Feed wurde verarbeitet
  ✅ Thumbnails wurden extrahiert
  ✅ Bilder wurden heruntergeladen
  ✅ Metadaten wurden generiert

Nächste Schritte:
  1. Verwende deinen eigenen RSS-Feed
  2. Überprüfe ob Output-Dateien generiert werden
  3. Integriere mit Jellyfin
  
Wenn keine JPG-Dateien bei deinem Feed vorhanden sind:
  → Das ist NORMAL! Dein Feed enthält keine Thumbnail-URLs
  → Siehe FAQ.md für mehr Informationen
        """)
        return 0
    elif demo_result is False:
        print("""
⚠️  DEMO-TEST FEHLGESCHLAGEN

Das könnte bedeuten:
  - feedparser nicht installiert
  - Netzwerkfehler beim Image-Download
  - Output-Verzeichnis nicht beschreibbar
  
Lösungen:
  1. Installiere feedparser: pip3 install feedparser
  2. Überprüfe Netzwerkverbindung
  3. Überprüfe Dateiberechtigungen
  
Siehe TESTING.md für detaillierte Fehlerbehebung.
        """)
        return 1
    else:
        print("""
ℹ️  DEMO NICHT MÖGLICH

create_demo_feed.py nicht gefunden.

Manuelle Überprüfung:
  python3 rss-to-strm.py "https://your-feed.com/rss"
  ls -la output/
  
Siehe QUICK_START.md für Anleitung.
        """)
        return 0

if __name__ == "__main__":
    sys.exit(main())
