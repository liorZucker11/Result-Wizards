import requests
from bs4 import BeautifulSoup
from collections import Counter
import csv

# List of URLs to scrape
urls = [
    "https://www.nba.com/player/1630166/deni-avdija",
    "https://www.nba.com/player/2544/lebron-james",
    "https://www.nba.com/player/1629029/luka-doncic",
    "https://www.nba.com/player/201939/stephen-curry",
    "https://www.nba.com/player/203507/giannis-antetokounmpo",
    "https://www.nba.com/player/1628369/jayson-tatum",
    "https://www.nba.com/player/201935/james-harden",
    "https://www.nba.com/player/1626164/devin-booker",
    "https://www.nba.com/player/201566/russell-westbrook",
    "https://www.nba.com/player/203076/anthony-davis",
]

# Words to search for
search_words = ["Player", "Games", "Assists", "Last", "Rebounds", "Points"]

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


# Function to export results to CSV
def export_to_csv(filename, results):
    """
    Exports the word count results to a CSV file.
    """
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Write the header
        header = ["URL"] + search_words
        writer.writerow(header)

        # Write the data
        for url, counts in results.items():
            row = [url] + [counts[word.lower()] for word in search_words]
            writer.writerow(row)

    print(f"Word counts exported to {filename}")


# Collect word counts for all URLs
all_results = {}
for url in urls:
    page_counts = count_words_in_page(url, search_words)
    all_results[url] = page_counts

# Print the results (optional)
for url, counts in all_results.items():
    print(f"\nWord counts for {url}:")
    for word, count in counts.items():
        print(f"{word}: {count}")

# Export to CSV
export_to_csv("CSV_Files/word_counts.csv", all_results)
