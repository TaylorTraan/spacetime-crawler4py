import re
from urllib.parse import urlparse, urljoin, parse_qs
from bs4 import BeautifulSoup

# A global set to track visited URLs and avoid duplicates.
visited_urls = set()

def scraper(url, resp):
    """Scrapes the URL and returns a list of valid links."""
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    """Extracts hyperlinks from a given URL's response content."""
    hyperLinks = []  # Store extracted hyperlinks.

    try:
        # Access the status safely.
        status = getattr(resp, 'status', None) or getattr(resp.raw_response, 'status', None)

        if status == 200:  # If the request is successful.
            soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
            print(f"Starting to crawl at: {resp.url}")

            # Find all anchor tags with href attributes.
            for anchor in soup.find_all('a', href=True):
                link = anchor['href']
                fullLink = urljoin(url, link)  # Combine base URL with the found link.

                # Check for duplicate URLs and traps.
                if fullLink not in visited_urls:
                    print(f"Found link: {fullLink}")
                    hyperLinks.append(fullLink)
                    visited_urls.add(fullLink)  # Mark as visited.
                else:
                    print(f"Skipping duplicate or previously visited URL: {fullLink}")

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

        # Avoid overly long URLs (potential traps).
        if len(url) > 200:
            print(f"Skipping overly long URL: {url}")
            return False

        return True

    except TypeError as e:
        print(f"TypeError for {url}: {e}")
        return False

