Reddit Scraper
=======

Run `__main__.py` or simply `python .` from inside the directory. This will run the GUI.
Once you have configured your settings using the GUI, running `python scrape.py` will
use your saved settings. You can then easily schedule the scraper to run daily.

Alternately, you may manually create `config.json` and then run `scrape.py`.

Reddit Scraper allows you to scrape the top images (or other file formats) 
from selected subreddits into selected directories on your machine.
You may configure how many files to scrape, what extensions to include,
which subreddits to scrape from, and which directories to write to.

The GUI needs a lot of work but this is essentially usable. 

Uses Python Reddit API Wrapper: https://github.com/praw-dev/praw

```% pip install praw```

One other dependancy:

```% pip install requests```

Contact me: chrisbarker@cmu.edu

