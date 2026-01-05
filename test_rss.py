#!/usr/bin/env python3
import feedparser

def test_rss_feed():
    url = 'https://checkin.libsyn.com/rss'
    print(f'Testing RSS feed: {url}')
    
    try:
        parsed = feedparser.parse(url)
        print(f'Bozo flag: {getattr(parsed, "bozo", "unknown")}')
        print(f'Version: {getattr(parsed, "version", "none")}')
        print(f'Entries count: {len(getattr(parsed, "entries", []))}')
        print(f'Feed title: {getattr(parsed.feed, "title", "No title")}')
        
        if hasattr(parsed, 'bozo_exception') and parsed.bozo_exception:
            print(f'Bozo exception: {parsed.bozo_exception}')
        
        if parsed.entries:
            print(f'First entry title: {parsed.entries[0].get("title", "No title")}')
            print(f'First entry summary: {parsed.entries[0].get("summary", "No summary")[:100]}...')
        
        return parsed
    except Exception as e:
        print(f'Error: {e}')
        return None

if __name__ == "__main__":
    test_rss_feed()
