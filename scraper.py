import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

def scraper(url, resp):
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

            # Look for all anchor tags with href attributes.
            for anchor in soup.find_all('a', href=True):
                link = anchor['href']
                fullLink = urljoin(url, link)  # Combine base URL with the found link.
                print(f"Found link: {fullLink}\n")
                hyperLinks.append(fullLink)

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
    """Checks if the URL should be crawled or not."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
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

        # Ensure the URL is not pointing to unwanted file types.
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError as e:
        print(f"TypeError for {url}: {e}")
        return False
