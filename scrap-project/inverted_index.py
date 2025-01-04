import re
from collections import defaultdict, Counter
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv

# Download stopwords and punkt if not already downloaded
# nltk.download('stopwords')
# nltk.download('punkt')
# nltk.download('punkt_tab')


# Initialize stop words
stop_words = set(stopwords.words('english'))
stop_words.update(map(str, range(10)))  # Add digits '0'-'9' to stop words
stop_words.update(map(chr, range(ord('a'), ord('z') + 1)))  # Add letters 'a'-'z' to stop words


def export_inverted_index_to_csv(filename, inverted_index):
    """
    Exports the inverted index to a CSV file.
    Each row contains a word and the list of document IDs where the word appears.
    """
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Word", "Document IDs"])  # Write the header

        for word, doc_ids in inverted_index.items():
            writer.writerow([word, ", ".join(map(str, sorted(doc_ids)))])  # Write word and doc IDs

    print(f"Inverted index exported to {filename}")


# Function to process text and remove stop words
def process_text(text):
    words = word_tokenize(text.lower())  # Tokenize and convert to lowercase
    words = [word for word in words if word.isalnum() and word not in stop_words]  # Filter out stop words and non-alphanumeric tokens
    return words


# Function to fetch page content
def fetch_page_content(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    return ""


# Function to extract meaningful text from HTML content
def extract_text_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    # Extract text from paragraphs, headings, etc.
    text = ' '.join(soup.stripped_strings)
    return text


# Example input URLs and their corresponding paths
urls_pages = {
    "https://www.nba.com/": {
        1: "player/1630166/deni-avdija",
        2: "player/2544/lebron-james",
        3: "player/1629029/luka-doncic",
        4: "player/201939/stephen-curry",
        5: "player/203507/giannis-antetokounmpo",
        6: "player/1628369/jayson-tatum",
        7: "player/201935/james-harden",
        8: "player/1626164/devin-booker",
        9: "player/201566/russell-westbrook",
        10: "player/203076/anthony-davis",

    },
    "https://www.nba.com/celtics/news/": {
        11: "sidebar-post-20241215-pritchard-makes-history-in-d-c-as-celtics-down-wizards",
        12: "sidebar-post-20241220-3-point-barrage-bulls-beat-boston-at-its-own-game",
        13: "sidebar-post-20241227-jaylen-brown-delivers-sparkling-two-way-effort-in-37-point-win-over-indy",
        14: "sidebar-post-20241225-celtics-strive-to-curb-inconsistencies-after-rare-back-to-back-losses",
        15: "gamerecap-keys-20241231-torbos",
        16: "gamerecap-keys-20250103-boshou",
        17: "sidebar-post-20250102-derrick-white-delivers-star-effort-in-win-over-t-wolves",
        18: "sidebar-post-20241231-celtics-54-point-win-closes-out-historic-year",
        19: "sidebar-post-20241229-al-horford-payton-pritchard-both-move-up-celtics-all-time-3-point-list",
        20: "sidebar-post-20241223-celtics-fall-in-orlando-despite-jaylen-browns-season-best-effort",
    }
}

# Build inverted index
inverted_index = defaultdict(set)
word_counts = Counter()

for base_url, paths in urls_pages.items():
    for doc_id, path in paths.items():
        # Join base URL with path
        full_url = urljoin(base_url, path)
        # Fetch page content
        html_content = fetch_page_content(full_url)
        # Extract and process text from HTML content
        page_text = extract_text_from_html(html_content)
        words = process_text(page_text)
        word_counts.update(words)
        for word in words:
            inverted_index[word].add(doc_id)

# Get the 15 most common words
most_common_words = [word for word, _ in word_counts.most_common(15)]

# Create an inverted index for the most common words
final_inverted_index = {word: inverted_index[word] for word in most_common_words}

export_inverted_index_to_csv("inverted_index.csv", final_inverted_index)

