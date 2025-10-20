# RSS 2.0 to STRM Converter

A robust, namespace-aware converter that transforms RSS 2.0 feeds (videos, podcasts, media streams) into STRM playlist files for use with media players and home theater software.

## Features

✅ **Comprehensive RSS 2.0 Support**
- Parses all major RSS 2.0 namespaces intelligently
- Multi-layer URL detection with structured fallbacks
- Atomic file operations with automatic rollback on errors

✅ **Namespace Support**
- **RSS 2.0 Standard**: `<enclosure>`, `<link>` elements with MIME type detection
- **Media RSS**: `<media:content>`, `<media:player>` elements
- **Dublin Core**: `<dc:creator>`, `<dc:date>` metadata
- **Atom Feed Format**: `<atom:link>` with content-type attributes
- **RSS Content Module**: `<content:encoded>` with embedded media

✅ **Intelligent URL Detection** (Priority Order)
1. RSS enclosure with `video/*` MIME type (highest reliability)
2. Enclosures array with video content type
3. Direct link field (if contains video extension)
4. Media namespace fields
5. Content module fields
6. Regex extraction from description (fallback)

✅ **Robust File Operations**
- Atomic replacement with temporary directory
- Automatic rollback on script failure
- Comprehensive logging at DEBUG, INFO, WARNING, ERROR levels

## Supported Video Formats

- `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, `.m3u8`
- `.ts`, `.flv`, `.ogv`, `.3gp`, `.f4v`

## Installation

```bash
# Clone or download the repository
cd RSS-2-strm

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip3 install feedparser
```

## Usage

1. **Configure the RSS URL** in `rss-to-strm.py`:
   ```python
   rssurl = "https://your-rss-feed-url.com/feed"
   ```

2. **Configure output directory** (optional):
   ```python
   output_library = "./output/"  # or your preferred path
   ```

3. **Run the script**:
   ```bash
   python3 rss-to-strm.py
   ```

## Output Structure

```
./output/
├── Episode Title 1/
│   ├── Episode Title 1.strm      (URL to video)
│   └── Episode Title 1.nfo       (Metadata for chronological sorting)
├── Episode Title 2/
│   ├── Episode Title 2.strm      (URL to video)
│   └── Episode Title 2.nfo       (Metadata for chronological sorting)
└── ...
```

### File Types

**STRM File**: Plain text file containing a single line with the direct video URL
```
https://example.com/video.mp4
```

**NFO File**: XML metadata file for Jellyfin/Kodi with:
- Episode title
- Air date (for chronological sorting)
- Plot/description
- Season/episode info
```xml
<?xml version="1.0" encoding="UTF-8"?>
<episodedetails>
  <title>Episode Title</title>
  <aired>2025-10-14</aired>
  <plot>Episode description...</plot>
  <season>1</season>
  <episode>1</episode>
</episodedetails>
```

## Example RSS Feeds

### Working Examples
- **Mediathekviewweb**: German TV (ARD, ZDF) - Uses RSS enclosures ✅
- **Most standard video podcasts**: Use Media RSS or standard RSS enclosures ✅

### Configuration Examples

#### German TV (Mediathek)
```python
rssurl = "https://mediathekviewweb.de/feed?query=%23sendertitle&everywhere=true"
output_library = "./output/mediathek/"
```

#### Generic Podcast Feed
```python
rssurl = "https://podcast-feed.example.com/feed.xml"
output_library = "./output/podcasts/"
```

## Using with Jellyfin/Kodi

### Jellyfin Setup for Chronological Sorting

1. **Add Library**: 
   - Settings → Libraries → Add Media Library
   - Choose folder → Select output directory
   - Content type: "Shows"

2. **Metadata Integration**:
   - Jellyfin automatically reads `.nfo` files
   - Videos sorted chronologically by `<aired>` date
   - Episode titles, descriptions, and metadata displayed

3. **Example Result** (chronological order):
   ```
   Drohnenalarm (aired: 2025-10-01)
   Deutsche Autos (aired: 2025-10-09)
   maischberger am 14.10.2025 (aired: 2025-10-14)
   Markus Lanz (aired: 2025-10-16)
   ```

### Kodi Setup

Similar to Jellyfin:
1. Add folder to library
2. Kodi reads `.strm` and `.nfo` files automatically
3. Content appears with full metadata
4. Sorted by aired date

## Logging

The script provides detailed logging output:

```
2025-10-20 04:16:32 - INFO - Fetching RSS feed from: https://...
2025-10-20 04:16:32 - INFO - Found 50 entries in RSS feed
2025-10-20 04:16:32 - INFO - ✓ Processing: Episode Title
2025-10-20 04:16:32 - INFO -   Video URL: https://...mp4
2025-10-20 04:16:32 - INFO -   Source: rss_enclosure
2025-10-20 04:16:32 - INFO -   Aired: 2025-10-14
2025-10-20 04:16:32 - INFO - Creating STRM file: ./output/Episode Title/Episode Title.strm
2025-10-20 04:16:32 - INFO - Creating NFO file: ./output/Episode Title/Episode Title.nfo
```

### URL Detection Sources

The logging shows which namespace was used to find each video:

| Source | Description |
|--------|-------------|
| `rss_enclosure` | RSS 2.0 `<enclosure>` with `video/*` MIME type |
| `enclosure_array` | Enclosures array element |
| `media_content` | Media RSS `<media:content>` |
| `media_link` | Media RSS link element |
| `atom_link` | Atom format `<atom:link>` |
| `content_encoded` | RSS Content Module `<content:encoded>` |
| `direct_link` | Direct `<link>` field with video extension |
| `description_regex` | Fallback regex extraction |

## Error Handling

- **SSL Certificate Issues**: Automatically handled with context bypass
- **Missing Videos**: Gracefully skipped with debug logging
- **Failed Script Execution**: Rolls back changes, preserves existing output
- **Temporary Files**: Automatically cleaned up on error

## Architecture

### URL Detection Strategy

The script implements a **structured, namespace-aware** approach rather than trial-and-error:

1. **Analysis Phase**: Inspects all RSS namespaces
2. **Priority Hierarchy**: Uses MIME types and standard attributes first
3. **Fallback Chain**: Only uses regex as absolute last resort
4. **Source Tracking**: Logs which namespace was used for transparency

### File Operations

```
1. Parse RSS feed
2. Extract video URLs with namespace analysis
3. Create temporary directory
4. Generate .strm files
5. On success: Atomic swap (replace old output)
6. On failure: Cleanup temp, preserve existing output
```

## Technical Details

### Dependencies
- **feedparser**: RSS/Atom parsing with namespace support
- **ssl**: Certificate handling for HTTPS feeds
- **tempfile/shutil**: Atomic file operations
- **logging**: Comprehensive debug output
- **re**: Regex fallback for edge cases

### File Processing
- **Filename normalization**: Removes invalid filesystem characters
- **Single-level structure**: Item title → .strm file (no subfolders)
- **Atomic operations**: Temp directory swap ensures consistency

## Troubleshooting

### No videos found
- Check RSS feed format with `logging` at DEBUG level
- Verify video URLs exist in feed elements
- Check network connectivity to RSS source

### SSL Certificate errors
- Script automatically handles common SSL issues
- For custom certificates, modify the ssl context

### Files not appearing
- Check `output_library` path in configuration
- Verify write permissions to output directory
- Review logs for specific error messages

## Future Enhancements

- [ ] Support for multiple video qualities (use highest resolution)
- [ ] Subtitle extraction (.srt, .ass files)
- [ ] Metadata import (cover art, description)
- [ ] Channel-specific grouping
- [ ] Schedule-based auto-refresh
- [ ] Configuration file support (.ini, .yaml)

## License

MIT (or your preferred license)