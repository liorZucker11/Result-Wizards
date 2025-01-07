from bs4 import BeautifulSoup
import networkx as nx
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import matplotlib.pyplot as plt
from urllib.parse import urljoin
from nltk.corpus import stopwords

# Download stopwords if not already downloaded
# nltk.download('stopwords')
# nltk.download('punkt')

stop_words = set(stopwords.words('english'))

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

chrome_options = Options()
chrome_options.add_argument("--headless=new")  # Use new headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)


def trim_url(url):
    """Trim the URL to its last part for simplicity."""
    return url.rstrip('/').split('/')[-1]


def fetch_links(url):
    """Fetch NBA-related links from the given page, but only return links in the `urls` list."""
    try:
        driver.get(url)
        time.sleep(3)  # Wait for the page to load completely

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        links = set()

        # Find all <a> tags and extract NBA-related links
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href.startswith('/'):
                href = urljoin("https://www.nba.com", href)  # Convert relative to absolute URLs
            if href in urls and href != url:
                links.add(href.rstrip('/'))  # Remove trailing slash for consistency

        return links
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return set()


trimmed_urls = [trim_url(url) for url in urls]

# Create a directed graph
G = nx.DiGraph()
for original, trimmed in zip(urls, trimmed_urls):
    G.add_node(trimmed)

# Add edges between pages by scraping links
for original, trimmed in zip(urls, trimmed_urls):
    print(f"Scraping {original}")
    links = fetch_links(original)
    # Only consider links in the `urls` list
    filtered_links = [link for link in links if link in urls]
    trimmed_links = [trim_url(link) for link in filtered_links]
    for link, trimmed_link in zip(filtered_links, trimmed_links):
        print(f"Adding edge from {original} to {link}")
        G.add_edge(trimmed, trimmed_link)

# Calculate PageRank
pagerank = nx.pagerank(G, alpha=0.85)

# Visualize the graph
plt.figure(figsize=(12, 12))  # Set figure size
pos = nx.spring_layout(G, k=0.5, iterations=50)  # Use a layout for positioning nodes
nx.draw(G, pos, with_labels=True, node_size=2000, node_color='skyblue', font_size=10, font_weight='bold', arrows=True)
plt.title("NBA Page Link Graph (Filtered)")
plt.show()

# Print the PageRank of each page
for page, rank in pagerank.items():
    print(f"{page} : {rank:.3f}")

# Quit the driver
driver.quit()
