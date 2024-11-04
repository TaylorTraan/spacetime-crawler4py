import re
from urllib.parse import urlparse, urljoin, parse_qs, urldefrag
from url_normalize import url_normalize
from bs4 import BeautifulSoup
import lxml




def scraper(url, resp, visitedURLs, subdomains):
    """Scrapes the URL and returns a list of valid links."""
    try:
        if resp.status != 200:
            return []
        if resp.raw_response is None:
            return []
        if resp.raw_response.content is None:
            return []
        if not resp:
            return []
        
        visitedURLs.add(url)
        getSubdomains(url, subdomains)
        
        if resp.status == 200:
            links = extract_next_links(url, resp)
            return [link for link in links if is_valid(link, visitedURLs)]
        else:
            return []
    except Exception as e:
        print(f"error at {url}")
        return []

def extract_next_links(url, resp):
    """Extracts hyperlinks from a given URL's response content."""
    hyperLinks = []  # Store extracted hyperlinks.
    
    try:

        if  resp and resp.status == 200 and resp.raw_response:  # If the request is successful.
            soup = BeautifulSoup(resp.raw_response.content, 'lxml')
            foundLinks = soup.findAll('a', href=True) # Find all anchor tags with href attributes.
            
            print(f"starting to crawl at {resp.url}")
            for link in foundLinks:  
                relativeLink = link['href']
                fullLink = urljoin(url, relativeLink)  # Combine base URL with the found link.
                
                defragmentedLink = urldefrag(fullLink)[0]
                
                hyperLinks.append(defragmentedLink)
        else:
            print(f"Error: Unable to fetch page. Status: {resp.status}")
            if hasattr(resp, 'error') and resp.error:
                print(f"Error details: {resp.error}")
    except AttributeError as e:
        print(f"AttributeError: {e} - Please check the response structure.")
    except Exception as e:
        print(f"Unexpected error occurred: {e}")

    return hyperLinks

def getSubdomains(url, subdomains):
    parsedUrl = urlparse(url)
    
    domain = parsedUrl.hostname

    #if domain is not none and domain is in allowed domains
    if domain and domain.endswith(".ics.uci.edu"):
        defragPath = urldefrag(url)[0]
        if domain in subdomains:
            subdomains[domain].add(defragPath)
        else:
            subdomains[domain] = {defragPath}

def is_valid(url, visitedUrl):
    """Checks if the URL should be crawled or not, avoiding traps."""
    try:
        
        if url in visitedUrl:
            return False
        parsed = urlparse(url_normalize(url))

        # Check the scheme.
        if parsed.scheme not in {"http", "https"}:
            return False
        
        #Checks if it has hostname
        if parsed.hostname is None:
            return False
        
        # Check if the path is blacklisted
        blackListedPaths = [
            '/~eppstein/pix/',
            '/ml/datasets.php',
            "ml/machine-learning-databases/tic-mld/ticeval2000.txt"
        ]
        if (parsed.path.startswith(blackListedPaths[0]) and parsed.path != blackListedPaths[0]) or parsed.path in blackListedPaths:
            return False

        #if current domain doesn't exist in listed domains; false
        allowedDomains = r"(.*\.ics\.uci\.edu|.*\.cs\.uci\.edu|.*\.informatics\.uci\.edu|.*\.stat\.uci\.edu)"
        if not re.match(allowedDomains, parsed.hostname):
            return False

        # Avoid non-HTML content.
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1|img|war|sql|apk|mpg|htm"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", 
            parsed.path.lower()):
            return False
        
        if len(url) > 200 or len(parsed.path.split('/')) > 20:
            print(f"Skipping overly long URL: {url}")
            return False

        return True

    except TypeError as e:
        print(f"TypeError for {url}: {e}")
        return False