"""
RSS 2.0 Feed to STRM Converter
Converts RSS 2.0 feeds (videos, podcasts, media) to STRM playlist files for media players.

Prerequisites:
    python3
    feedparser package (pip3 install feedparser)

Usage: 
    1. Change the rssurl if desired
    2. Change the output_library path
    3. Run the script

Supported RSS Namespaces:
    - RSS 2.0 Standard (enclosures, links, MIME types)
    - Media RSS (media:content, media:player, media:thumbnail)
    - Dublin Core (dc:creator, dc:date, etc.)
    - Atom (atom:link with video/* types)
    - RSS Content Module (content:encoded)

Video URL Detection Strategy (Priority Order):
    1. RSS enclosure links with video/* MIME type (highest reliability)
    2. Enclosures array with video/* MIME type
    3. Direct link field (if contains video file extension)
    4. media: namespace fields (Media RSS)
    5. content: namespace fields (Content Module)
    6. Fallback: regex extraction from description/summary (last resort)

Supported Video Formats:
    .mp4, .mkv, .avi, .mov, .webm, .m3u8, .ts, .flv, .ogv, .3gp, .f4v

Output Structure:
    ./output/
    ├── Title 1/
    │   └── Title 1.strm
    ├── Title 2/
    │   └── Title 2.strm
    └── ...

File Operations:
    - Atomic replacement: writes to temp directory first, swaps on success
    - Rollback on error: preserves existing output on script failure
    - Comprehensive logging: DEBUG, INFO, WARNING, ERROR levels
"""

import feedparser, os
import logging
import ssl
import urllib.request
import re
import shutil
import tempfile
import sys
from datetime import datetime
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Fix SSL certificate verification issue for feedparser
ssl._create_default_https_context = ssl._create_unverified_context

#************************************************************************************************************************
# Configuration - can be overridden via command line arguments
rssurl               = "https://mediathekviewweb.de/feed?query=%3E30%20%23markus%2CLanz%20%23maischberger%20%23caren%2Cmiosga%20%23presseclub%20%23hart%2Caber%2Cfair%20%23maybrit%2Cillner%20%23phoenix%2Crunde%20%23internationaler%2Cfr%C3%BChschoppen&everywhere=true"  #url of the rss feed
output_library       = "./output/"      #base path for output library
filter_keywords      = "Gebärdensprache"               #comma-separated list of keywords to filter out (case-insensitive). Items with matching titles are excluded.
                                        #example: "Gebärdensprache,Untertitel,Preview"

# Parse command line arguments
if len(sys.argv) > 1:
    rssurl = sys.argv[1]
    logging.info(f"RSS URL override via command line: {rssurl}")

if len(sys.argv) > 2:
    output_library = sys.argv[2]
    logging.info(f"Output library override via command line: {output_library}")

if len(sys.argv) > 3:
    filter_keywords = sys.argv[3]
    logging.info(f"Filter keywords override via command line: {filter_keywords}")

# Parse filter keywords into a list (case-insensitive matching)
filter_list = [keyword.strip().lower() for keyword in filter_keywords.split(',') if keyword.strip()]
if filter_list:
    logging.info(f"Filter keywords active: {filter_list}")

logging.info(f"Configuration - RSS URL: {rssurl}")
logging.info(f"Configuration - Output Library: {output_library}")
logging.info(f"Configuration - Absolute Output Library Path: {os.path.abspath(output_library)}")
#************************************************************************************************************************


#use feedparser to grab rss feed and extract all video urls
def get_feed(url):
    logging.info(f"Fetching RSS feed from: {url}")
    feed = feedparser.parse(url)
    
    logging.debug(f"Feed title: {feed.get('feed', {}).get('title', 'N/A')}")
    logging.debug(f"Feed version: {feed.get('version', 'N/A')}")
    logging.debug(f"Number of entries in feed object: {len(feed.get('entries', []))}")
    
    if not feed.entries:
        logging.warning("No entries found in RSS feed")
        logging.warning(f"Feed keys available: {list(feed.keys())}")
        if feed.get('bozo_exception'):
            logging.warning(f"Feed parsing error: {feed.bozo_exception}")
        return {}
    
    logging.info(f"Found {len(feed.entries)} entries in RSS feed")

    #create dictionary with title and list of video direct urls
    dict = {}
    
    # Define valid video file extensions
    valid_extensions = ('.mp4', '.mkv', '.avi', '.mov', '.webm', '.m3u8', '.ts', '.flv', '.ogv', '.3gp', '.f4v')
    
    def is_video_url(url):
        """Check if URL ends with a valid video extension"""
        if not url:
            return False
        # Remove query parameters to check extension
        base_url = url.split('?')[0].lower()
        return base_url.endswith(valid_extensions)
    
    def is_video_mime_type(mime_type):
        """Check if MIME type indicates video content"""
        if not mime_type:
            return False
        mime_lower = mime_type.lower()
        return mime_lower.startswith('video/') or mime_lower in ['application/x-mpegurl', 'application/vnd.apple.mpegurl']
    
    def extract_url_from_links_array(entry):
        """Extract video URL from links array using namespace-aware approach"""
        if 'links' not in entry:
            return None, None  # (url, source_description)
        
        # Priority 1: Look for enclosure with video/* type (RSS 2.0 standard)
        for link in entry.links:
            if link.get('rel') == 'enclosure' and is_video_mime_type(link.get('type')):
                url = link.get('href')
                if url:
                    logging.debug(f"✓ Found video via RSS enclosure (rel=enclosure, type={link.get('type')})")
                    return url, "rss_enclosure"
        
        # Priority 2: Look for media:content links (Media RSS namespace)
        for link in entry.links:
            if link.get('rel') == 'media' or 'media' in link.get('type', '').lower():
                url = link.get('href')
                if url and (is_video_url(url) or is_video_mime_type(link.get('type'))):
                    logging.debug(f"✓ Found video via media: namespace link")
                    return url, "media_link"
        
        # Priority 3: atom:link with relation that implies video
        for link in entry.links:
            link_type = link.get('type', '').lower()
            if is_video_mime_type(link_type):
                url = link.get('href')
                if url:
                    logging.debug(f"✓ Found video via atom:link with video MIME type ({link_type})")
                    return url, "atom_link"
        
        # Priority 4: alternate links with video file extension
        for link in entry.links:
            if link.get('rel') == 'alternate':
                url = link.get('href')
                if url and is_video_url(url):
                    logging.debug(f"✓ Found video via alternate link with video extension")
                    return url, "alternate_link"
        
        # Priority 5: Any other link with video extension
        for link in entry.links:
            url = link.get('href')
            if url and is_video_url(url):
                logging.debug(f"✓ Found video via generic link")
                return url, "generic_link"
        
        return None, None
    
    def extract_url_from_enclosures(entry):
        """Extract video URL from enclosures array"""
        if 'enclosures' not in entry or not entry.enclosures:
            return None, None
        
        for enclosure in entry.enclosures:
            if is_video_mime_type(enclosure.get('type')):
                url = enclosure.get('href')
                if url:
                    logging.debug(f"✓ Found video via enclosures array (type={enclosure.get('type')})")
                    return url, "enclosure_array"
        
        # Fallback: try any enclosure with video extension
        for enclosure in entry.enclosures:
            url = enclosure.get('href')
            if url and is_video_url(url):
                logging.debug(f"✓ Found video via enclosure with video extension")
                return url, "enclosure_fallback"
        
        return None, None
    
    def extract_url_from_media_namespace(entry):
        """Extract video URL from media: namespace fields"""
        # media:content (Media RSS namespace)
        if 'media_content' in entry and entry.media_content:
            for media in entry.media_content:
                if is_video_mime_type(media.get('type')):
                    url = media.get('url')
                    if url:
                        logging.debug(f"✓ Found video via media:content namespace")
                        return url, "media_content"
        
        # media:player
        if 'media_player' in entry:
            url = entry.media_player.get('url')
            if url and is_video_url(url):
                logging.debug(f"✓ Found video via media:player")
                return url, "media_player"
        
        return None, None
    
    def extract_url_from_content_namespace(entry):
        """Extract video URL from content: namespace fields"""
        # content:encoded
        if 'content' in entry and isinstance(entry.content, list) and entry.content:
            for content_item in entry.content:
                content_value = content_item.get('value', '')
                # Look for video URLs in HTML-encoded content
                urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]*\.(?:mp4|mkv|avi|mov|webm|m3u8|ts|flv|ogv|3gp|f4v)', content_value)
                if urls:
                    logging.debug(f"✓ Found video via content:encoded namespace")
                    return urls[0], "content_encoded"
        
        return None, None
    
    def extract_url_from_description(entry):
        """Last resort: extract video URL from summary/description via regex"""
        for field in ['summary', 'description', 'subtitle']:
            if field in entry:
                text = entry.get(field, '')
                if isinstance(text, str):
                    urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]*\.(?:mp4|mkv|avi|mov|webm|m3u8|ts|flv|ogv|3gp|f4v)', text)
                    if urls:
                        logging.debug(f"✓ Found video via regex in {field} field")
                        return urls[0], "description_regex"
        
        return None, None
    
    for entry in feed['entries']:
        try:
            entry_title = entry['title'].split(" - ")[0]    
        except:
            entry_title = entry['title']
        
        # Check if title should be filtered out (case-insensitive)
        should_filter = False
        if filter_list:
            title_lower = entry_title.lower()
            for keyword in filter_list:
                if keyword in title_lower:
                    logging.info(f"⊘ Filtered out: {entry_title} (matches keyword: '{keyword}')")
                    should_filter = True
                    break
        
        if should_filter:
            continue
        video_url = None
        source = None
        
        # Strategy 1: links array (highest priority - most structured)
        video_url, source = extract_url_from_links_array(entry)
        
        # Strategy 2: enclosures array (RSS 2.0 standard)
        if not video_url:
            video_url, source = extract_url_from_enclosures(entry)
        
        # Strategy 3: direct 'link' field (may be a direct video URL)
        if not video_url and 'link' in entry:
            link_url = entry.get('link')
            if link_url and is_video_url(link_url):
                video_url = link_url
                source = "direct_link"
                logging.debug(f"✓ Found video via direct link field")
        
        # Strategy 4: media: namespace (Media RSS)
        if not video_url:
            video_url, source = extract_url_from_media_namespace(entry)
        
        # Strategy 5: content: namespace
        if not video_url:
            video_url, source = extract_url_from_content_namespace(entry)
        
        # Strategy 6: Last resort - description/summary regex
        if not video_url:
            video_url, source = extract_url_from_description(entry)
        
        if not video_url:
            logging.debug(f"⚠ No video URL found for entry: {entry_title}")
            continue
        
        # Extract metadata for NFO file with namespace awareness
        metadata = {
            'title': entry_title,
            'aired': None,
            'summary': None,
            'author': None,
            'tags': [],
            'duration': None,
            'thumbnail': None,  # NEW: Thumbnail URL
            'source_url': video_url
        }
        
        # 1. Extract title from various namespace sources
        # Priority: explicit title_detail > dc:title > entry title
        if 'title' in entry:
            metadata['title'] = entry_title
        
        # 2. Extract aired date from various sources
        aired_date = None
        
        # Priority 1: 'published' field (standard RSS)
        if 'published' in entry:
            try:
                aired_dt = parsedate_to_datetime(entry['published'])
                aired_date = aired_dt.strftime('%Y-%m-%d')
                logging.debug(f"✓ Extracted aired date from 'published': {aired_date}")
            except Exception as e:
                logging.debug(f"Could not parse published date: {entry.get('published')}")
        
        # Priority 2: 'updated' field (Atom namespace fallback)
        if not aired_date and 'updated' in entry:
            try:
                updated_dt = parsedate_to_datetime(entry['updated'])
                aired_date = updated_dt.strftime('%Y-%m-%d')
                logging.debug(f"✓ Extracted aired date from 'updated' (Atom): {aired_date}")
            except Exception as e:
                logging.debug(f"Could not parse updated date: {entry.get('updated')}")
        
        metadata['aired'] = aired_date
        
        # 3. Extract description/summary from various namespace sources
        # Priority: content:encoded > summary > dc:description
        summary_text = None
        
        # Priority 1: content:encoded (Content Module namespace)
        if 'content' in entry and isinstance(entry.content, list) and entry.content:
            content_value = entry.content[0].get('value', '')
            # Strip HTML tags
            summary_text = re.sub('<[^<]+?>', '', content_value).strip()
            logging.debug(f"✓ Extracted summary from content:encoded namespace")
        
        # Priority 2: summary field (standard RSS)
        if not summary_text and 'summary' in entry:
            summary_text = entry.get('summary', '').strip()
            logging.debug(f"✓ Extracted summary from 'summary' field")
        
        # Priority 3: subtitle (alternative)
        if not summary_text and 'subtitle' in entry:
            summary_text = entry.get('subtitle', '').strip()
            logging.debug(f"✓ Extracted summary from 'subtitle' field")
        
        # Limit to 500 chars
        if summary_text:
            metadata['summary'] = summary_text[:500]
        
        # 4. Extract author information (Dublin Core & standard)
        # Priority: author (dc:creator equivalent) > contributor
        if 'author' in entry:
            metadata['author'] = entry.get('author')
            logging.debug(f"✓ Extracted author: {metadata['author']}")
        elif 'author_detail' in entry:
            author_detail = entry.get('author_detail', {})
            if isinstance(author_detail, dict):
                metadata['author'] = author_detail.get('name', author_detail.get('href'))
                logging.debug(f"✓ Extracted author from author_detail: {metadata['author']}")
        
        # 5. Extract tags/categories (RSS categories or custom tags)
        if 'tags' in entry and entry.tags:
            metadata['tags'] = [tag.get('term', tag) for tag in entry.tags]
            logging.debug(f"✓ Extracted tags: {metadata['tags']}")
        
        # 6. Extract duration if available (Media RSS namespace)
        if 'duration' in entry:
            try:
                duration_sec = int(entry.get('duration', 0))
                duration_min = duration_sec // 60
                metadata['duration'] = f"{duration_min} min"
                logging.debug(f"✓ Extracted duration: {metadata['duration']}")
            except:
                pass
        
        # 7. Extract thumbnail/image with namespace awareness
        # Priority 1: media:thumbnail (Media RSS namespace)
        if 'media_thumbnail' in entry and entry.media_thumbnail:
            thumbnail_url = entry.media_thumbnail[0].get('url')
            if thumbnail_url:
                metadata['thumbnail'] = thumbnail_url
                logging.debug(f"✓ Extracted thumbnail from media:thumbnail")
        
        # Priority 2: media:content with thumbnail (Media RSS)
        if not metadata['thumbnail'] and 'media_content' in entry:
            for media in entry.media_content:
                if media.get('medium') == 'image' or 'image' in media.get('type', '').lower():
                    thumbnail_url = media.get('url')
                    if thumbnail_url:
                        metadata['thumbnail'] = thumbnail_url
                        logging.debug(f"✓ Extracted thumbnail from media:content")
                        break
        
        # Priority 3: image element (various RSS formats)
        if not metadata['thumbnail'] and 'image' in entry:
            image_data = entry.get('image')
            if isinstance(image_data, dict):
                thumbnail_url = image_data.get('url')
                if thumbnail_url:
                    metadata['thumbnail'] = thumbnail_url
                    logging.debug(f"✓ Extracted thumbnail from image element")
            elif isinstance(image_data, str):
                metadata['thumbnail'] = image_data
                logging.debug(f"✓ Extracted thumbnail from image string")
        
        # Priority 4: RSS enclosure with image MIME type
        if not metadata['thumbnail'] and 'enclosures' in entry:
            for enclosure in entry.enclosures:
                if 'image' in enclosure.get('type', '').lower():
                    thumbnail_url = enclosure.get('href')
                    if thumbnail_url:
                        metadata['thumbnail'] = thumbnail_url
                        logging.debug(f"✓ Extracted thumbnail from image enclosure")
                        break
        
        # Priority 5: links array with image relation/type
        if not metadata['thumbnail'] and 'links' in entry:
            for link in entry.links:
                link_type = link.get('type', '').lower()
                link_rel = link.get('rel', '').lower()
                if 'image' in link_type or 'image' in link_rel or link_rel == 'preview':
                    thumbnail_url = link.get('href')
                    if thumbnail_url:
                        metadata['thumbnail'] = thumbnail_url
                        logging.debug(f"✓ Extracted thumbnail from links (rel={link_rel})")
                        break
        
        # Priority 6: Try to extract from summary/HTML (last resort)
        if not metadata['thumbnail'] and 'summary' in entry:
            summary = entry.get('summary', '')
            # Look for img tags with src attributes
            img_urls = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', summary)
            if img_urls:
                # Filter for image URLs (jpg, png, webp, etc)
                image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp')
                for url in img_urls:
                    if url.lower().endswith(image_extensions):
                        metadata['thumbnail'] = url
                        logging.debug(f"✓ Extracted thumbnail from summary HTML")
                        break
        
        if metadata['thumbnail']:
            logging.info(f"  Thumbnail: {metadata['thumbnail'][:60]}...")
        
        logging.info(f"✓ Processing: {entry_title}")
        logging.info(f"  Video URL: {video_url}")
        logging.info(f"  Source: {source}")
        if metadata['aired']:
            logging.info(f"  Aired: {metadata['aired']}")
        
        dict[entry_title] = {
            'url': video_url,
            'metadata': metadata
        }
    
    return dict


#function to normalize the name to remove invalid chars for file names
def normalize_filename(str):
    bad_chars = '<>:"/\|?*'
    for char in bad_chars:
        str = str.replace(char, '')
    return str

def create_nfo_xml(metadata):
    """Create NFO XML content for Jellyfin/Kodi metadata with namespace-aware fields"""
    root = ET.Element('episodedetails')
    
    # Title
    title_elem = ET.SubElement(root, 'title')
    title_elem.text = metadata.get('title', 'Unknown')
    
    # Aired date (for chronological sorting)
    if metadata.get('aired'):
        aired_elem = ET.SubElement(root, 'aired')
        aired_elem.text = metadata['aired']
    
    # Plot/Description (from content:encoded or summary)
    if metadata.get('summary'):
        plot_elem = ET.SubElement(root, 'plot')
        plot_elem.text = metadata['summary']
    
    # Director/Author (from dc:creator or author field)
    if metadata.get('author'):
        director_elem = ET.SubElement(root, 'director')
        director_elem.text = metadata['author']
    
    # Genre/Tags (from category or tags)
    if metadata.get('tags'):
        for tag in metadata['tags']:
            genre_elem = ET.SubElement(root, 'genre')
            genre_elem.text = tag
    
    # Duration (from Media RSS namespace)
    if metadata.get('duration'):
        runtime_elem = ET.SubElement(root, 'runtime')
        runtime_elem.text = metadata['duration']
    
    # Thumbnail/Cover image (from various namespace sources)
    if metadata.get('thumbnail'):
        thumb_elem = ET.SubElement(root, 'thumb')
        thumb_elem.text = metadata['thumbnail']
        # Also add as cover (Jellyfin compatibility)
        cover_elem = ET.SubElement(root, 'cover')
        cover_elem.text = metadata['thumbnail']
    
    # Add generic season/episode info for organization
    season_elem = ET.SubElement(root, 'season')
    season_elem.text = '1'
    
    episode_elem = ET.SubElement(root, 'episode')
    episode_elem.text = '1'
    
    # Indent for readability
    ET.indent(root, space='  ')
    
    return ET.tostring(root, encoding='unicode')

#create directories and write out strm and nfo files
def write_strm_files(video_dict, temp_output_library):
    logging.info(f"Processing {len(video_dict)} items")
    for item_title in video_dict:
        item_data = video_dict[item_title]
        video_url = item_data['url']
        metadata = item_data['metadata']
        
        item_path = os.path.join(temp_output_library, normalize_filename(item_title))
        item_strm = os.path.join(item_path, normalize_filename(item_title) + ".strm")
        item_nfo = os.path.join(item_path, normalize_filename(item_title) + ".nfo")

        if not os.path.exists(temp_output_library):
            logging.debug(f"Creating library directory: {temp_output_library}")
            os.mkdir(temp_output_library)                
        if not os.path.exists(item_path):
            logging.debug(f"Creating item directory: {item_path}")
            os.mkdir(item_path)
        
        # Write STRM file (URL pointer)
        logging.info(f"Creating STRM file: {item_strm}")
        with open(item_strm, "w") as f:
            f.write(video_url)
        
        # Write NFO file (metadata for chronological sorting)
        logging.info(f"Creating NFO file: {item_nfo}")
        nfo_content = create_nfo_xml(metadata)
        with open(item_nfo, "w", encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(nfo_content)
        
        # Download and save thumbnail if URL available
        if metadata.get('thumbnail'):
            thumbnail_url = metadata['thumbnail']
            
            # Determine file extension from URL
            thumb_filename = None
            if thumbnail_url.lower().endswith(('.jpg', '.jpeg')):
                thumb_filename = normalize_filename(item_title) + ".jpg"
            elif thumbnail_url.lower().endswith('.png'):
                thumb_filename = normalize_filename(item_title) + ".png"
            elif thumbnail_url.lower().endswith('.webp'):
                thumb_filename = normalize_filename(item_title) + ".webp"
            elif thumbnail_url.lower().endswith('.gif'):
                thumb_filename = normalize_filename(item_title) + ".gif"
            else:
                # Try to extract from URL query parameters
                if '?' in thumbnail_url:
                    base_url = thumbnail_url.split('?')[0]
                    if base_url.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                        ext = base_url.split('.')[-1]
                        thumb_filename = normalize_filename(item_title) + "." + ext
                        logging.debug(f"✓ Extracted extension from URL base: {ext}")
                
                # If still no filename, default to jpg
                if not thumb_filename:
                    thumb_filename = normalize_filename(item_title) + ".jpg"
            
            if thumb_filename:
                item_thumb = os.path.join(item_path, thumb_filename)
                try:
                    logging.info(f"Downloading thumbnail: {item_thumb}")
                    # Download thumbnail with SSL context bypass
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    urllib.request.urlopen(thumbnail_url, context=ctx).read()
                    
                    with urllib.request.urlopen(thumbnail_url, context=ctx) as response:
                        thumbnail_data = response.read()
                    
                    with open(item_thumb, 'wb') as f:
                        f.write(thumbnail_data)
                    
                    # Update NFO to use local thumbnail path
                    logging.debug(f"✓ Thumbnail saved: {thumb_filename}")
                    
                except Exception as e:
                    logging.warning(f"Could not download thumbnail: {e}")
                    logging.debug(f"  URL: {thumbnail_url}")                    




#build the video dictionary
video_dict = get_feed(rssurl)

# Create files in a temporary directory first
temp_dir = tempfile.mkdtemp(prefix='rss_to_strm_')
logging.info(f"Writing to temporary directory: {temp_dir}")

try:
    write_strm_files(video_dict, temp_dir)
    logging.info("All files written successfully to temporary directory")
    
    # If successful, replace the old output_library with the new one
    if os.path.exists(output_library):
        logging.info(f"Removing old output directory: {output_library}")
        shutil.rmtree(output_library)
    
    logging.info(f"Moving temporary directory to final location: {output_library}")
    shutil.move(temp_dir, output_library)
    
    logging.info("Script completed successfully")
    
except Exception as e:
    logging.error(f"Error during file generation: {e}")
    logging.info("Cleaning up temporary directory without modifying existing output")
    shutil.rmtree(temp_dir, ignore_errors=True)
    logging.error("Script failed - existing output retained")

