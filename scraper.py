import re
from urllib.parse import urlparse, urljoin, urldefrag, urlunparse

from bs4 import BeautifulSoup
import tokenize
import time

from collections import defaultdict

MAX_URL_CONTENT_LENGTH = 5 * 1024 * 1024  # one megabyte



visited_urls = []
words_dict=defaultdict(int)
longest_url=('',0)
subdomains=defaultdict(int)

visit_count = dict()  # Map paths to times visited

STOP_WORDS = {'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't",
              'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by',
              "can't", 'cannot', 'could', "couldn't", 'did', "didn't", 'do', 'does', "doesn't", 'doing', "don't",
              'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', "hadn't", 'has', "hasn't", 'have',
              "haven't", 'having', 'he', "he'd", "he'll", "he's", 'her', 'here', "here's", 'hers', 'herself', 'him',
              'himself', 'his', 'how', "how's", 'i', "i'd", "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', "isn't",
              'it', "it's", 'its', 'itself', "let's", 'me', 'more', 'most', "mustn't", 'my', 'myself', 'no', 'nor',
              'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out',
              'over', 'own', 'same', "shan't", 'she', "she'd", "she'll", "she's", 'should', "shouldn't", 'so', 'some',
              'such', 'than', 'that', "that's", 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there',
              "there's", 'these', 'they', "they'd", "they'll", "they're", "they've", 'this', 'those', 'through', 'to',
              'too', 'under', 'until', 'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'were',
              "weren't", 'what', "what's", 'when', "when's", 'where', "where's", 'which', 'while', 'who', "who's",
              'whom', 'why', "why's", 'with', "won't", 'would', "wouldn't", 'you', "you'd", "you'll", "you're",
              "you've", 'your', 'yours', 'yourself', 'yourselves'}


def scraper(url, resp):
    links = extract_next_links(url, resp)
    output_to_txt()
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

    if url in visited_urls:
        return links

    try:
        if resp.status == 200 and len(resp.raw_response.content) < MAX_URL_CONTENT_LENGTH:

            visited_urls.append(url)

            parse_url = urlparse(url)

            extract_content(url, resp)

            soup = BeautifulSoup(resp.raw_response.content, 'html.parser')

            for new_url in soup.find_all('a'):

                absolute_link = urldefrag(urljoin(parse_url.scheme + "://" + parse_url.netloc, new_url['href']))[0]
                if '?' in absolute_link:
                    absolute_link = absolute_link.split("?")[0]

                if not max_visits(absolute_link):
                    links.append(absolute_link)

    except AttributeError:
        print(f'Status Code: {resp.status}\nError: {resp.error}')
    return list()


def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        if not re.match(
                r".*\.(ics\.uci\.edu"
                + r"|cs\.uci\.edu"
                + r"|informatics\.uci\.edu"
                + r"|stat\.uci\.edu)", parsed.netloc.lower()):
            return False

        # Avoid pdfs
        if "pdf" in parsed.path:
            return False

        # zip attachments
        if "zip-attachment" in parsed.path.lower():
            return False

        # files
        if "/files" in url or "/file" in url:
            return False

        # user uploads
        if "wp-content/uploads" in parsed.path.lower():
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico|php"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|ppsx|pps"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|ova"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv|xml"
            + r"|r|py|java|c|cc|cpp|h|svn|svn-base|bw|bigwig"
            + r"|txt|odc|apk|img|war"
            + r"|bam|bai|out|tab|edgecount|junction|ipynb|bib|lif"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise


def extract_content(url, resp):

    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
    tokens_list = tokenize_content(soup.text)
    # Only high text content pages
    if len(tokens_list) > 100:
        filtered_tokens=[token for token in tokens_list if token not in STOP_WORDS]

        global longest_url
        if len(filtered_tokens)>longest_url[1]:
            longest_url=(url, len(filtered_tokens))
        for token in filtered_tokens:
            words_dict[token]+=1

        parse_url = urlparse(url)
        if "ics.uci.edu" in parse_url.netloc or "cs.uci.edu" in parse_url.netloc or "informatics.uci.edu" in parse_url.netloc or "stat.uci.edu" in parse_url.netloc:
            if "https://" + parse_url.netloc in subdomains.keys():
                subdomains["https://" + parse_url.netloc] += 1
            elif "http://" + parse_url.netloc in subdomains.keys():
                subdomains["http://" + parse_url.netloc] += 1
            else:
                subdomains[parse_url.scheme + "://" + parse_url.netloc] += 1


def tokenize_content(text_content):
    tokens = []
    for line in text_content:
        token_line = re.split('[^0-9A-Za-z]', line.lower())
        tokens.extend(token_line)
    return list(filter(None, tokens))



def output_to_txt():
    with open('output.txt', 'w', encoding='utf-8') as file:
        file.write("QUESTION #1" + "\n\n")
        file.write("Visited URLs:\n")
        for visited_url in visited_urls:
            file.write(visited_url + '\n')

        file.write("QUESTION #2" + "\n\n")
        file.write("\nWord Frequencies:\n")
        for word, frequency in words_dict.items():
            file.write(f"{word}: {frequency}\n")

        file.write("QUESTION #3" + "\n\n")
        file.write("\nLongest URL:\n")
        file.write(f"URL: {longest_url[0]}\n")
        file.write(f"Word Count: {longest_url[1]}\n")

        file.write("QUESTION #4" + "\n\n")
        file.write("\nSubdomains:\n")
        for subdomain, count in subdomains.items():
            file.write(f"{subdomain}: {count}\n")



def max_visits(link):

    global visit_count
    new_link = urldefrag(link)[0]

    if new_link not in visit_count:
        visit_count[new_link] = 1
    elif visit_count[new_link] < 15:
        visit_count[new_link] += 1
    else:
        return True

    return False


