"""Scrape images linked to from specified subreddits."""

try:
    import praw
except ImportError:
    print "Unable to find praw. see https://github.com/praw-dev/praw"
    raise

from time import sleep
import urllib
import requests
import urlparse
import re
import os
import sys
import datetime
import settings as settings_
import string

_REDDIT_API_SLEEP_TIME = 2.50
_VALID_CHARS = frozenset(''.join(("-_.() ", string.ascii_letters, string.digits)))

def sanitize(s, default_name="image"):
    sanitized = ''.join(c for c in s if c in _VALID_CHARS)
    return sanitized[:0xFF] if sanitized else default_name # Use default if string is empty.

def unique(filename):
    """Return a guaranteed-unique version of a given filename."""
    if not os.path.exists(filename):
        return filename
    else:
        parts = filename.split('.')
        parts.insert(-1, '%d') # Put a number before the extension.
        filename_fmt = '.'.join(parts)
        num = 0
        while os.path.exists(filename_fmt % num):
            num += 1
        return filename_fmt % num

def download_and_save(url, filename, directory_data):
    """Save the data at a given URL to a given local filename."""
    data = urllib.urlopen(url).read()
    if is_duplicate(data,  directory_data):
        return
    with open(filename, mode='wb') as output:
        output.write(data)

def is_duplicate(data, directory_data):
    h = hash(data)
    if h in directory_data:
        with open(directory_data[h]) as fid:
            existing_data = fid.read()
        return existing_data == data
    return False

def scan_hash(dirname):
    sub_items = os.listdir(dirname)
    filenames = (os.path.join(dirname, f) for f in sub_items)
    filenames = (f for f in filenames if not os.path.isdir(f))
    data = {}
    for f in filenames:
        with open(f) as fid:
            data[hash(fid.read())] = f
    return data

def fetch_image(submission, url, directory):
    # votes = '+%s,-%s' % (submission.ups, submission.downs)
    extension = url.split('.')[-1]
    title = sanitize(submission.title) # Remove illegal characters
    if title.endswith('.'): title = title[:-1] # Fix foo..jpg
    local_filename = unique(os.path.join(directory, '%s.%s' % (title, extension)))
    directory_data = scan_hash(directory)
    download_and_save(url, local_filename, directory_data)

def get_submissions(subred, limit, timeframe):
    methname = 'get_top_from_%s' % timeframe
    if hasattr(subred, methname):
        return getattr(subred, methname)(limit=limit)
    else:
        raise ValueError('Unrecognized timeframe: %s' %  timeframe)

def is_imgur_image(url):
    return bool(type_of_imgur_url(url))

def type_of_imgur_url(url):
    parsed_url = urlparse.urlparse(url)
    if parsed_url.netloc == "i.imgur.com":
        return "direct"
    if parsed_url.netloc == "imgur.com":
        if "/a/" in parsed_url.path:
            return "album"
        else:
            return "indirect"
    return None

def scrape(settings, include_sub=None, include_dir=None, timeframe='day', limits=None):
    r = praw.Reddit(user_agent=settings.user_agent)
    for grouping in settings.groupings:
        if ((include_dir is not None and grouping.name not in include_dir) or
            not grouping.enabled):
            continue
        for subreddit in grouping.subreddits:
            if ((include_sub is not None and subreddit.name not in include_sub) or not subreddit.enabled):
                continue
            dirname = grouping.dirname_for(subreddit)

            if not os.path.exists(dirname):
                os.makedirs(dirname)

            extensions = set(subreddit.file_types)
            subred = r.get_subreddit(subreddit.name)
            submissions = get_submissions(subred, limits, timeframe)

            count = 0
            for submission in submissions:
                if is_imgur_image(submission.url):
                    
                    parsed_url = urlparse.urlparse(submission.url)
                    image_identifier = parsed_url.path[1:]
                    image_type = type_of_imgur_url(submission.url)

                    if image_type == "direct":
                        fetch_image(submission, submission.url, dirname)
                        count += 1

                    elif image_type == "indirect":
                        image_extention = ".jpg" # seems to work everytime even though we don't really know the original image format
                        constructed_url = "http://i.imgur.com/" + image_identifier + image_extention
                        fetch_image(submission, constructed_url, dirname)
                        count += 1

                    elif image_type == "album":
                        # Fetch all the images from the album?
                        noscript_url = "http://imgur.com/" + image_identifier + "/noscript"

                        try:
                            response = requests.get(url=noscript_url).text
                            # Read in the images now so we can get stats and stuff:
                            images = re.findall('<img src="(\/\/i\.imgur\.com\/([a-zA-Z0-9]+\.(jpg|jpeg|png|gif)))(\?[0-9]+)?"', response)
                            for url in images:
                                constructed_url = "http:" + url[0]
                                fetch_image(submission, constructed_url, dirname)
                                count += 1
                        except:
                            print "Album request failed for submission " + noscript_url

                    elif image_type == None:
                        # Some form of imgur link we dont handle yet...galleries?
                        print "couldn't find image file for url %s", submission.url
                else:
                    if any(submission.url.lower().endswith(ext.lower()) for ext in extensions):
                        fetch_image(submission, submission.url, dirname)
                        count += 1
                    else:
                        print "couldn't find image file for url %s", submission.url

            yield count

            sleep(_REDDIT_API_SLEEP_TIME) # Avoid offending the Reddit API Gods!

    yield True

if __name__ == '__main__':
    settings = settings_.Settings()
    list(scrape(settings))
