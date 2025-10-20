#!/usr/bin/env python3
"""
Test Helper: Erstellt einen Demo-RSS-Feed mit Thumbnails für Testing
"""

DEMO_RSS_WITH_THUMBNAILS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" 
     xmlns:media="http://search.yahoo.com/mrss/"
     xmlns:content="http://purl.org/rss/1.0/modules/content/"
     xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>Demo Feed with Thumbnails</title>
    <link>https://example.com</link>
    <description>Test Feed für Thumbnail-Extraktion</description>
    
    <!-- Entry 1: media:thumbnail (Priority 1) -->
    <item>
      <title>Demo Video 1 - Media Thumbnail</title>
      <link>https://example.com/video1</link>
      <published>2025-10-16T12:00:00Z</published>
      <dc:creator>Test Creator</dc:creator>
      <category>Demo</category>
      <description>Video mit media:thumbnail</description>
      <media:thumbnail url="https://picsum.photos/300/400?random=1" />
      <media:content url="https://example.com/video1.mp4" type="video/mp4" />
    </item>
    
    <!-- Entry 2: media:content image (Priority 2) -->
    <item>
      <title>Demo Video 2 - Media Content Image</title>
      <link>https://example.com/video2</link>
      <published>2025-10-15T12:00:00Z</published>
      <dc:creator>Test Creator</dc:creator>
      <category>Demo</category>
      <description>Video mit media:content image</description>
      <media:content type="image/jpeg" medium="image" url="https://picsum.photos/300/400?random=2" />
      <media:content url="https://example.com/video2.mp4" type="video/mp4" />
    </item>
    
    <!-- Entry 3: Enclosure mit image (Priority 4) -->
    <item>
      <title>Demo Video 3 - Image Enclosure</title>
      <link>https://example.com/video3</link>
      <published>2025-10-14T12:00:00Z</published>
      <dc:creator>Test Creator</dc:creator>
      <category>Demo</category>
      <description>Video mit enclosure image</description>
      <enclosure url="https://picsum.photos/300/400?random=3" type="image/jpeg" length="50000" />
      <media:content url="https://example.com/video3.mp4" type="video/mp4" />
    </item>
    
    <!-- Entry 4: HTML img in summary (Priority 6 - Fallback) -->
    <item>
      <title>Demo Video 4 - HTML Image</title>
      <link>https://example.com/video4</link>
      <published>2025-10-13T12:00:00Z</published>
      <dc:creator>Test Creator</dc:creator>
      <category>Demo</category>
      <summary>&lt;img src="https://picsum.photos/300/400?random=4" /&gt; &lt;p&gt;Video mit HTML img Tag&lt;/p&gt;</summary>
      <media:content url="https://example.com/video4.mp4" type="video/mp4" />
    </item>
    
    <!-- Entry 5: Mehrere media:thumbnails (erstes wird genommen) -->
    <item>
      <title>Demo Video 5 - Multiple Thumbnails</title>
      <link>https://example.com/video5</link>
      <published>2025-10-12T12:00:00Z</published>
      <dc:creator>Test Creator</dc:creator>
      <category>Demo</category>
      <description>Video mit mehreren Thumbnails</description>
      <media:thumbnail url="https://picsum.photos/300/400?random=5a" />
      <media:thumbnail url="https://picsum.photos/300/400?random=5b" />
      <media:content url="https://example.com/video5.mp4" type="video/mp4" />
    </item>
    
    <!-- Entry 6: Kein Thumbnail (Test für Fallback) -->
    <item>
      <title>Demo Video 6 - No Thumbnail</title>
      <link>https://example.com/video6</link>
      <published>2025-10-11T12:00:00Z</published>
      <dc:creator>Test Creator</dc:creator>
      <category>Demo</category>
      <description>Video ohne Thumbnail - sollte keine Fehler verursachen</description>
      <media:content url="https://example.com/video6.mp4" type="video/mp4" />
    </item>
    
  </channel>
</rss>"""

if __name__ == "__main__":
    import sys
    import os
    
    # Speichert Demo-RSS in /tmp für schnelles Testen
    output_path = "/tmp/demo_feed_with_thumbnails.xml"
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(DEMO_RSS_WITH_THUMBNAILS)
    
    print(f"✅ Demo RSS Feed erstellt: {output_path}")
    print()
    print("Verwendung:")
    print("=" * 60)
    print("1. Speichere diesen Dateinamen und modifiziere rss-to-strm.py:")
    print()
    print("   Ändere diese Zeile in rss-to-strm.py:")
    print("   ```")
    print("   RSS_FEED_URL = 'https://mediathekviewweb.de/feed'")
    print("   ```")
    print()
    print("   Zu dieser Zeile (zum Testen):")
    print("   ```")
    print(f"   RSS_FEED_URL = 'file://{output_path}'")
    print("   # oder")
    print(f"   RSS_FEED_URL = '{output_path}'  # (funktioniert auch)")
    print("   ```")
    print()
    print("2. Oder führe direkt aus:")
    print(f"   python3 rss-to-strm.py {output_path}")
    print()
    print("3. Das Skript wird dann:")
    print("   - Alle 6 Demo-Videos verarbeiten")
    print("   - Thumbnails aus verschiedenen Quellen extrahieren")
    print("   - Bilder herunterladen (von picsum.photos)")
    print("   - NFO-Dateien mit <thumb> und <cover> generieren")
    print()
    print("Feed-Inhalt:")
    print("=" * 60)
    print(f"- 6 Demo-Videos mit verschiedenen Thumbnail-Quellen")
    print(f"- Entry 1: media:thumbnail (Priority 1)")
    print(f"- Entry 2: media:content image (Priority 2)")
    print(f"- Entry 3: enclosure image (Priority 4)")
    print(f"- Entry 4: HTML img tag (Priority 6)")
    print(f"- Entry 5: Mehrere media:thumbnails")
    print(f"- Entry 6: Kein Thumbnail (Fallback)")
