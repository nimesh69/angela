#!/usr/bin/env python3
"""
Improved Sanfoundry MCQ Scraper
Specifically designed for the Sanfoundry index page structure with tables
"""

import urllib.request
import urllib.parse
import html.parser
import csv
import re
import sys
import time
from typing import List, Dict

class ImprovedSanfoundryLinkExtractor(html.parser.HTMLParser):
    """Extract MCQ page links from Sanfoundry index pages - improved version"""
    
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.mcq_links = []
        self.in_content = False
        self.current_tag = None
        
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        attrs_dict = dict(attrs)
        
        # Look for content areas - be more inclusive
        if tag == 'div' and 'class' in attrs_dict:
            class_value = attrs_dict['class']
            if any(keyword in class_value for keyword in ['entry-content', 'content', 'post-content']):
                self.in_content = True
        
        # Also check for table structures
        elif tag in ['table', 'td', 'tr']:
            self.in_content = True
        
        # Extract links when in content areas
        elif tag == 'a' and self.in_content and 'href' in attrs_dict:
            href = attrs_dict['href']
            # Check if this looks like an MCQ page URL
            if self.is_mcq_link(href):
                full_url = urllib.parse.urljoin(self.base_url, href)
                if full_url not in self.mcq_links:
                    self.mcq_links.append(full_url)
    
    def handle_endtag(self, tag):
        if tag == 'div':
            self.in_content = False
        # Keep content flag for tables until table ends
        elif tag == 'table':
            self.in_content = False
    
    def is_mcq_link(self, href):
        """Check if URL looks like an MCQ page - improved detection"""
        mcq_indicators = [
            'questions-answers',
            'multiple-choice-questions',
            'mcq',
            '-questions-',
            'interview-questions',
            'data-structure',
            'sorting',
            'searching',
            'algorithm'
        ]
        
        # Must be from sanfoundry domain
        if 'sanfoundry.com' not in href:
            return False
        
        # Skip certain non-MCQ pages
        skip_patterns = [
            'wp-content',
            'category',
            'tag',
            'author',
            'feed',
            '.png',
            '.jpg',
            '.css',
            '.js'
        ]
        
        href_lower = href.lower()
        
        # Skip if contains skip patterns
        if any(pattern in href_lower for pattern in skip_patterns):
            return False
            
        # Should contain MCQ indicators
        return any(indicator in href_lower for indicator in mcq_indicators)
    
    def get_links(self):
        """Return extracted MCQ links"""
        return self.mcq_links


class ImprovedSanfoundryMCQParser(html.parser.HTMLParser):
    """Parse individual MCQ pages - improved version"""
    
    def __init__(self):
        super().__init__()
        self.mcqs = []
        self.full_text = ""
        self.in_content = False
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == 'div' and 'class' in attrs_dict:
            class_value = attrs_dict['class']
            if any(keyword in class_value for keyword in ['entry-content', 'content', 'post-content']):
                self.in_content = True
    
    def handle_endtag(self, tag):
        if tag == 'div' and self.in_content:
            self.in_content = False
    
    def handle_data(self, data):
        if self.in_content:
            self.full_text += data + "\n"
    
    def extract_mcqs(self):
        """Extract MCQs from the collected text - improved patterns"""
        if not self.full_text.strip():
            return []
        
        mcqs = []
        
        # Try multiple extraction methods
        mcqs.extend(self._extract_numbered_questions())
        
        # Try block-based extraction if numbered didn't work well
        if len(mcqs) < 5:  # If we got very few MCQs, try alternative methods
            mcqs.extend(self._extract_question_answer_blocks())
        
        return mcqs
    
    def _extract_numbered_questions(self):
        """Extract MCQs with numbered question format"""
        mcqs = []
        
        # Look for patterns like "1." or "Q1." or "Question 1"
        patterns = [
            r'\n\s*(\d+)\.\s*',  # Standard "1. "
            r'\n\s*Q\.?\s*(\d+)\s*[\.\:]\s*',  # "Q1." or "Q 1:"
            r'\n\s*Question\s+(\d+)\s*[\.\:]\s*'  # "Question 1:"
        ]
        
        for pattern in patterns:
            question_blocks = re.split(pattern, self.full_text, flags=re.IGNORECASE)
            
            if len(question_blocks) > 3:  # Found meaningful splits
                for i in range(1, len(question_blocks), 2):
                    if i + 1 < len(question_blocks):
                        question_num = question_blocks[i]
                        question_content = question_blocks[i + 1]
                        
                        mcq = self._parse_question_block(question_content, question_num)
                        if mcq and mcq['question'] and len(mcq['question']) > 10:
                            mcqs.append(mcq)
                
                if mcqs:  # If this pattern worked, use it
                    break
        
        return mcqs
    
    def _extract_question_answer_blocks(self):
        """Alternative extraction method looking for Q&A blocks"""
        mcqs = []
        
        # Look for patterns with explicit question markers
        question_patterns = [
            r'((?:Which|What|How|Where|When|Why|Who)[^?]*\?[^?]*?(?:a\)|A\))[^?]*?(?:Answer|Ans)[\s:]*[a-dA-D])',
            r'(\d+[^?]*\?[^?]*?(?:a\)|A\))[^?]*?(?:Answer|Ans)[\s:]*[a-dA-D])',
        ]
        
        for pattern in question_patterns:
            matches = re.finditer(pattern, self.full_text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                block = match.group(1)
                mcq = self._parse_question_block(block)
                if mcq and mcq['question'] and len(mcq['question']) > 10:
                    mcqs.append(mcq)
        
        return mcqs
    
    def _parse_question_block(self, block, question_num=None):
        """Parse a single question block - improved parsing"""
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
        
        # Extract question - look for text ending with ?
        question_patterns = [
            r'^[^?]*\?',  # Everything until first ?
            r'(\d+\.?\s*[^?]*\?)',  # Numbered question
            r'((?:Which|What|How|Where|When|Why|Who)[^?]*\?)',  # Question words
        ]
        
        for pattern in question_patterns:
            match = re.search(pattern, block, re.IGNORECASE)
            if match:
                question = match.group().strip()
                # Clean question number
                question = re.sub(r'^\d+\.?\s*', '', question)
                if len(question) > 10:  # Meaningful question
                    mcq['question'] = question
                    break
        
        # If no question found, try first substantial sentence
        if not mcq['question']:
            sentences = re.split(r'[.!?]', block)
            for sentence in sentences:
                clean_sentence = sentence.strip()
                if len(clean_sentence) > 15 and not re.match(r'^[a-d]\)', clean_sentence, re.IGNORECASE):
                    mcq['question'] = clean_sentence
                    break
        
        # Extract options with improved patterns
        option_patterns = [
            # Pattern 1: a) option text
            (r'[aA]\)\s*([^()]*?)(?=[bB]\)|Answer|Explanation|\n\s*[bB]\)|$)', 'option_a'),
            (r'[bB]\)\s*([^()]*?)(?=[cC]\)|Answer|Explanation|\n\s*[cC]\)|$)', 'option_b'),
            (r'[cC]\)\s*([^()]*?)(?=[dD]\)|Answer|Explanation|\n\s*[dD]\)|$)', 'option_c'),
            (r'[dD]\)\s*([^()]*?)(?=Answer|Explanation|View|$)', 'option_d'),
        ]
        
        for pattern, key in option_patterns:
            match = re.search(pattern, block, re.IGNORECASE | re.DOTALL)
            if match:
                option_text = match.group(1).strip()
                # Clean up option text
                option_text = re.sub(r'\s+', ' ', option_text)
                option_text = re.sub(r'\s*(View|Show)\s*$', '', option_text)  # Remove trailing "View"
                if option_text and len(option_text) > 1:
                    mcq[key] = option_text
        
        # Extract answer with multiple patterns
        answer_patterns = [
            r'(?:Answer|Ans|Correct)[\s:]*([a-dA-D])',
            r'(?:Solution)[\s:]*([a-dA-D])',
            r'\b([a-dA-D])\s+is\s+correct',
            r'correct\s+answer\s+is\s+([a-dA-D])',
        ]
        
        for pattern in answer_patterns:
            match = re.search(pattern, block, re.IGNORECASE)
            if match:
                mcq['correct_answer'] = match.group(1).upper()
                break
        
        # Extract explanation
        explanation_patterns = [
            r'(?:Explanation|Solution|Reason)[\s:]+([^.]*(?:\.[^.]*){0,2})',  # Explanation + up to 2 sentences
            r'(?:Because|Since)[\s:]+([^.]*)',
        ]
        
        for pattern in explanation_patterns:
            match = re.search(pattern, block, re.IGNORECASE)
            if match:
                explanation = match.group(1).strip()
                explanation = re.sub(r'\s+', ' ', explanation)
                if len(explanation) > 10:  # Meaningful explanation
                    mcq['explanation'] = explanation[:250]  # Limit length
                    break
        
        return mcq


def fetch_page(url):
    """Fetch a webpage"""
    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
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
    
    extractor = ImprovedSanfoundryLinkExtractor(index_url)
    extractor.feed(html_content)
    links = extractor.get_links()
    
    print(f"Found {len(links)} MCQ page links")
    
    # Print first few links for debugging
    if links:
        print("Sample links:")
        for i, link in enumerate(links[:5]):
            print(f"  {i+1}. {link}")
    
    return links


def scrape_mcq_page(url):
    """Scrape MCQs from a single page"""
    print(f"Scraping: {url}")
    
    html_content = fetch_page(url)
    if not html_content:
        return []
    
    parser = ImprovedSanfoundryMCQParser()
    parser.feed(html_content)
    mcqs = parser.extract_mcqs()
    
    print(f"  Found {len(mcqs)} MCQs")
    return mcqs


def save_mcqs_to_csv(mcqs, filename='mcqs.csv'):
    """Save MCQs to CSV file in the specified format"""
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
        print("Usage: python3 improved_sanfoundry_scraper.py <index_url> [output_file.csv] [max_pages]")
        print("Example: python3 improved_sanfoundry_scraper.py https://www.sanfoundry.com/1000-data-structures-algorithms-ii-questions-answers/ mcqs.csv 10")
        return
    
    index_url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'mcqs.csv'
    max_pages = int(sys.argv[3]) if len(sys.argv) > 3 else 20  # Increased default
    
    print("Improved Sanfoundry MCQ Scraper")
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
    successful_pages = 0
    
    for i, link in enumerate(mcq_links, 1):
        print(f"\n[{i}/{len(mcq_links)}] ", end="")
        mcqs = scrape_mcq_page(link)
        if mcqs:
            all_mcqs.extend(mcqs)
            successful_pages += 1
        
        # Be respectful - small delay between requests
        if i < len(mcq_links):
            time.sleep(1.5)
    
    # Step 3: Remove duplicates and save
    unique_mcqs = []
    seen_questions = set()
    
    for mcq in all_mcqs:
        question_key = mcq['question'][:50].lower() if mcq['question'] else ''
        if question_key and question_key not in seen_questions:
            seen_questions.add(question_key)
            unique_mcqs.append(mcq)
    
    print(f"\n" + "=" * 50)
    print(f"Pages scraped successfully: {successful_pages}/{len(mcq_links)}")
    print(f"Total MCQs scraped: {len(all_mcqs)}")
    print(f"Unique MCQs: {len(unique_mcqs)}")
    
    if unique_mcqs:
        # Quality metrics
        complete_mcqs = sum(1 for mcq in unique_mcqs if all([
            mcq['question'], mcq['option_a'], mcq['option_b'], mcq['option_c'], mcq['option_d']
        ]))
        print(f"Complete MCQs (all fields): {complete_mcqs}")
        
        partial_mcqs = sum(1 for mcq in unique_mcqs if all([
            mcq['question'], mcq['option_a'], mcq['option_b']
        ]))
        print(f"Partial MCQs (Q + 2+ options): {partial_mcqs}")
        
        with_answers = sum(1 for mcq in unique_mcqs if mcq['correct_answer'])
        print(f"MCQs with answers: {with_answers}")
        
        with_explanations = sum(1 for mcq in unique_mcqs if mcq['explanation'])
        print(f"MCQs with explanations: {with_explanations}")
        
        # Save to CSV
        save_mcqs_to_csv(unique_mcqs, output_file)
        
        # Show sample
        if unique_mcqs and unique_mcqs[0]['question']:
            print(f"\nSample MCQ:")
            sample = unique_mcqs[0]
            print(f"Q: {sample['question']}")
            if sample['option_a']: print(f"A) {sample['option_a']}")
            if sample['option_b']: print(f"B) {sample['option_b']}")
            if sample['option_c']: print(f"C) {sample['option_c']}")
            if sample['option_d']: print(f"D) {sample['option_d']}")
            if sample['correct_answer']: print(f"Answer: {sample['correct_answer']}")
            if sample['explanation']: print(f"Explanation: {sample['explanation'][:100]}...")
        
        print(f"\n✓ Scraping completed! Check {output_file}")
    else:
        print("\n✗ No MCQs extracted successfully")
        print("Possible issues:")
        print("1. The website structure has changed")
        print("2. The pages don't contain MCQs in expected format") 
        print("3. Network/access restrictions")


if __name__ == "__main__":
    main()