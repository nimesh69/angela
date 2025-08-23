#!/usr/bin/env python3
"""
Comprehensive Sanfoundry MCQ Scraper
1. Extracts links to individual MCQ pages from the main index
2. Scrapes MCQs from each individual page
3. Saves all MCQs to CSV format
"""

import urllib.request
import urllib.parse
import html.parser
import csv
import re
import sys
import time
from typing import List, Dict

class SanfoundryLinkExtractor(html.parser.HTMLParser):
    """Extract MCQ page links from Sanfoundry index pages"""
    
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.mcq_links = []
        self.in_entry_content = False
        self.current_tag = None
        
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        attrs_dict = dict(attrs)
        
        # Look for entry-content div
        if tag == 'div' and 'class' in attrs_dict:
            if 'entry-content' in attrs_dict['class']:
                self.in_entry_content = True
        
        # Extract links when in entry-content
        elif tag == 'a' and self.in_entry_content and 'href' in attrs_dict:
            href = attrs_dict['href']
            # Check if this looks like an MCQ page URL
            if self.is_mcq_link(href):
                full_url = urllib.parse.urljoin(self.base_url, href)
                if full_url not in self.mcq_links:
                    self.mcq_links.append(full_url)
    
    def handle_endtag(self, tag):
        if tag == 'div' and self.in_entry_content:
            self.in_entry_content = False
    
    def is_mcq_link(self, href):
        """Check if URL looks like an MCQ page"""
        mcq_indicators = [
            'questions-answers',
            'multiple-choice-questions',
            'mcq',
            '-questions-',
            'interview-questions'
        ]
        
        # Must be from sanfoundry domain
        if 'sanfoundry.com' not in href:
            return False
            
        # Should contain MCQ indicators
        href_lower = href.lower()
        return any(indicator in href_lower for indicator in mcq_indicators)
    
    def get_links(self):
        """Return extracted MCQ links"""
        return self.mcq_links


class SanfoundryMCQParser(html.parser.HTMLParser):
    """Parse individual MCQ pages"""
    
    def __init__(self):
        super().__init__()
        self.mcqs = []
        self.full_text = ""
        self.in_entry_content = False
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == 'div' and 'class' in attrs_dict:
            if 'entry-content' in attrs_dict['class']:
                self.in_entry_content = True
    
    def handle_endtag(self, tag):
        if tag == 'div' and self.in_entry_content:
            self.in_entry_content = False
    
    def handle_data(self, data):
        if self.in_entry_content:
            self.full_text += data + "\n"
    
    def extract_mcqs(self):
        """Extract MCQs from the collected text"""
        if not self.full_text.strip():
            return []
        
        # Try different extraction methods
        mcqs = []
        
        # Method 1: Look for numbered questions with options
        mcqs.extend(self._extract_numbered_questions())
        
        # Method 2: Look for explicit question patterns
        if not mcqs:
            mcqs.extend(self._extract_question_patterns())
        
        return mcqs
    
    def _extract_numbered_questions(self):
        """Extract MCQs with numbered question format"""
        mcqs = []
        
        # Split by question numbers (1., 2., etc.)
        question_blocks = re.split(r'\n\s*(\d+)\.\s*', self.full_text)
        
        for i in range(1, len(question_blocks), 2):  # Every other element after split
            if i + 1 < len(question_blocks):
                question_num = question_blocks[i]
                question_content = question_blocks[i + 1]
                
                mcq = self._parse_question_block(question_content, question_num)
                if mcq and mcq['question']:
                    mcqs.append(mcq)
        
        return mcqs
    
    def _extract_question_patterns(self):
        """Extract using question patterns"""
        mcqs = []
        
        # Look for question indicators
        question_patterns = [
            r'(Which[^?]*\?)',
            r'(What[^?]*\?)', 
            r'(How[^?]*\?)',
            r'(Where[^?]*\?)',
            r'(When[^?]*\?)',
            r'(Why[^?]*\?)'
        ]
        
        for pattern in question_patterns:
            matches = re.finditer(pattern, self.full_text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                # Get context around the question
                start = max(0, match.start() - 100)
                end = min(len(self.full_text), match.end() + 500)
                context = self.full_text[start:end]
                
                mcq = self._parse_question_block(context)
                if mcq and mcq['question']:
                    mcqs.append(mcq)
        
        return mcqs
    
    def _parse_question_block(self, block, question_num=None):
        """Parse a single question block"""
        mcq = {
            'question': '',
            'option_a': '',
            'option_b': '',
            'option_c': '',
            'option_d': '',
            'correct_answer': '',
            'explanation': ''
        }
        
        # Clean the block
        block = re.sub(r'\s+', ' ', block.strip())
        
        # Extract question
        # Look for question ending with ?
        question_match = re.search(r'(.+?\?)', block)
        if question_match:
            question = question_match.group(1).strip()
            # Remove question number if present
            question = re.sub(r'^\d+\.\s*', '', question)
            mcq['question'] = question
        else:
            # If no question mark, take first substantial sentence
            sentences = re.split(r'[.!]', block)
            for sentence in sentences:
                if len(sentence.strip()) > 20:
                    mcq['question'] = sentence.strip()
                    break
        
        # Extract options (a), b), c), d) or A), B), C), D)
        option_patterns = [
            (r'[aA]\)\s*([^()]*?)(?=[bB]\)|\n|$)', 'option_a'),
            (r'[bB]\)\s*([^()]*?)(?=[cC]\)|\n|$)', 'option_b'),
            (r'[cC]\)\s*([^()]*?)(?=[dD]\)|\n|$)', 'option_c'),
            (r'[dD]\)\s*([^()]*?)(?=\n|Answer|Explanation|$)', 'option_d')
        ]
        
        for pattern, key in option_patterns:
            match = re.search(pattern, block, re.IGNORECASE)
            if match:
                option_text = match.group(1).strip()
                # Clean up option text
                option_text = re.sub(r'\s+', ' ', option_text)
                mcq[key] = option_text
        
        # Extract answer
        answer_patterns = [
            r'Answer[\s:]*([a-dA-D])',
            r'Correct[\s:]*([a-dA-D])',
            r'Solution[\s:]*([a-dA-D])',
            r'\bAns[\s:]*([a-dA-D])',
        ]
        
        for pattern in answer_patterns:
            match = re.search(pattern, block, re.IGNORECASE)
            if match:
                mcq['correct_answer'] = match.group(1).upper()
                break
        
        # Extract explanation
        explanation_patterns = [
            r'Explanation[\s:]+(.+?)(?=\n\d+\.|$)',
            r'Solution[\s:]+(.+?)(?=\n\d+\.|$)',
            r'Reason[\s:]+(.+?)(?=\n\d+\.|$)'
        ]
        
        for pattern in explanation_patterns:
            match = re.search(pattern, block, re.IGNORECASE | re.DOTALL)
            if match:
                explanation = match.group(1).strip()
                explanation = re.sub(r'\s+', ' ', explanation)
                mcq['explanation'] = explanation[:300]  # Limit length
                break
        
        return mcq


def fetch_page(url):
    """Fetch a webpage"""
    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode('utf-8', errors='ignore')
            
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def extract_mcq_links(index_url):
    """Extract MCQ page links from index page"""
    print(f"Extracting MCQ links from: {index_url}")
    
    html_content = fetch_page(index_url)
    if not html_content:
        return []
    
    extractor = SanfoundryLinkExtractor(index_url)
    extractor.feed(html_content)
    links = extractor.get_links()
    
    print(f"Found {len(links)} MCQ page links")
    return links


def scrape_mcq_page(url):
    """Scrape MCQs from a single page"""
    print(f"Scraping: {url}")
    
    html_content = fetch_page(url)
    if not html_content:
        return []
    
    parser = SanfoundryMCQParser()
    parser.feed(html_content)
    mcqs = parser.extract_mcqs()
    
    print(f"  Found {len(mcqs)} MCQs")
    return mcqs


def save_mcqs_to_csv(mcqs, filename='mcqs.csv'):
    """Save MCQs to CSV file"""
    if not mcqs:
        print("No MCQs to save")
        return False
    
    fieldnames = ['question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'explanation']
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for mcq in mcqs:
                # Ensure correct answer is uppercase
                if mcq['correct_answer']:
                    mcq['correct_answer'] = mcq['correct_answer'].upper()
                writer.writerow(mcq)
        
        print(f"✓ Successfully saved {len(mcqs)} MCQs to {filename}")
        return True
        
    except Exception as e:
        print(f"Error saving to CSV: {e}")
        return False


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python3 sanfoundry_full_scraper.py <index_url> [output_file.csv] [max_pages]")
        print("Example: python3 sanfoundry_full_scraper.py https://www.sanfoundry.com/1000-data-structures-algorithms-ii-questions-answers/ mcqs.csv 5")
        return
    
    index_url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'mcqs.csv'
    max_pages = int(sys.argv[3]) if len(sys.argv) > 3 else 10  # Limit to prevent too many requests
    
    print("Comprehensive Sanfoundry MCQ Scraper")
    print("=" * 50)
    
    # Step 1: Extract MCQ page links
    mcq_links = extract_mcq_links(index_url)
    
    if not mcq_links:
        print("No MCQ page links found!")
        return
    
    # Limit number of pages to scrape
    if len(mcq_links) > max_pages:
        print(f"Limiting to first {max_pages} pages (use 3rd argument to change)")
        mcq_links = mcq_links[:max_pages]
    
    # Step 2: Scrape MCQs from each page
    all_mcqs = []
    
    for i, link in enumerate(mcq_links, 1):
        print(f"\n[{i}/{len(mcq_links)}] ", end="")
        mcqs = scrape_mcq_page(link)
        all_mcqs.extend(mcqs)
        
        # Be respectful - small delay between requests
        if i < len(mcq_links):
            time.sleep(2)
    
    # Step 3: Remove duplicates and save
    unique_mcqs = []
    seen_questions = set()
    
    for mcq in all_mcqs:
        question_key = mcq['question'][:50].lower() if mcq['question'] else ''
        if question_key and question_key not in seen_questions:
            seen_questions.add(question_key)
            unique_mcqs.append(mcq)
    
    print(f"\n" + "=" * 50)
    print(f"Total MCQs scraped: {len(all_mcqs)}")
    print(f"Unique MCQs: {len(unique_mcqs)}")
    
    if unique_mcqs:
        complete_mcqs = sum(1 for mcq in unique_mcqs if all([
            mcq['question'], mcq['option_a'], mcq['option_b']
        ]))
        print(f"Complete MCQs (with at least Q + 2 options): {complete_mcqs}")
        
        with_answers = sum(1 for mcq in unique_mcqs if mcq['correct_answer'])
        print(f"MCQs with answers: {with_answers}")
        
        save_mcqs_to_csv(unique_mcqs, output_file)
        
        # Show sample
        if unique_mcqs and unique_mcqs[0]['question']:
            print(f"\nSample MCQ:")
            sample = unique_mcqs[0]
            print(f"Q: {sample['question']}")
            print(f"A) {sample['option_a']}")
            print(f"B) {sample['option_b']}")
            print(f"C) {sample['option_c']}")
            print(f"D) {sample['option_d']}")
            print(f"Answer: {sample['correct_answer']}")
            if sample['explanation']:
                print(f"Explanation: {sample['explanation'][:100]}...")
        
        print(f"\n✓ Scraping completed! Check {output_file}")
    else:
        print("\n✗ No MCQs extracted successfully")


if __name__ == "__main__":
    main()