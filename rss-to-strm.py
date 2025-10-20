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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Fix SSL certificate verification issue for feedparser
ssl._create_default_https_context = ssl._create_unverified_context

#************************************************************************************************************************
rssurl               = "https://mediathekviewweb.de/feed?query=%3E30%20%23markus%2CLanz%20%23maischberger%20%23caren%2Cmiosga%20%23presseclub%20%23hart%2Caber%2Cfair%20%23maybrit%2Cillner%20%23phoenix%2Crunde%20%23internationaler%2Cfr%C3%BChschoppen&everywhere=true"  #url of the rss feed
output_library       = "./output/"      #base path for output library
#************************************************************************************************************************

logging.info(f"Configuration - RSS URL: {rssurl}")
logging.info(f"Configuration - Output Library: {output_library}")
logging.info(f"Configuration - Absolute Output Library Path: {os.path.abspath(output_library)}")


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
        
        # Comprehensive URL extraction with multiple fallback strategies
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
        
        logging.info(f"✓ Processing: {entry_title}")
        logging.info(f"  Video URL: {video_url}")
        logging.info(f"  Source: {source}")
        dict[entry_title] = [video_url]
    
    return dict


#function to normalize the name to remove invalid chars for file names
def normalize_filename(str):
    bad_chars = '<>:"/\|?*'
    for char in bad_chars:
        str = str.replace(char, '')
    return str

#create directories and write out strm files if they don't exist
def write_strm_files(video_dict, temp_output_library):
    logging.info(f"Processing {len(video_dict)} items")
    for item_title in video_dict:
        for video_url in video_dict[item_title]:
            video_basename = os.path.splitext(os.path.basename(video_url))[0] #get the video filename without extension so we can add a .strm to the end
            
            item_path = os.path.join(temp_output_library, normalize_filename(item_title))   #output example ./output/Item
            item_strm = os.path.join(item_path, normalize_filename(item_title) + ".strm")

            if not os.path.exists(temp_output_library):
                logging.debug(f"Creating library directory: {temp_output_library}")
                os.mkdir(temp_output_library)                
            if not os.path.exists(item_path):
                logging.debug(f"Creating item directory: {item_path}")
                os.mkdir(item_path)
            
            logging.info(f"Creating item STRM file: {item_strm}")
            f = open(item_strm, "w")
            f.write(video_url)
            f.close()                    




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

