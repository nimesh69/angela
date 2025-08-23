#!/usr/bin/env python3
"""
MCQ Web Scraper
Scrapes Multiple Choice Questions from websites and saves them to CSV format.
CSV Format: question,option_a,option_b,option_c,option_d,correct_answer(in capital),explanation
"""

import requests
from bs4 import BeautifulSoup
import csv
import re
import sys
from urllib.parse import urljoin, urlparse
import time
import json
from typing import List, Dict, Optional

class MCQScraper:
    def __init__(self, base_url: str, delay: float = 1.0):
        """
        Initialize the MCQ scraper
        
        Args:
            base_url: The base URL of the website to scrape
            delay: Delay between requests to be respectful to the server
        """
        self.base_url = base_url
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.mcqs = []
    
    def get_page(self, url: str) -> BeautifulSoup:
        """
        Fetch and parse a webpage
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object of the parsed HTML
        """
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            time.sleep(self.delay)
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove HTML entities
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        return text
    
    def extract_mcqs_generic(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Generic MCQ extraction that works with common patterns
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            List of MCQ dictionaries
        """
        mcqs = []
        
        # Common patterns for MCQ containers
        mcq_selectors = [
            '.question', '.mcq', '.quiz-question', '.question-container',
            '[class*="question"]', '[class*="mcq"]', '[class*="quiz"]',
            'div.question', 'div.mcq', 'li.question'
        ]
        
        mcq_containers = []
        for selector in mcq_selectors:
            containers = soup.select(selector)
            if containers:
                mcq_containers.extend(containers)
                break
        
        # If no specific containers found, try to find questions by pattern
        if not mcq_containers:
            # Look for numbered questions
            mcq_containers = soup.find_all(text=re.compile(r'^\s*\d+\.\s*'))
            if mcq_containers:
                mcq_containers = [elem.parent for elem in mcq_containers if elem.parent]
        
        for container in mcq_containers:
            mcq = self.extract_single_mcq(container)
            if mcq and mcq['question']:
                mcqs.append(mcq)
        
        return mcqs
    
    def extract_single_mcq(self, container) -> Dict:
        """
        Extract a single MCQ from a container element
        
        Args:
            container: BeautifulSoup element containing the MCQ
            
        Returns:
            Dictionary with MCQ data
        """
        mcq = {
            'question': '',
            'option_a': '',
            'option_b': '',
            'option_c': '',
            'option_d': '',
            'correct_answer': '',
            'explanation': ''
        }
        
        # Extract question
        question_selectors = [
            '.question-text', '.question-title', '.q-text',
            'h3', 'h4', 'h5', 'p:first-child', '.question p'
        ]
        
        question_elem = None
        for selector in question_selectors:
            question_elem = container.select_one(selector)
            if question_elem:
                break
        
        if not question_elem:
            # Try to find question by pattern
            question_text = container.get_text()
            question_match = re.search(r'^\s*\d+\.\s*(.+?)(?=\n|\s*[A-D][\.\)])', question_text, re.MULTILINE)
            if question_match:
                mcq['question'] = self.clean_text(question_match.group(1))
        else:
            mcq['question'] = self.clean_text(question_elem.get_text())
        
        # Extract options
        option_selectors = [
            '.option', '.choice', '.answer-option', '[class*="option"]',
            'li', 'p'
        ]
        
        options = []
        for selector in option_selectors:
            option_elems = container.select(selector)
            if option_elems:
                for elem in option_elems:
                    text = self.clean_text(elem.get_text())
                    # Check if this looks like an option (starts with A, B, C, D)
                    if re.match(r'^\s*[A-D][\.\)]\s*', text):
                        options.append(text)
                if options:
                    break
        
        # If no specific option elements, try to extract from text
        if not options:
            text = container.get_text()
            option_pattern = r'([A-D][\.\)]\s*[^\n]+)'
            option_matches = re.findall(option_pattern, text)
            options = [self.clean_text(opt) for opt in option_matches]
        
        # Assign options to A, B, C, D
        option_keys = ['option_a', 'option_b', 'option_c', 'option_d']
        for i, option in enumerate(options[:4]):
            if i < len(option_keys):
                # Remove the A), B), etc. prefix
                clean_option = re.sub(r'^\s*[A-D][\.\)]\s*', '', option)
                mcq[option_keys[i]] = clean_option
        
        # Extract correct answer
        correct_selectors = [
            '.correct-answer', '.answer', '[class*="correct"]',
            '[class*="answer"]', '.solution'
        ]
        
        for selector in correct_selectors:
            correct_elem = container.select_one(selector)
            if correct_elem:
                correct_text = self.clean_text(correct_elem.get_text())
                # Extract letter from correct answer
                letter_match = re.search(r'[A-D]', correct_text.upper())
                if letter_match:
                    mcq['correct_answer'] = letter_match.group()
                break
        
        # Extract explanation
        explanation_selectors = [
            '.explanation', '.solution', '.answer-explanation',
            '[class*="explanation"]', '[class*="solution"]'
        ]
        
        for selector in explanation_selectors:
            explanation_elem = container.select_one(selector)
            if explanation_elem:
                mcq['explanation'] = self.clean_text(explanation_elem.get_text())
                break
        
        return mcq
    
    def scrape_url(self, url: str) -> List[Dict]:
        """
        Scrape MCQs from a single URL
        
        Args:
            url: URL to scrape
            
        Returns:
            List of MCQ dictionaries
        """
        soup = self.get_page(url)
        if not soup:
            return []
        
        # Try different extraction methods
        mcqs = self.extract_mcqs_generic(soup)
        
        print(f"Found {len(mcqs)} MCQs on {url}")
        return mcqs
    
    def scrape_multiple_pages(self, urls: List[str]) -> List[Dict]:
        """
        Scrape MCQs from multiple URLs
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            List of all MCQ dictionaries
        """
        all_mcqs = []
        for url in urls:
            mcqs = self.scrape_url(url)
            all_mcqs.extend(mcqs)
        
        return all_mcqs
    
    def save_to_csv(self, mcqs: List[Dict], filename: str = 'mcqs.csv'):
        """
        Save MCQs to CSV file
        
        Args:
            mcqs: List of MCQ dictionaries
            filename: Output filename
        """
        if not mcqs:
            print("No MCQs to save")
            return
        
        fieldnames = ['question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'explanation']
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for mcq in mcqs:
                # Ensure correct answer is in capital
                if mcq['correct_answer']:
                    mcq['correct_answer'] = mcq['correct_answer'].upper()
                writer.writerow(mcq)
        
        print(f"Saved {len(mcqs)} MCQs to {filename}")
    
    def print_summary(self, mcqs: List[Dict]):
        """Print a summary of scraped MCQs"""
        print(f"\nSummary:")
        print(f"Total MCQs scraped: {len(mcqs)}")
        
        if mcqs:
            complete_mcqs = [mcq for mcq in mcqs if all([
                mcq['question'], mcq['option_a'], mcq['option_b'], 
                mcq['option_c'], mcq['option_d']
            ])]
            print(f"Complete MCQs (with all options): {len(complete_mcqs)}")
            
            with_answers = [mcq for mcq in mcqs if mcq['correct_answer']]
            print(f"MCQs with correct answers: {len(with_answers)}")
            
            with_explanations = [mcq for mcq in mcqs if mcq['explanation']]
            print(f"MCQs with explanations: {len(with_explanations)}")


def main():
    """Main function to run the scraper"""
    if len(sys.argv) < 2:
        print("Usage: python mcq_scraper.py <website_url> [output_file.csv]")
        print("Example: python mcq_scraper.py https://example.com/mcq-page mcqs.csv")
        return
    
    url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'mcqs.csv'
    
    print(f"Starting MCQ scraper for: {url}")
    print(f"Output file: {output_file}")
    print("-" * 50)
    
    scraper = MCQScraper(url)
    mcqs = scraper.scrape_url(url)
    
    scraper.print_summary(mcqs)
    
    if mcqs:
        scraper.save_to_csv(mcqs, output_file)
        print(f"\nScraping completed! Check {output_file} for results.")
        
        # Show first MCQ as example
        if mcqs[0]['question']:
            print(f"\nExample MCQ:")
            mcq = mcqs[0]
            print(f"Question: {mcq['question'][:100]}...")
            print(f"Options: A) {mcq['option_a'][:50]}...")
            print(f"Correct Answer: {mcq['correct_answer']}")
    else:
        print("\nNo MCQs found. Please check:")
        print("1. The website URL is correct")
        print("2. The website contains MCQs")
        print("3. The website structure is supported")


if __name__ == "__main__":
    main()