#!/usr/bin/env python3
"""
Web scraper for heritage site information from websites.
This module downloads content from web pages and saves it as text files
in the transcripts directory.
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
import re
import time
import json
import argparse
from pathlib import Path
from urllib.parse import urlparse
import random
from typing import Optional, Dict, List, Tuple

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import configuration
from backend.config import TRANSCRIPTS_DIR

# Path to the transcript tracking file
TRANSCRIPT_TRACKING_FILE = os.path.join(TRANSCRIPTS_DIR, '.processed_transcripts.json')

class WebScraper:
    """Scraper for heritage site information from websites"""
    
    def __init__(self, output_dir: str = TRANSCRIPTS_DIR):
        """Initialize the web scraper with output directory"""
        self.output_dir = output_dir
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        # Create the output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
    def _generate_filename(self, url: str, title: str = None) -> str:
        """
        Generate a filename for the scraped content
        
        Args:
            url: URL of the scraped page
            title: Page title (optional)
            
        Returns:
            A filename for the scraped content
        """
        if title:
            # Clean title to create a safe filename
            safe_title = re.sub(r'[^\w\s-]', '', title.lower())
            safe_title = re.sub(r'[\s]+', '_', safe_title)
            # Truncate if too long
            if len(safe_title) > 50:
                safe_title = safe_title[:50]
            if not safe_title:
                # Fallback if title is empty after cleaning
                safe_title = f"web_content_{int(time.time())}"
        else:
            # Use the domain and path as filename
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.replace("www.", "")
            path = parsed_url.path.strip("/").replace("/", "_")
            if not path:
                safe_title = f"{domain}_{int(time.time())}"
            else:
                safe_title = f"{domain}_{path}"
                if len(safe_title) > 50:
                    safe_title = safe_title[:50]
        
        filename = f"{safe_title}.txt"
        # Avoid overwriting existing files
        counter = 1
        base_name = safe_title
        while os.path.exists(os.path.join(self.output_dir, filename)):
            safe_title = f"{base_name}_{counter}"
            filename = f"{safe_title}.txt"
            counter += 1
            
        return filename
    
    def _extract_content(self, soup: BeautifulSoup, url: str) -> Tuple[str, str]:
        """
        Extract title and main content from a BeautifulSoup object
        
        Args:
            soup: BeautifulSoup object of the webpage
            url: URL of the scraped page
            
        Returns:
            Tuple of (title, content)
        """
        # Extract title
        title = "Untitled"
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            title = title_tag.string.strip()
            
        # Extract main content based on common patterns
        content = ""
        
        # First try to find article or main content divs
        main_content = None
        for selector in ['article', 'main', '.main-content', '.article-content', '.post-content', 
                         '#content', '.content', '[role="main"]', '.entry-content', '.page-content']:
            elements = soup.select(selector)
            if elements:
                main_content = elements[0]
                break
        
        if main_content:
            # Extract text from main content
            paragraphs = main_content.find_all('p')
            if paragraphs:
                content = "\n\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            
            # If we didn't get enough content from paragraphs, extract all text
            if len(content) < 100:
                content = main_content.get_text(separator="\n\n", strip=True)
        else:
            # Fallback: extract all paragraph text
            paragraphs = soup.find_all('p')
            if paragraphs:
                content = "\n\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            
        # Add metadata at the top of the content
        metadata = f"Title: {title}\nSource URL: {url}\nDate Retrieved: {time.strftime('%Y-%m-%d')}\n\n"
        content = metadata + content
        
        return title, content
    
    def scrape_url(self, url: str) -> Optional[str]:
        """
        Scrape content from a URL and save it to a file
        
        Args:
            url: URL to scrape
            
        Returns:
            Path to the saved file, or None if scraping failed
        """
        try:
            print(f"Scraping {url}...")
            
            # Make request with appropriate headers
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title and content
            title, content = self._extract_content(soup, url)
            
            # Generate filename
            filename = self._generate_filename(url, title)
            filepath = os.path.join(self.output_dir, filename)
            
            # Save content to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
            print(f"Saved content to {filepath}")
            return filepath
            
        except requests.RequestException as e:
            print(f"Error scraping {url}: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error scraping {url}: {str(e)}")
            return None
    
    def scrape_multiple_urls(self, urls: List[str], delay: int = 2) -> Dict[str, str]:
        """
        Scrape multiple URLs with a delay between requests
        
        Args:
            urls: List of URLs to scrape
            delay: Delay in seconds between requests (to avoid rate limiting)
            
        Returns:
            Dictionary mapping URLs to saved file paths
        """
        results = {}
        
        for i, url in enumerate(urls, 1):
            print(f"Processing URL {i}/{len(urls)}")
            filepath = self.scrape_url(url)
            results[url] = filepath
            
            # Add delay before next request (except for last URL)
            if i < len(urls):
                # Add some randomization to the delay to appear more human-like
                actual_delay = delay + random.uniform(0.5, 1.5)
                print(f"Waiting {actual_delay:.1f} seconds before next request...")
                time.sleep(actual_delay)
        
        # Print summary
        successful = sum(1 for path in results.values() if path)
        print(f"\nScraping complete: {successful}/{len(urls)} URLs scraped successfully")
        
        return results

def load_processed_transcripts() -> Dict[str, bool]:
    """Load the list of processed transcript files"""
    if not os.path.exists(TRANSCRIPT_TRACKING_FILE):
        return {}
    
    try:
        with open(TRANSCRIPT_TRACKING_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_tracking_file(tracking_data: Dict[str, bool]) -> None:
    """Save the tracking data to file"""
    with open(TRANSCRIPT_TRACKING_FILE, 'w') as f:
        json.dump(tracking_data, f, indent=2)

def main():
    """Main function to run web scraper from command line"""
    parser = argparse.ArgumentParser(description="Scrape heritage site content from websites")
    parser.add_argument('--url', type=str, help="URL to scrape")
    parser.add_argument('--urls', type=str, help="Path to text file containing URLs (one per line)")
    parser.add_argument('--output-dir', type=str, default=TRANSCRIPTS_DIR, 
                        help="Directory to save scraped content")
    parser.add_argument('--delay', type=int, default=2,
                        help="Delay in seconds between requests for multiple URLs")
    
    args = parser.parse_args()
    scraper = WebScraper(args.output_dir)
    
    if args.url:
        # Scrape a single URL
        filepath = scraper.scrape_url(args.url)
        if filepath:
            print(f"Content saved to {filepath}")
            
            # Update tracking file with the new transcript
            if os.path.exists(filepath):
                tracking_data = load_processed_transcripts()
                filename = os.path.basename(filepath)
                tracking_data[filename] = False  # Mark as downloaded but not processed
                save_tracking_file(tracking_data)
                print(f"Added {filename} to tracking file")
                
            sys.exit(0)
        else:
            print("Failed to scrape URL")
            sys.exit(1)
    
    elif args.urls:
        # Scrape multiple URLs from file
        try:
            with open(args.urls, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                
            if not urls:
                print(f"No valid URLs found in {args.urls}")
                sys.exit(1)
                
            print(f"Found {len(urls)} URLs to scrape")
            results = scraper.scrape_multiple_urls(urls, args.delay)
            
            # Update tracking file with new transcripts
            tracking_data = load_processed_transcripts()
            for url, filepath in results.items():
                if filepath and os.path.exists(filepath):
                    filename = os.path.basename(filepath)
                    tracking_data[filename] = False  # Mark as downloaded but not processed
            
            save_tracking_file(tracking_data)
            print(f"Updated tracking file with new transcripts")
            
            sys.exit(0)
        except Exception as e:
            print(f"Error reading URLs file: {str(e)}")
            sys.exit(1)
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()