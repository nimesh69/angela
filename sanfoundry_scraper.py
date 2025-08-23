#!/usr/bin/env python3
"""
Sanfoundry MCQ Scraper
Scrapes MCQs from Sanfoundry Data Structures & Algorithms pages
Uses only built-in Python modules (no external dependencies)
"""

import urllib.request
import urllib.parse
import html.parser
import csv
import re
import json
import sys
from typing import List, Dict

class SanfoundryParser(html.parser.HTMLParser):
    """Custom HTML parser for Sanfoundry MCQ pages"""
    
    def __init__(self):
        super().__init__()
        self.mcqs = []
        self.current_mcq = {}
        self.current_tag = None
        self.current_attrs = {}
        self.capture_text = False
        self.text_buffer = ""
        self.in_question = False
        self.in_options = False
        self.in_answer = False
        self.in_explanation = False
        self.option_counter = 0
        self.question_number = 0
        
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        self.current_attrs = dict(attrs)
        
        # Look for question containers
        if tag == 'p' and any('question' in str(v).lower() for v in attrs):
            self.in_question = True
            self.capture_text = True
            
        # Look for numbered questions (common pattern: strong tag with number)
        elif tag == 'strong':
            self.capture_text = True
            
        # Look for option lists
        elif tag == 'ol' or tag == 'ul':
            self.in_options = True
            self.option_counter = 0
            
        elif tag == 'li' and self.in_options:
            self.capture_text = True
            
        # Look for answer sections
        elif tag == 'p' and any('answer' in str(v).lower() for v in attrs):
            self.in_answer = True
            self.capture_text = True
            
        # Look for explanation sections  
        elif tag == 'div' and any('explanation' in str(v).lower() for v in attrs):
            self.in_explanation = True
            self.capture_text = True
    
    def handle_endtag(self, tag):
        if self.capture_text and self.text_buffer.strip():
            text = self.clean_text(self.text_buffer)
            
            if self.in_question and tag in ['p', 'strong']:
                # Check if this looks like a question
                if self.is_question_text(text):
                    if self.current_mcq and any(self.current_mcq.values()):
                        self.mcqs.append(self.current_mcq)
                    
                    self.current_mcq = {
                        'question': text,
                        'option_a': '',
                        'option_b': '',
                        'option_c': '',
                        'option_d': '',
                        'correct_answer': '',
                        'explanation': ''
                    }
                    self.question_number += 1
                
            elif self.in_options and tag == 'li':
                # Assign to option slots
                option_keys = ['option_a', 'option_b', 'option_c', 'option_d']
                if self.option_counter < len(option_keys):
                    # Clean option text (remove a), b), etc.)
                    clean_option = re.sub(r'^[a-d]\)\s*', '', text, flags=re.IGNORECASE)
                    self.current_mcq[option_keys[self.option_counter]] = clean_option
                    self.option_counter += 1
                    
            elif self.in_answer and tag == 'p':
                # Extract answer letter
                answer_match = re.search(r'[a-d]', text.lower())
                if answer_match:
                    self.current_mcq['correct_answer'] = answer_match.group().upper()
                    
            elif self.in_explanation and tag == 'div':
                self.current_mcq['explanation'] = text
        
        # Reset states
        if tag == 'p':
            self.in_question = False
            self.in_answer = False
        elif tag in ['ol', 'ul']:
            self.in_options = False
        elif tag == 'div':
            self.in_explanation = False
            
        self.capture_text = False
        self.text_buffer = ""
    
    def handle_data(self, data):
        if self.capture_text:
            self.text_buffer += data
    
    def clean_text(self, text):
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove HTML entities
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
        text = text.replace('&lt;', '<').replace('&gt;', '>')
        return text
    
    def is_question_text(self, text):
        """Check if text looks like a question"""
        # Remove question numbers
        clean_text = re.sub(r'^\d+\.\s*', '', text)
        
        # Should be substantial text
        if len(clean_text) < 10:
            return False
            
        # Should end with question mark or be substantial statement
        if clean_text.endswith('?') or len(clean_text) > 20:
            return True
            
        # Check for question keywords
        question_keywords = ['what', 'which', 'how', 'where', 'when', 'why', 'who']
        return any(keyword in clean_text.lower() for keyword in question_keywords)
    
    def get_mcqs(self):
        """Return list of extracted MCQs"""
        # Add last MCQ if exists
        if self.current_mcq and any(self.current_mcq.values()):
            self.mcqs.append(self.current_mcq)
        return self.mcqs


class SanfoundryGenericParser(html.parser.HTMLParser):
    """Generic parser that works with various Sanfoundry page layouts"""
    
    def __init__(self):
        super().__init__()
        self.mcqs = []
        self.full_text = ""
        
    def handle_data(self, data):
        self.full_text += data + " "
    
    def extract_mcqs_from_text(self):
        """Extract MCQs using text patterns"""
        # Split text into potential question blocks
        # Look for numbered questions
        question_blocks = re.split(r'\n\s*\d+\.\s*', self.full_text)
        
        for i, block in enumerate(question_blocks[1:], 1):  # Skip first empty split
            mcq = self.parse_question_block(f"{i}. {block}")
            if mcq and mcq['question']:
                self.mcqs.append(mcq)
        
        return self.mcqs
    
    def parse_question_block(self, block):
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
        
        # Extract question (everything before first option)
        question_match = re.search(r'^\d+\.\s*(.+?)(?=\n?[a-d]\))', block, re.DOTALL | re.IGNORECASE)
        if question_match:
            mcq['question'] = self.clean_text(question_match.group(1))
        
        # Extract options
        option_patterns = [
            (r'[a]\)\s*([^\n]+)', 'option_a'),
            (r'[b]\)\s*([^\n]+)', 'option_b'), 
            (r'[c]\)\s*([^\n]+)', 'option_c'),
            (r'[d]\)\s*([^\n]+)', 'option_d')
        ]
        
        for pattern, key in option_patterns:
            match = re.search(pattern, block, re.IGNORECASE)
            if match:
                mcq[key] = self.clean_text(match.group(1))
        
        # Extract answer
        answer_patterns = [
            r'answer[\s:]*[a-d]',
            r'correct[\s:]*[a-d]',
            r'solution[\s:]*[a-d]'
        ]
        
        for pattern in answer_patterns:
            match = re.search(pattern, block, re.IGNORECASE)
            if match:
                letter = re.search(r'[a-d]', match.group(), re.IGNORECASE)
                if letter:
                    mcq['correct_answer'] = letter.group().upper()
                break
        
        # Extract explanation
        explanation_match = re.search(r'explanation[\s:]+(.+)', block, re.IGNORECASE | re.DOTALL)
        if explanation_match:
            mcq['explanation'] = self.clean_text(explanation_match.group(1)[:200])  # Limit length
        
        return mcq
    
    def clean_text(self, text):
        """Clean and normalize text"""
        text = re.sub(r'\s+', ' ', text.strip())
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
        return text


def fetch_webpage(url):
    """Fetch webpage content using urllib"""
    try:
        print(f"Fetching: {url}")
        
        # Create request with headers
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            html_content = response.read().decode('utf-8', errors='ignore')
            return html_content
            
    except Exception as e:
        print(f"Error fetching webpage: {e}")
        return None


def save_mcqs_to_csv(mcqs, filename='mcqs.csv'):
    """Save MCQs to CSV file in the specified format"""
    if not mcqs:
        print("No MCQs to save")
        return
    
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


def print_mcq_summary(mcqs):
    """Print summary of scraped MCQs"""
    print(f"\nScraping Summary:")
    print(f"Total MCQs found: {len(mcqs)}")
    
    if mcqs:
        complete_mcqs = sum(1 for mcq in mcqs if all([
            mcq['question'], mcq['option_a'], mcq['option_b'], 
            mcq['option_c'], mcq['option_d']
        ]))
        print(f"Complete MCQs (all options): {complete_mcqs}")
        
        with_answers = sum(1 for mcq in mcqs if mcq['correct_answer'])
        print(f"MCQs with answers: {with_answers}")
        
        with_explanations = sum(1 for mcq in mcqs if mcq['explanation'])
        print(f"MCQs with explanations: {with_explanations}")
        
        # Show sample
        if mcqs and mcqs[0]['question']:
            print(f"\nSample MCQ:")
            sample = mcqs[0]
            print(f"Q: {sample['question'][:100]}...")
            print(f"A) {sample['option_a'][:50]}...")
            print(f"B) {sample['option_b'][:50]}...")
            print(f"Answer: {sample['correct_answer']}")


def scrape_sanfoundry_mcqs(url, output_file='mcqs.csv'):
    """Main function to scrape Sanfoundry MCQs"""
    
    # Fetch webpage
    html_content = fetch_webpage(url)
    if not html_content:
        return []
    
    # Try different parsing approaches
    parsers = [SanfoundryParser(), SanfoundryGenericParser()]
    all_mcqs = []
    
    for parser in parsers:
        try:
            parser.feed(html_content)
            if hasattr(parser, 'extract_mcqs_from_text'):
                mcqs = parser.extract_mcqs_from_text()
            else:
                mcqs = parser.get_mcqs()
            
            print(f"Parser {parser.__class__.__name__} found {len(mcqs)} MCQs")
            all_mcqs.extend(mcqs)
            
        except Exception as e:
            print(f"Parser {parser.__class__.__name__} failed: {e}")
            continue
    
    # Remove duplicates
    unique_mcqs = []
    seen_questions = set()
    
    for mcq in all_mcqs:
        question_key = mcq['question'][:50].lower()
        if question_key not in seen_questions and mcq['question']:
            seen_questions.add(question_key)
            unique_mcqs.append(mcq)
    
    print_mcq_summary(unique_mcqs)
    
    if unique_mcqs:
        save_mcqs_to_csv(unique_mcqs, output_file)
    else:
        print("No MCQs extracted. The page structure may not be supported.")
    
    return unique_mcqs


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python3 sanfoundry_scraper.py <url> [output_file.csv]")
        print("Example: python3 sanfoundry_scraper.py https://www.sanfoundry.com/1000-data-structures-algorithms-ii-questions-answers/")
        return
    
    url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'mcqs.csv'
    
    print("Sanfoundry MCQ Scraper")
    print("=" * 50)
    
    mcqs = scrape_sanfoundry_mcqs(url, output_file)
    
    if mcqs:
        print(f"\n✓ Scraping completed successfully!")
        print(f"Check {output_file} for the results.")
    else:
        print(f"\n✗ No MCQs were extracted.")
        print("This could mean:")
        print("1. The page doesn't contain MCQs in expected format")
        print("2. The page structure has changed")
        print("3. Network/access issues")


if __name__ == "__main__":
    main()