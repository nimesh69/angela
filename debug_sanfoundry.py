#!/usr/bin/env python3
"""
Debug script to examine Sanfoundry website structure
"""

import urllib.request
import re

def debug_sanfoundry_structure(url):
    """Debug the structure of Sanfoundry website"""
    
    # Fetch webpage
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            html_content = response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error fetching webpage: {e}")
        return
    
    print(f"Page length: {len(html_content)} characters")
    print("=" * 50)
    
    # Look for patterns that might indicate MCQs
    patterns = [
        r'\d+\.\s*[A-Z].*?\?',  # Numbered questions ending with ?
        r'\d+\)\s*[A-Z].*?\?',  # Numbered questions with ) ending with ?
        r'[A-D]\)\s*\w+',       # Options like A) something
        r'[a-d]\)\s*\w+',       # Options like a) something  
        r'Question\s*\d+',      # Question headers
        r'Answer[\s:]*[A-D]',   # Answer patterns
        r'Explanation',         # Explanations
    ]
    
    for i, pattern in enumerate(patterns, 1):
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        print(f"Pattern {i} ({pattern}): {len(matches)} matches")
        if matches:
            print("  Sample matches:")
            for match in matches[:3]:  # Show first 3 matches
                print(f"    {match[:100]}...")
        print()
    
    # Look for specific Sanfoundry patterns
    print("Looking for Sanfoundry-specific patterns:")
    print("-" * 40)
    
    # Check for common container classes
    container_patterns = [
        r'<div[^>]*class="[^"]*entry[^"]*"[^>]*>',
        r'<div[^>]*class="[^"]*content[^"]*"[^>]*>',
        r'<div[^>]*class="[^"]*question[^"]*"[^>]*>',
        r'<div[^>]*class="[^"]*post[^"]*"[^>]*>',
        r'<article[^>]*>',
        r'<section[^>]*>',
    ]
    
    for pattern in container_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        print(f"{pattern}: {len(matches)} matches")
    
    print("\n" + "=" * 50)
    
    # Show a sample of the HTML structure
    print("HTML Sample (first 2000 chars):")
    print("-" * 30)
    print(html_content[:2000])
    
    print("\n" + "=" * 50)
    print("HTML Sample (middle section):")
    print("-" * 30)
    mid_point = len(html_content) // 2
    print(html_content[mid_point:mid_point+2000])
    
    # Try to find the main content area
    content_patterns = [
        r'<div[^>]*class="[^"]*entry-content[^"]*"[^>]*>(.*?)</div>',
        r'<div[^>]*class="[^"]*post-content[^"]*"[^>]*>(.*?)</div>',
        r'<article[^>]*>(.*?)</article>',
        r'<main[^>]*>(.*?)</main>',
    ]
    
    print("\n" + "=" * 50)
    print("Content Analysis:")
    print("-" * 30)
    
    for pattern in content_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
        print(f"Pattern {pattern[:50]}...: {len(matches)} matches")
        if matches:
            # Show snippet of first match
            content = matches[0][:500]
            print(f"  Content snippet: {content}...")
            print()


if __name__ == "__main__":
    url = "https://www.sanfoundry.com/1000-data-structures-algorithms-ii-questions-answers/"
    debug_sanfoundry_structure(url)