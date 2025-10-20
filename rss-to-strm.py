"""
Prerequisites:
    python3
    feedparser package (pip3 install feedparser)

Usage: 
    Change the output_library path
    Change the rssurl if desired.
    Run the script
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
#rssurl               = "https://trailers.apple.com/trailers/home/rss/newtrailers.rss"  #url of the rss feed
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
    for entry in feed['entries']:
        try:
            entry_title = entry['title'].split(" - ")[0]    
        except:
            entry_title = entry['title']
        
        # Try to get video URL from RSS 2.0 standard elements in priority order
        video_url = None
        
        # 1. Check for enclosure element (RSS Media namespace - most reliable)
        if 'enclosures' in entry and len(entry.enclosures) > 0:
            enclosure_url = entry.enclosures[0].get('href')
            if enclosure_url and enclosure_url.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.webm', '.m3u8')):
                video_url = enclosure_url
                logging.debug(f"Found video URL in enclosure: {video_url}")
        
        # 2. Fallback to link element (standard RSS)
        if not video_url and 'link' in entry:
            link_url = entry.get('link')
            if link_url and link_url.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.webm', '.m3u8')):
                video_url = link_url
                logging.debug(f"Found video URL in link: {video_url}")
        
        # 3. Check media:content (some feeds use media namespace)
        if not video_url and 'media_content' in entry:
            for media in entry.media_content:
                media_url = media.get('url')
                if media_url and media_url.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.webm', '.m3u8')):
                    video_url = media_url
                    logging.debug(f"Found video URL in media:content: {video_url}")
                    break
        
        # 4. Check summary/description for embedded links (fallback)
        if not video_url and 'summary' in entry:
            summary = entry.get('summary', '')
            # Simple regex-like check for URLs in description
            urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]*\.(?:mp4|mkv|avi|mov|webm|m3u8)', summary)
            if urls:
                video_url = urls[0]
                logging.debug(f"Found video URL in summary: {video_url}")
        
        if not video_url:
            logging.debug(f"No video URL found for entry: {entry_title}")
            continue
        
        logging.info(f"Processing: {entry_title}")
        logging.info(f"Found video for {entry_title}: {video_url}")
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

