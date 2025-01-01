import nltk
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

import requests
from bs4 import BeautifulSoup
from collections import Counter
import re

def remove_stop_words(index):
    stop_words = {
        'a', 'an', 'the', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of',
        'with', 'by', 'from', 'up', 'about', 'into', 'over', 'after', 'is',
        'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'shall', 'should', 'may',
        'might', 'must', 'can', 'could', 'that', 'this', 'these', 'those'
    }
    return Counter({word: count for word, count in index.items() if word not in stop_words})

from nltk.stem import PorterStemmer

def apply_stemming(index):
    stemmer = PorterStemmer()
    stemmed_index = {}
    for word, count in index.items():
        stemmed_word = stemmer.stem(word)
        if stemmed_word in stemmed_index:
            stemmed_index[stemmed_word] += count
        else:
            stemmed_index[stemmed_word] = count
    # Convert the dictionary to a Counter object before returning
    return Counter(stemmed_index)

def scrape_and_count_words(url, target_word):
    try:
        # Send HTTP request to the URL
        response = requests.get(url)
        response.raise_for_status()
        
        # Create BeautifulSoup object to parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get all text from the page
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        print(text)
        
        # Clean the text
        # Convert to lowercase and split into words
        words = re.findall(r'\w+', text.lower())

        # Write words to file using UTF-8 encoding
        with open('words.txt', 'w', encoding='utf-8') as file:
            for word in words:
                file.write(word + '\n')
        
        # Count all words
        word_counts = Counter(words)
        
        # Remove stop words
        word_counts = remove_stop_words(word_counts)
        
        # Apply stemming to the word counts
        stemmed_counts = apply_stemming(word_counts)
        
        # Get count for specific word (stem the target word too)
        stemmer = PorterStemmer()
        stemmed_target = stemmer.stem(target_word.lower())
        target_count = stemmed_counts.get(stemmed_target, 0)
        
        return {
            'target_word_count': target_count,
            'all_word_counts': stemmed_counts
        }
        
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return None

# Example usage
if __name__ == "__main__":
    url = 'https://en.wikipedia.org/wiki/Bird'
    word = 'birds'
    
    result = scrape_and_count_words(url, word)
    
    if result:
        print(f"\nThe word '{word}' appears {result['target_word_count']} times")
        
        # Print top 10 most common words
        print("\nTop 10 most common words:")
        for word, count in result['all_word_counts'].most_common(10):
            print(f"{word}: {count}")
