import requests
from bs4 import BeautifulSoup
from collections import Counter

# List of URLs to scrape
urls = [
    "https://www.premierleague.com/news/3998819",
    "https://www.premierleague.com/news/3960710",
    "https://www.premierleague.com/news/3921955",
    "https://www.premierleague.com/news/3921955",
    "https://www.premierleague.com/news/3893153",
    "https://www.premierleague.com/news/3853193",
    "https://www.premierleague.com/news/3808489",
    "https://www.premierleague.com/news/3808575",
    "https://www.premierleague.com/news/3776619",
    "https://www.premierleague.com/news/3331263"

]

# Words to search for
search_words = ["Player", "Award", "Month", "London", "April", "Manager"]


# Function to count the words
def count_words_in_page(url, search_words):
    # Get the page content
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Get all text from the page
    text = soup.get_text().lower()

    # Count occurrences of each word
    word_counts = Counter(text.split())

    # Search for the specified words
    results = {word.lower(): word_counts[word.lower()] for word in search_words}

    return results


# Loop through each URL and print the word counts
for url in urls:
    page_counts = count_words_in_page(url, search_words)
    print(f"\nWord counts for {url}:")
    for word, count in page_counts.items():
        print(f"{word}: {count}")
