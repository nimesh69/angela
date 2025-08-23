#!/usr/bin/env python3
"""
Easy MCQ Scraper - Simple script to scrape MCQs from websites
Customize the selectors in the script for your specific website.
"""

import requests
from bs4 import BeautifulSoup
import csv
import re

def scrape_mcqs_from_website(url, output_file='mcqs.csv'):
    """
    Simple function to scrape MCQs from a website
    
    Args:
        url: Website URL containing MCQs
        output_file: Output CSV filename
    """
    
    # Setup session with headers
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    print(f"Fetching: {url}")
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching website: {e}")
        return
    
    soup = BeautifulSoup(response.content, 'html.parser')
    mcqs = []
    
    # =========================================================================
    # CUSTOMIZE THIS SECTION FOR YOUR SPECIFIC WEBSITE
    # =========================================================================
    
    # Method 1: Try to find question containers
    # Common selectors for MCQ containers (modify as needed)
    question_containers = soup.find_all(['div', 'li', 'section'], class_=re.compile(r'question|mcq|quiz'))
    
    if not question_containers:
        # Method 2: Look for numbered questions
        question_containers = []
        for element in soup.find_all(text=re.compile(r'^\s*\d+\.\s*')):
            if element.parent:
                question_containers.append(element.parent)
    
    if not question_containers:
        # Method 3: Look for elements containing "A)" or "a)"
        potential_containers = soup.find_all(text=re.compile(r'[A-D][\.\)]'))
        containers_set = set()
        for element in potential_containers:
            parent = element.parent
            while parent and parent.name not in ['body', 'html']:
                if len(parent.get_text().split('\n')) > 4:  # Likely contains full MCQ
                    containers_set.add(parent)
                    break
                parent = parent.parent
        question_containers = list(containers_set)
    
    print(f"Found {len(question_containers)} potential MCQ containers")
    
    for i, container in enumerate(question_containers, 1):
        print(f"Processing container {i}...")
        
        mcq = {
            'question': '',
            'option_a': '',
            'option_b': '',
            'option_c': '',
            'option_d': '',
            'correct_answer': '',
            'explanation': ''
        }
        
        container_text = container.get_text()
        
        # Extract question (everything before first option or until first A)/a))
        question_match = re.search(r'(.*?)(?=\s*[A-Da-d][\.\)])', container_text, re.DOTALL)
        if question_match:
            question = question_match.group(1).strip()
            # Remove question number if present
            question = re.sub(r'^\s*\d+\.\s*', '', question)
            mcq['question'] = question.strip()
        
        # Extract options A, B, C, D
        option_patterns = [
            (r'[Aa][\.\)]\s*([^\n]*(?:\n(?![A-Da-d][\.\)]).*)*)', 'option_a'),
            (r'[Bb][\.\)]\s*([^\n]*(?:\n(?![A-Da-d][\.\)]).*)*)', 'option_b'),
            (r'[Cc][\.\)]\s*([^\n]*(?:\n(?![A-Da-d][\.\)]).*)*)', 'option_c'),
            (r'[Dd][\.\)]\s*([^\n]*(?:\n(?![A-Da-d][\.\)]).*)*)', 'option_d')
        ]
        
        for pattern, key in option_patterns:
            match = re.search(pattern, container_text, re.IGNORECASE | re.MULTILINE)
            if match:
                option_text = match.group(1).strip()
                # Clean up option text
                option_text = re.sub(r'\s+', ' ', option_text)
                mcq[key] = option_text
        
        # Try to find correct answer
        # Look for patterns like "Answer: A", "Correct: B", etc.
        answer_patterns = [
            r'(?:answer|correct|solution)[\s:]*([A-D])',
            r'correct\s+answer[\s:]*([A-D])',
            r'answer[\s:]*\(?([A-D])\)?'
        ]
        
        for pattern in answer_patterns:
            match = re.search(pattern, container_text, re.IGNORECASE)
            if match:
                mcq['correct_answer'] = match.group(1).upper()
                break
        
        # Try to find explanation
        explanation_patterns = [
            r'(?:explanation|solution|reason)[\s:]+(.+?)(?=\n\s*\d+\.|$)',
            r'(?:because|since)[\s:]+(.+?)(?=\n\s*\d+\.|$)'
        ]
        
        for pattern in explanation_patterns:
            match = re.search(pattern, container_text, re.IGNORECASE | re.DOTALL)
            if match:
                explanation = match.group(1).strip()
                explanation = re.sub(r'\s+', ' ', explanation)
                mcq['explanation'] = explanation
                break
        
        # Only add MCQ if it has question and at least 2 options
        if mcq['question'] and mcq['option_a'] and mcq['option_b']:
            mcqs.append(mcq)
            print(f"  ✓ Extracted: {mcq['question'][:50]}...")
        else:
            print(f"  ✗ Skipped incomplete MCQ")
    
    # Save to CSV
    if mcqs:
        fieldnames = ['question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'explanation']
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(mcqs)
        
        print(f"\n✓ Successfully saved {len(mcqs)} MCQs to {output_file}")
        
        # Show sample
        if mcqs:
            print(f"\nSample MCQ:")
            sample = mcqs[0]
            print(f"Question: {sample['question']}")
            print(f"A) {sample['option_a']}")
            print(f"B) {sample['option_b']}")
            print(f"C) {sample['option_c']}")
            print(f"D) {sample['option_d']}")
            print(f"Answer: {sample['correct_answer']}")
            if sample['explanation']:
                print(f"Explanation: {sample['explanation']}")
    else:
        print("No MCQs found. You may need to customize the extraction logic for this website.")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python easy_scraper.py <website_url> [output_file.csv]")
        print("Example: python easy_scraper.py https://example.com/mcqs mcqs.csv")
        sys.exit(1)
    
    url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'mcqs.csv'
    
    scrape_mcqs_from_website(url, output_file)