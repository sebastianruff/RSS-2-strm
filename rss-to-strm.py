"""
Prerequisites:
    python3
    feedparser and yt-dlp packages (pip3 install feedparser yt-dlp)

Usage: 
    Change the output_library path
    Change the rssurl and/or preferred_resolution if desired.
    Run the script
"""

import feedparser, os
from yt_dlp import YoutubeDL
import logging
import ssl
import urllib.request

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Fix SSL certificate verification issue
ssl._create_default_https_context = ssl._create_unverified_context

# Create an unverified HTTPS context for urllib
ssl_context = ssl._create_unverified_context()
urllib.request.HTTPSHandler(context=ssl_context)

#************************************************************************************************************************
#rssurl               = "https://trailers.apple.com/trailers/home/rss/newtrailers.rss"  #url of the rss feed
rssurl               = "https://mediathekviewweb.de/feed?query=%3E30%20%23markus%2CLanz%20%23maischberger%20%23caren%2Cmiosga%20%23presseclub%20%23hart%2Caber%2Cfair%20%23maybrit%2Cillner%20%23phoenix%2Crunde%20%23internationaler%2Cfr%C3%BChschoppen&everywhere=true"  #url of the rss feed
preferred_resolution = "hd1080"         #preferred resolution of the video - valid options are "sd" "hd720" or "hd1080"   
output_library       = "./output/"      #base path for output library
#************************************************************************************************************************

logging.info(f"Configuration - RSS URL: {rssurl}")
logging.info(f"Configuration - Preferred Resolution: {preferred_resolution}")
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
        
        # Try to get a valid link from the entry
        link = entry.get('link') or entry.get('id')
        if not link:
            logging.debug(f"No link found for entry: {entry_title}")
            continue
        
        logging.info(f"Processing: {entry_title}")
        videos = get_video_url(link, preferred_resolution)
        if len(videos) > 0:
            logging.info(f"Found {len(videos)} video(s) for {entry_title}")
            dict[entry_title] = videos
        else:
            logging.warning(f"No videos found for {entry_title}")
    return dict

#use yt-dlp to find the direct urls of video files
def get_video_url(url, res):
    direct_urls = []
    
    # If URL is already a direct video file, return it as-is
    if url.endswith('.mp4') or url.endswith('.mkv') or url.endswith('.avi') or url.endswith('.mov'):
        logging.debug(f"Direct video file detected: {url}")
        direct_urls.append(url)
        return direct_urls
    
    try:
        logging.debug(f"Extracting video info from: {url}")
        ydl_opts = {
            'skip_unavailable_fragments': True,
            'socket_timeout': 30,
            'no_warnings': False,
            'quiet': False,
            'no_check_certificate': True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
    except Exception as e:
        logging.error(f"Error extracting info from {url}: {e}")
        return direct_urls
    
    # Handle both single entry and multiple entries
    entries = info_dict.get('entries', [info_dict]) if 'entries' in info_dict else [info_dict]
    
    for entry in entries:      
        formats = entry.get('formats', [])
        logging.debug(f"Found {len(formats)} formats available")
        for f in formats:
            format_id = f.get('format_id', '')
            # Check if this format matches the preferred resolution
            if res in format_id or format_id == res:
                fname = os.path.basename(f.get('url', ''))
                # For generic feeds, we're less strict about filtering
                if fname:
                    logging.debug(f"Selected format: {format_id} - {fname}")
                    direct_urls.append(f['url'])
    
    return direct_urls
    
#function to normalize the name to remove invalid chars for file names
def normalize_filename(str):
    bad_chars = '<>:"/\|?*'
    for char in bad_chars:
        str = str.replace(char, '')
    return str

#create directories and write out strm files if they don't exist
def write_strm_files(video_dict):
    logging.info(f"Processing {len(video_dict)} items")
    for item_title in video_dict:
        for video_url in video_dict[item_title]:
            video_basename = os.path.splitext(os.path.basename(video_url))[0] #get the video filename without extension so we can add a .strm to the end
            
            item_path = os.path.join(output_library, normalize_filename(item_title))   #output example ./output/Item
            item_strm = os.path.join(item_path, normalize_filename(item_title) + ".strm")

            if not os.path.exists(output_library):
                logging.debug(f"Creating library directory: {output_library}")
                os.mkdir(output_library)                
            if not os.path.exists(item_path):
                logging.debug(f"Creating item directory: {item_path}")
                os.mkdir(item_path)
            if not os.path.exists(item_strm):
                logging.info(f"Creating item STRM file: {item_strm}")
                f = open(item_strm, "w")
                f.write(video_url)
                f.close()                    


#build the video dictionary
video_dict = get_feed(rssurl)

#create dirs and write out strm files
write_strm_files(video_dict)

logging.info("Script completed successfully")

