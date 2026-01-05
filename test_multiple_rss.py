#!/usr/bin/env python3
import feedparser

def test_rss_feeds():
    feeds = [
        'http://feeds.bbci.co.uk/news/technology/rss.xml',
        'https://www.nasa.gov/rss/dyn/breaking_news.rss',
        'https://rss.cnn.com/rss/edition.rss',
        'https://feeds.feedburner.com/TechCrunch'
    ]
    
    for url in feeds:
        print(f'\nTesting: {url}')
        try:
            parsed = feedparser.parse(url)
            print(f'  Bozo flag: {getattr(parsed, "bozo", "unknown")}')
            print(f'  Version: {getattr(parsed, "version", "none")}')
            print(f'  Entries count: {len(getattr(parsed, "entries", []))}')
            
            if hasattr(parsed, 'bozo_exception') and parsed.bozo_exception:
                print(f'  Bozo exception: {parsed.bozo_exception}')
            
            if parsed.entries:
                print(f'  First entry: {parsed.entries[0].get("title", "No title")}')
            
            if parsed.version:
                print(f'  ✅ SUCCESS: Feed parsed correctly')
                return url  # Return first working feed
                
        except Exception as e:
            print(f'  Error: {e}')
    
    return None

if __name__ == "__main__":
    working_feed = test_rss_feeds()
    if working_feed:
        print(f'\n✅ Working feed found: {working_feed}')
    else:
        print('\n❌ No working feeds found - network issue confirmed')
