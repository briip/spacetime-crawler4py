import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
from collections import defaultdict

MAX_URL_CONTENT_LENGTH = 5 * 1024 * 1024  # one megabyte

visited_urls = []
words_dict = defaultdict(int)
longest_url = ('', 0)
subdomains = defaultdict(int)
visit_count = defaultdict(int)  # Map paths to times visited

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
    except Exception as e:
        print(f'Error getting: {url}: {e}')

    return links


def is_valid(url):
    try:
        parsed = urlparse(url)
        pattern = re.compile(r"(?:http?://|https?://)?(?:\w+\.)?(?:ics|cs|informatics|stat)\.uci\.edu/")
        # pattern = re.compile(r'^https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]+)')

        if re.match(pattern, url.lower()):  # Checks if URL matches the requirements


            # Avoid pdfs and zip attachments
            if "zip-attachment" in parsed.path.lower():
                return False
            
            if "pdf" in parsed.path:
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
        return False
    except TypeError:
        print("TypeError for ", parsed)
        raise


def extract_content(url, resp):
    try:
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')

        tokens_list = tokenize_content(soup.text)

        if len(tokens_list) > 0:
            filtered_tokens = [token for token in tokens_list if token not in STOP_WORDS]
            global longest_url
            if len(filtered_tokens) > longest_url[1]:
                longest_url = (url, len(filtered_tokens))
            for token in filtered_tokens:
                words_dict[token] += 1

            parse_url = urlparse(url)
            subdomain_key = f"{parse_url.scheme}://{parse_url.netloc}"

            if "ics.uci.edu" in parse_url.netloc:
                    subdomains[subdomain_key] = subdomains.get(subdomain_key, 0) + 1

    except Exception as e:
        print(f'Error extracting content from {url}: {e}')


def tokenize_content(text):

    global STOP_WORDS
    tokens = []
    for line in text.split('\n'):
        # lower case
        words = re.findall(r'[A-Za-z0-9]+(?:[\.\'\’\‘][A-Za-z0-9]+)*', line.lower())
        words = [word for word in words if (word and word not in STOP_WORDS and len(word) > 1)]
        tokens.extend(words)
    return tokens



def max_visits(link):
    new_link = urldefrag(link)[0] if urldefrag(link)[0] else link
    if new_link not in visit_count:
        visit_count[new_link] = 1
    elif visit_count[new_link] < 15:
        visit_count[new_link] += 1
    else:
        return True
    return False


def output_to_txt():
    with open('output.txt', 'w', encoding='utf-8') as file:
        file.write("QUESTION #1" + "\n\n")
        file.write(f"Visited URLs: {len(visited_urls)}\n")
        for visited_url in visited_urls:
            file.write(visited_url + '\n')

        file.write("QUESTION #2" + "\n\n")
        file.write("\nWord Frequencies:\n")
        sorted_words = sorted(words_dict.items(), key=lambda x: x[1], reverse=True)

        for word, frequency in enumerate(sorted_words[:50], start=1):
            file.write(f"{word}: {frequency}\n")

        file.write("QUESTION #3" + "\n\n")
        file.write("\nLongest URL:\n")
        file.write(f"URL: {longest_url[0]}\n")
        file.write(f"Word Count: {longest_url[1]}\n")

        file.write("QUESTION #4" + "\n\n")
        file.write(f"\nSubdomains in the ics.uci.edu domain: {len(subdomains)}\n")
        sorted_subdomains = sorted(subdomains.items())
        for subdomain, count in sorted_subdomains:
            file.write(f"{subdomain}: {count}\n")
