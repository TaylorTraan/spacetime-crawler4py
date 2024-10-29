import re
from urllib.parse import urlparse, urljoin, parse_qs
from bs4 import BeautifulSoup
import lxml
from collections import Counter, defaultdict

# A global set to track visited URLs and avoid duplicates.
visited_urls = set()

# Data structures for analytics
unique_pages = set()  # Tracks unique pages based on URL (excluding fragments)
page_lengths = {}     # Tracks page lengths {url: word_count}
word_counter = Counter()  # Counts words across all pages
subdomains = defaultdict(int)  # Counts unique pages per subdomain

# Load English stop words
with open("stop_words.txt") as f:
    stop_words = set(f.read().split())

def scraper(url, resp):
    """Scrapes the URL and returns a list of valid links."""
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    """Extracts hyperlinks from a given URL's response content."""
    global unique_pages
    hyperLinks = []  # Store extracted hyperlinks.
    

    try:
        # Access the status safely.
        status = getattr(resp, 'status', None) or getattr(resp.raw_response, 'status', None)

        if status == 200 and resp and resp.raw_response:  # If the request is successful.
            soup = BeautifulSoup(resp.raw_response.content, 'lxml')
            aTags = soup.findAll('a', href=True) # Find all anchor tags with href attributes.
            
            text = soup.get_text()
            words = re.findall(r'\b\w+\b', text.lower())
            words = [word for word in words if word not in stop_words]

            # Update page length
            page_lengths[url] = len(words)

            # Update word counter
            word_counter.update(words)

            # Track subdomains
            domain = urlparse(url).netloc
            if domain.endswith('.uci.edu'):
                subdomains[domain] += 1
    
            for anchor in aTags:
                relativeLink = anchor['href']
                fullLink = urljoin(url, relativeLink)  # Combine base URL with the found link.

                # Check for duplicate URLs and traps.
                print(f"Found link: {fullLink}")
                hyperLinks.append(fullLink)
                visited_urls.add(fullLink)  # Mark as visited.

            unique_pages.add(url)

        else:
            print(f"Error: Unable to fetch page. Status: {status}")
            if hasattr(resp, 'error') and resp.error:
                print(f"Error details: {resp.error}")

    except AttributeError as e:
        print(f"AttributeError: {e} - Please check the response structure.")
    except Exception as e:
        print(f"Unexpected error occurred: {e}")

    return hyperLinks

def is_valid(url):
    """Checks if the URL should be crawled or not, avoiding traps."""
    try:
        parsed = urlparse(url)

        # Check the scheme.
        if parsed.scheme not in {"http", "https"}:
            return False

        # Avoid revisiting the same URL.
        if url in visited_urls:
            return False

        # Avoid URLs with query parameters that look like calendars or session IDs.
        query_params = parse_qs(parsed.query)
        if any(re.match(r'\d{4}-\d{2}-\d{2}', param) for param in query_params):
            print(f"Skipping potential calendar trap: {url}")
            return False

        # Allowed domains for crawling.
        allowedDomains = {
            ".ics.uci.edu",
            ".cs.uci.edu",
            ".informatics.uci.edu",
            ".stat.uci.edu",
            "today.uci.edu/department/information_computer_sciences",
        }

        # Check if the domain is in the allowed list.
        if not any(domain in parsed.netloc for domain in allowedDomains):
            return False

        # Avoid non-HTML content.
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", 
            parsed.path.lower()):
            return False


        return True

    except TypeError as e:
        print(f"TypeError for {url}: {e}")
        return False


def generate_report():
    """Generates a report with analytics and saves it to a text file."""
    # Longest page URL and length
    longest_page_url, longest_page_length = max(page_lengths.items(), key=lambda x: x[1], default=("None", 0))

    # 50 most common words
    common_words = word_counter.most_common(50)

    # Write report
    with open("analytics_report.txt", "w") as f:
        f.write("Analytics Report\n")
        f.write("================\n\n")
        
        # Unique pages
        f.write(f"Total unique pages: {len(unique_pages)}\n\n")
        
        # Longest page
        f.write(f"Longest page: {longest_page_url}\n")
        f.write(f"Word count: {longest_page_length}\n\n")
        
        # Most common words
        f.write("50 Most Common Words (excluding stop words):\n")
        for word, count in common_words:
            f.write(f"{word}: {count}\n")
        f.write("\n")

        # Subdomains
        f.write("Subdomains and Unique Pages Count:\n")
        for domain, count in sorted(subdomains.items()):
            f.write(f"{domain}, {count}\n")

# Call this function at the end of the crawl to generate the report
generate_report()