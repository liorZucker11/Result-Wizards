from collections import defaultdict, Counter
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk

nltk.download('stopwords')
nltk.download('punkt')
nltk.data.path.append(r"C:\Users\USER\nltk_data")

# Initialize stop words
stop_words = set(stopwords.words('english'))
stop_words.update(map(str, range(10)))  # Add digits '0'-'9' to stop words
stop_words.update(map(chr, range(ord('a'), ord('z') + 1)))  # Add letters 'a'-'z' to stop words


def process_text(content):
    words = word_tokenize(content.lower())  # Tokenize and convert to lowercase
    words = [word for word in words if word.isalnum() and word not in stop_words]  # Filter out stop words and non-alphanumeric tokens
    return words


def build_inverted_index_from_pages(pages_content):
    """
    Build an inverted index and calculate the most frequent words from a list of pages content.
    """
    inverted_index = defaultdict(set)
    word_counts = Counter()

    for doc_id, content in enumerate(pages_content, start=1):
        words = process_text(content)
        word_counts.update(words)
        for word in words:
            inverted_index[word].add(doc_id)

    # Get the 15 most common words
    most_common_words = [word for word, _ in word_counts.most_common(15)]

    # Create an inverted index for the most common words
    final_inverted_index = {word: inverted_index[word] for word in most_common_words}

    return final_inverted_index, word_counts.most_common(15)
