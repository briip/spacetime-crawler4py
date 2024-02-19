import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from lxml import html


def scraper(url, resp):
    links = extract_next_links(url, resp)

    # Save unique url
    count_unique_urls(links, 'unique_pages_count.txt')
    # Save the longest page to a different output file
    save_longest_page(url, resp, 'longest_page_info.txt')

    return [link for link in links if is_valid(link)]


def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    links = []

    if resp.status == 200 and resp.raw_response.content:

        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')

        for hyperlink in soup.find_all('a', href=True):

            links.append(hyperlink['href'])  # href contains the URL that the hyperlink points to

    return list()


def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        # de-fragment
        url_without_fragment = url.split("#")[0]

        parsed = urlparse(url_without_fragment)

        if parsed.scheme not in set(["http", "https"]):
            return False

        # Only crawl these domains
        allowed_domains = [
            "ics.uci.edu",
            "cs.uci.edu",
            "informatics.uci.edu",
            "stat.uci.edu"
        ]

        # Check if the domain of the URL is in the allowed domains
        if not any(parsed.netloc.endswith(domain) for domain in allowed_domains):
            return False

        # Allow these file types
        if not re.match(
                r"^\/[^\/]*(\/.*)?$",
                parsed.path
        ) or re.match(   # Exclude these file types
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            return False

        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise


'''  if parsed.netloc.endswith(("ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu")):
                return re.match(r"^\/.*$", parsed.path)
            return False
    '''


def count_unique_urls(urls, output_file):
    unique_urls = set()  # Set to store unique URLs

    # Iterate through the URLs and add them to the set
    for url in urls:
        # Remove fragment from the URL
        url_no_fragment = urlparse(url)._replace(fragment='').geturl()
        # Add the URL without fragment to the set of unique URLs
        unique_urls.add(url_no_fragment)

    # Count the number of unique URLs
    unique_count = len(unique_urls)

    # Append the count to the specified file
    with open(output_file, 'a') as file:
        file.write(str(unique_count) + '\n')


def save_longest_page(url, resp, output_file):
    # Check if the response is successful (status code 200)
    if resp.status == 200:
        # Parse the HTML content
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
        # Find all text elements in the HTML
        text_elements = soup.find_all(text=True)
        # Concatenate the text elements to form the entire page content
        page_content = ' '.join(element.strip() for element in text_elements if element.strip())
        # Split the page content into words
        words = page_content.split()
        # Calculate the number of words in the page
        word_count = len(words)

        # Check if the file exists
        try:
            with open(output_file, 'r') as file:
                # Read the current longest page length
                current_longest, current_url = map(str.strip, file.readlines())
        except FileNotFoundError:
            # If the file doesn't exist, set the current longest to 0
            current_longest, current_url = '0', ''

        # If the current page is longer than the previous longest page, save it to the file
        if word_count > current_longest:
            # Write the new longest page length and URL to the file
            with open(output_file, 'w') as file:
                file.write(f"{word_count}\n{url}")






