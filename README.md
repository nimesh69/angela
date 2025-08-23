# MCQ Web Scraper for Sanfoundry

This project contains Python scripts to scrape Multiple Choice Questions (MCQs) from Sanfoundry website and save them in CSV format.

## 🎯 Output Format

The scraper saves MCQs in CSV format with the following columns:
```
question,option_a,option_b,option_c,option_d,correct_answer(in capital),explanation
```

Example:
```csv
What is a data structure?,A programming language,A collection of algorithms,A way to store and organize data,A type of computer hardware,C,A data structure is a way to store and organize data efficiently
```

## 📁 Files Included

### Main Scrapers
1. **`improved_sanfoundry_scraper.py`** - ⭐ **RECOMMENDED** 
   - Comprehensive scraper for Sanfoundry MCQ pages
   - Extracts links from index pages and scrapes individual MCQ pages
   - Uses only built-in Python modules (no external dependencies)

2. **`sanfoundry_full_scraper.py`** - Alternative comprehensive scraper

3. **`sanfoundry_scraper.py`** - Basic scraper (single page)

### Utility Scripts
4. **`mcq_scraper.py`** - Generic scraper for any MCQ website (requires external libraries)
5. **`easy_scraper.py`** - Simplified scraper template
6. **`debug_sanfoundry.py`** - Debug tool to analyze website structure

### Configuration
7. **`requirements.txt`** - External dependencies (optional)

## 🚀 Quick Start

### Option 1: Using the Improved Scraper (Recommended)

```bash
# Scrape 10 pages from Sanfoundry Data Structures & Algorithms
python3 improved_sanfoundry_scraper.py "https://www.sanfoundry.com/1000-data-structures-algorithms-ii-questions-answers/" mcqs.csv 10
```

### Option 2: Custom Number of Pages

```bash
# Scrape 5 pages (faster)
python3 improved_sanfoundry_scraper.py "https://www.sanfoundry.com/1000-data-structures-algorithms-ii-questions-answers/" my_mcqs.csv 5

# Scrape 20 pages (more comprehensive)
python3 improved_sanfoundry_scraper.py "https://www.sanfoundry.com/1000-data-structures-algorithms-ii-questions-answers/" all_mcqs.csv 20
```

## 📖 Usage Instructions

### Basic Usage
```bash
python3 improved_sanfoundry_scraper.py <index_url> [output_file.csv] [max_pages]
```

**Parameters:**
- `index_url`: The Sanfoundry index page URL (required)
- `output_file.csv`: Output CSV filename (default: mcqs.csv)
- `max_pages`: Maximum number of MCQ pages to scrape (default: 20)

### Example Commands

```bash
# Basic usage - scrapes 20 pages by default
python3 improved_sanfoundry_scraper.py "https://www.sanfoundry.com/1000-data-structures-algorithms-ii-questions-answers/"

# Save to specific file
python3 improved_sanfoundry_scraper.py "https://www.sanfoundry.com/1000-data-structures-algorithms-ii-questions-answers/" my_questions.csv

# Limit to 5 pages for testing
python3 improved_sanfoundry_scraper.py "https://www.sanfoundry.com/1000-data-structures-algorithms-ii-questions-answers/" test.csv 5

# Comprehensive scraping (50 pages)
python3 improved_sanfoundry_scraper.py "https://www.sanfoundry.com/1000-data-structures-algorithms-ii-questions-answers/" comprehensive.csv 50
```

## 🔧 Installation & Requirements

### No Installation Required!
The main scraper (`improved_sanfoundry_scraper.py`) uses only built-in Python modules:
- `urllib.request` - for web requests
- `html.parser` - for HTML parsing
- `csv` - for CSV file operations
- `re` - for regular expressions

### Optional Dependencies
If you want to use the generic scrapers, install:
```bash
pip install -r requirements.txt
```

## 📊 What the Scraper Does

1. **Link Extraction**: Finds all MCQ page links from the Sanfoundry index page
2. **Individual Page Scraping**: Visits each MCQ page and extracts questions
3. **Data Parsing**: Extracts:
   - Question text
   - Four options (A, B, C, D)
   - Correct answer (in capital letter)
   - Explanation (when available)
4. **Deduplication**: Removes duplicate questions
5. **CSV Export**: Saves in the specified format

## 📈 Expected Output

### Typical Results
- **Pages Found**: 200+ MCQ page links
- **Success Rate**: 80-95% of pages scraped successfully  
- **MCQs per Page**: 1-15 MCQs depending on page content
- **Total MCQs**: 50-500+ depending on pages scraped

### Sample Output
```
Improved Sanfoundry MCQ Scraper
==================================================
Extracting MCQ links from: https://www.sanfoundry.com/1000-data-structures-algorithms-ii-questions-answers/
Found 235 MCQ page links
Sample links:
  1. https://www.sanfoundry.com/searching-multiple-choice-questions-mcq/
  2. https://www.sanfoundry.com/data-structure-questions-answers-linear-search-iterative/
  ...

Limiting to first 10 pages
[1/10] Scraping: https://www.sanfoundry.com/searching-multiple-choice-questions-mcq/
  Found 5 MCQs
[2/10] Scraping: https://www.sanfoundry.com/data-structure-questions-answers-linear-search-iterative/
  Found 3 MCQs
...

==================================================
Pages scraped successfully: 10/10
Total MCQs scraped: 45
Unique MCQs: 42
Complete MCQs (all fields): 38
MCQs with answers: 42
✓ Successfully saved 42 MCQs to mcqs.csv
```

## ⚠️ Important Notes

### Rate Limiting
- The scraper includes delays between requests (1.5 seconds) to be respectful to the server
- Don't scrape too aggressively to avoid being blocked

### Website Structure
- The scraper is designed for the current Sanfoundry website structure
- If the website changes, the scraper may need updates

### Data Quality
- Not all pages may contain MCQs in the expected format
- Some MCQs may have incomplete data (missing options or explanations)
- The scraper includes quality metrics in the output

## 🛠️ Troubleshooting

### No MCQs Found
```bash
# Use debug script to analyze page structure
python3 debug_sanfoundry.py
```

### Network Issues
- Check internet connection
- Try reducing the number of pages
- The website may be temporarily unavailable

### CSV Format Issues
- Ensure you're using UTF-8 encoding when opening the CSV
- Use Excel's "Data > From Text/CSV" feature for proper formatting

## 📝 Example CSV Output

```csv
question,option_a,option_b,option_c,option_d,correct_answer,explanation
What is a data structure?,A programming language,A collection of algorithms,A way to store and organize data,A type of computer hardware,C,A data structure is a way to store and organize data efficiently
Which searching algorithm is fastest?,Linear search,Binary search,Jump search,All are equal,B,Binary search has O(log n) time complexity
What is the time complexity of linear search?,O(1),O(log n),O(n),O(n^2),C,Linear search checks each element sequentially
```

## 🎯 Tips for Best Results

1. **Start Small**: Begin with 5-10 pages to test
2. **Check Output**: Review the CSV file for data quality
3. **Adjust Pages**: Increase page count for more comprehensive results
4. **Monitor Progress**: Watch the console output for success rates
5. **Be Patient**: Large scraping jobs take time due to rate limiting

## 🔄 Updates & Maintenance

The scraper may need updates if:
- Sanfoundry changes their website structure
- New MCQ formats are introduced
- Performance optimizations are needed

For issues or improvements, check the individual script files for modification guidelines.

---

**Last Updated**: 2024
**Compatible with**: Python 3.6+
**Tested on**: Sanfoundry Data Structures & Algorithms MCQ pages