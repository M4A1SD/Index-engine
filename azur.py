# Manager Page: Daniel & Arthur - This was long and painful
# Ideas for the future : 1. maybe stem the words before cleaning the text from
# words with special characters, not sure what happens if we have a word like "microsoft's"
# 3. fuck i think i forgot oh yeah do the front end
"""
-----!!!IMPORTANT!!!------
To anyone working with the index, the structure is:
{
  term:{
    docs:{
      "id1":cnt_in_doc
    },
    count: cnt
  }
}
  -term is a word
  -docs is a json dictionary list or whatever you wanna fucking call it of doc
   ids and the amount of times that word appears in them
  -count is the count the word appears in the entire site

This message may or may not have been written while I was druink
"""

"""
Plan: scrape ms azure's allowed pages
run through all the pages in ms azure, check if they're still in ms azure and if
they're allowed in robots.txt, if so download and stem the content.
"""
import requests
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin

class RobotsChecker:
  """
  This class is used to check if a given url is allowed in the robots.txt file
  of a given website.
  """
  def __init__(self,base_url):
    self.base_url = base_url
    self.robots_url = urljoin(base_url,"/robots.txt")
    self.robot_parser = RobotFileParser()
    self.load_robots_txt()

  def load_robots_txt(self):
    try:
      response = requests.get(self.robots_url)
      if response.status_code == 200:
        self.robot_parser.parse(response.text.splitlines())
      else:
        print(f"Couldn't fetch robots.txt. Status code {response.status_code}")
    except Exception as e:
      print(f"Error loading robots.txt: {e}")

  def is_allowed(self, url):
    return self.robot_parser.can_fetch("*",url)

  def is_in_site(self,url):
    if not url.startswith(('http','https')):
      full_url = urljoin(self.base_url,url)
      return full_url.startswith(self.base_url)
    return url.startswith(self.base_url)

"""
Cell 2: Download all allowed relevant MS AZURE links.
"""
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
from nltk.stem import PorterStemmer

class AzureSearchEngine:
  def __init__(self):
    self.base_url = "https://azure.microsoft.com"
    self.pages = []
    self.word_locations = defaultdict(list)  # word -> [(page_id, frequency), ...]
    self.stop_words = {'a', 'an', 'the', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
    self.robots_checker = RobotsChecker(self.base_url)
    self.stemmer=PorterStemmer()

  def stem_word(self,word):
    return self.stemmer.stem(word)

  def is_link_in_pages(self, link):
    # Remove trailing slash if present
    normalized_link = link.rstrip('/')
    for page in self.pages:
        # Compare normalized URLs
        if page['url'].rstrip('/') == normalized_link:
            return False
    return True

  def fetch_azure_pages(self):
    try:
      response = requests.get(self.base_url) # Get a response from Azure link
      response.raise_for_status()
      soup = BeautifulSoup(response.text, 'html.parser') # parse html from hompage
      links = soup.find_all('a') # Get all links from anchor tags
      visited_urls = set()
      for i, link in enumerate(links):
        url = link['href']
        # Normalize URL by removing trailing slash
        normalized_url = url.rstrip('/')
        if normalized_url in visited_urls:
          continue
        visited_urls.add(normalized_url)
        # iterate through all the links we found on the homepage, add all those that are still in ms azure's site
        if not url.startswith('http'): # I assume that if the link doesn't start with http then it means it stays on the site (relative links)
          url=self.base_url + url.lstrip('/') # Why do we add microsoft azure's base url and what's url.lstrip?
        #grab the content for each url we find
        if self.robots_checker.is_in_site(url) and self.robots_checker.is_allowed(url):
          page_content = self.fetch_page_content(url)
        else:
          continue
        # So if the page has any content, we add it to the data structure we save all the pages's content and id.
        if page_content:
          self.pages.append({
              'id': i + 1,
              'url': url,
              'content': page_content
          })

      return True

    except Exception as e:
      print(f"Error fetching pages: {str(e)}")
      return False

  def fetch_page_content(self, url): # Fetches a page's content as string from a given url
    try:
      response = requests.get(url) # send a request to the url
      response.raise_for_status()
      soup = BeautifulSoup(response.content,"html.parser") # pars the content using beautiful soup html parser
      content = soup.get_text()
      content = self.clean_text(content)
      # Stem the content
      stemmed_words = []
      words = content.split(' ')
      for word in words:
        stemmed_words.append(self.stem_word(word))
      stemmed_content = ' '.join(stemmed_words)
      return stemmed_content
    except requests.exceptions.RequestException as e: # In case we run into issues, print accordingly and return nothing.
      print(f"Error fetching page content: {str(e)}")
      return None

  def clean_text(self, text):
    """Remove unwanted characters, numbers, and stopwords from the text."""
    # Remove non-alphabetic characters using a regular expression
    clean_text = re.sub(r'[^a-zA-Z\s]', '', text)

    # Convert to lowercase for uniformity
    clean_text = clean_text.lower()

    # Remove stopwords
    words = clean_text.split()
    words = [word for word in words if word not in self.stop_words]

    return ' '.join(words)

"""
Step 3: Create inverted index from page contents
For each document in the previous step, use the add_document function to create an inverted index.
"""
# ---------------------------------------------------------------------------------------------------- INDEX SERVICE ---------------------------------------------------------------------------------------------
import uuid
import re
# index_service.py
class IndexService:
    def __init__(self):
        self.documents = {}
        self.index = {}
        self.AzureSearchEngine = AzureSearchEngine()

    # Creates/Recreates the index and saves it
    def restore_index(self):
        self.AzureSearchEngine.fetch_azure_pages()
        for page in self.AzureSearchEngine.pages:
          self.add_document(page)
        print("Index restored!")
        return True

    # Receives a doc's content
    def add_document(self, doc_data):
        """Add a document to the index"""
        # Giving each doc a unique id
        doc_id = str(uuid.uuid4())
        # in the document array, we place the document data and the id
        self.documents[doc_id] = {**doc_data, 'id': doc_id}

        # Create inverted index
        # it's not stemmed here so if you want stemming gotta add it.
        words = doc_data['content'].lower().split()
        for word in words:
            if word not in self.index:
                self.index[word] = {}
                self.index[word]['count'] = 1
                self.index[word]['docs'] = {}
                self.index[word]['docs'][self.documents[doc_id]['url']] = 1

            elif self.documents[doc_id]['url'] not in self.index[word]['docs']:
                self.index[word]['docs'][self.documents[doc_id]['url']] = 1
                self.index[word]['count'] += 1

            elif self.documents[doc_id]['url'] in self.index[word]['docs']:
              self.index[word]['count'] += 1
              self.index[word]['docs'][self.documents[doc_id]['url']] += 1 # need to check if it's the word's first time in the doc itself and not first time in the site

        return self.documents[doc_id]

    def get_document(self, doc_id):
        """Retrieve a document by ID"""
        return self.documents.get(doc_id)

    def search_word(self, word):
        """Find documents containing a word"""
        word = word.lower()
        return list(self.index.get(word, set()))

# ------------------------------------------------------------------------------------------------------------- Database Service -------------------------------------------------------------------------------------------------------------------
from firebase import firebase
import json
import time
"""
This class is used to communicate with the Firebase Database.
"""
class DatabaseService:
  def __init__(self):
    self.db_url = "https://natalibraudecloud-default-rtdb.europe-west1.firebasedatabase.app/"
    self.FBconn = firebase.FirebaseApplication(self.db_url, None)
    self.IndexService = IndexService()
    self.chunkCount = 0

  def sort_index(self):
    for term in self.IndexService.index:
      self.IndexService.index[term]['docs'] = dict(sorted(self.IndexService.index[term]['docs'].items(), key=lambda x: x[1], reverse=True))

  def restore_index(self):
    self.IndexService.restore_index()

  def upload_docmap(self):
    try:
      for doc in self.IndexService.documents:
        self.FBconn.put('/DocMap2/',doc,json.dumps(self.IndexService.documents[doc]['url']))

      #self.FBconn.put('/DocMap/','docmap',json.dumps(self.IndexService.documents))
      print("Document map uploaded to database.")
    except Exception as e:
        print(f"Error uploading document map: {e}")

  def download_docmap(self):
    try:
      docmap = self.FBconn.get('/DocMap/','docmap')
      self.IndexService.documents = json.loads(docmap)
      print("Document map downloaded from database.")
    except Exception as e:
        print(f"Error downloading document map: {e}")

  def upload_index(self):
    self.sort_index()
    for term in self.IndexService.index:
      self.FBconn.put('/Index/',term,json.dumps(self.IndexService.index[term]))
      if term == 'australia':
        print(f"{term}:{self.IndexService.index[term]}")

  def download_index(self):
    """Download the index from the database"""
    i = 0
    while True:
      chunk = self.FBconn.get('/Index/',f'chunk_{i}')
      print(chunk)
      if chunk is None:
        break
      chunk = json.loads(chunk)
      self.IndexService.index.update(chunk)
      i += 1
    print("Index downloaded from database.")

# Now we'll try downloading the index and presenting it by count
import pandas as pd
from IPython.display import display
db = DatabaseService()
db.restore_index()
db.upload_index()
#db.upload_docmap()
#db.download_docmap()
df = pd.DataFrame.from_dict(db.IndexService.documents, orient='index')
#df.sort_values(by='count',ascending=False)
display(df)
"""
import pandas as pd
from IPython.display import display
db = DatabaseService()

db.download_index()
print(db.IndexService.index)
df = pd.DataFrame.from_dict(db.IndexService.index, orient='index')
df.sort_values(by='count',ascending=False)
display(df)
"""