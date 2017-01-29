from bs4 import BeautifulSoup
from urllib2 import urlopen, Request, HTTPError, URLError
import os
import sys
import re
import csv

reload(sys)
sys.setdefaultencoding('utf-8')

BASE_URL = 'http://urmyeyes.blogbus.com'


def get_page_count():
    page = urlopen(BASE_URL)
    soup = BeautifulSoup(page, 'html.parser')
    t = soup.find('div', {'class': 'pageNavi'})
    return int(re.findall(r'\b\d+\b', t.text.split()[0])[0])


def find_all_blog_links(url):
    page = urlopen(url)
    soup = BeautifulSoup(page, 'html.parser')
    blog_links = [title.a['href'] for title in soup.find_all('h2', attrs={'class': 'news-title'})]
    return blog_links


class Blog:
    link = None
    blog_soup = None
    title = None
    category = None
    paragraphs = []
    imageLinks = []
    created_at = None
    cmtBodies = []
    cmtAuthors = []
    is_encrypted = None

    def __init__(self, url):
        self.read_individual_blog(url)
        self.is_encrypted = self.get_blog_title_and_category()
        if not self.is_encrypted:
            self.get_timestamp()
            self.get_post_body()
            self.get_comments()

    def read_individual_blog(self, blog_link):
        self.link = blog_link
        page = urlopen(blog_link)
        self.blog_soup = BeautifulSoup(page, 'html.parser')

    def get_blog_title_and_category(self):
        post_header = self.blog_soup.find('div', attrs={'class': 'postHeader'})
        if not post_header:
            return True
        titles = post_header.h2.text.split('-')
        self.title = ''.join(titles[0].split('.')[0].strip().split('/'))
        self.category = titles[1].strip()
        print 'working on blog ', self.title, self.category
        return False

    def get_post_body(self):
        body = self.blog_soup.find('div', attrs={'class': 'postBody'})
        ps = body.find_all('p')
        self.imageLinks = []
        self.paragraphs = []
        for p in ps:
            if p.img:
                self.imageLinks.append(p.img['src'])
            else:
                self.paragraphs.append(p.text)

    def get_timestamp(self):
        self.created_at = self.blog_soup.find('span', attrs={'class': 'time'}).text

    def get_comments(self):
        cmt_soup = self.blog_soup.find('ul', attrs={'id': 'comments'})
        if not cmt_soup:
            return
        self.cmtBodies = [body.text for body in cmt_soup.find_all('div', attrs={'class': 'cmtBody'})]
        self.cmtBodies += [body.text for body in cmt_soup.find_all('div', attrs={'class': 'reCmtBody'})]
        self.cmtAuthors = [author.text.split('|')[0] for author in cmt_soup.find_all('span', attrs={'class': 'author'})]
        print ['cmtAuthor: ' + cmtauthor for cmtauthor in self.cmtAuthors]
        print ['cmtbody: ' + cmtbody for cmtbody in self.cmtBodies]

    def save_blog_content(self):
        if self.is_encrypted:
            return
        if not os.path.isdir(self.category):
            os.mkdir(self.category)
        file_name = self.category + '/' + self.title + '.txt'
        print 'file name ----- ', file_name
        if os.path.isfile(file_name):
            print 'file ', file_name, ' exists'
        else:
            blog_file = open(file_name, 'wb')
            for p in self.paragraphs:
                blog_file.write(p)
                blog_file.write('\n')
            blog_file.write('\n\n\n')
            blog_file.write(self.created_at)
            blog_file.write('\n\n\n')
            for i in range(0, len(self.cmtAuthors)):
                blog_file.write(self.cmtAuthors[i])
                blog_file.write(': ')
                blog_file.write(self.cmtBodies[i])
                blog_file.write('\n')
            blog_file.close()

        i = 0
        print self.imageLinks
        for imageLink in self.imageLinks:
            image_file_path = self.category + '/' + self.title + '-' + str(i) + '.jpg'
            if os.path.isfile(image_file_path):
                print 'image ', image_file_path, ' exists'
            else:
                try:
                    print 'about to download ', imageLink
                    img_request = Request(imageLink)
                    img_data = urlopen(img_request).read()
                    output = open(image_file_path, 'wb')
                    print 'output is ', output
                    output.write(img_data)
                    output.close()
                except HTTPError:
                    print 'download ' + image_file_path + ' failed'
                except URLError:
                    print 'download ' + image_file_path + ' failed'
                else:
                    print 'download ' + image_file_path + ' failed for no reason'
            i += 1
        print 'Finished save blog content'


all_blog_links = []
total_page_number = get_page_count()
all_page_links = [BASE_URL + '/index_' + str(index) + '.html' for index in range(1, total_page_number + 1)]

if os.path.isfile('blog_links.csv'):
    with open('blog_links.csv', 'rb') as csv_file:
        csv_reader = csv.reader(csv_file)
        all_blog_links = [''.join(row) for row in csv_reader]
else:
    for page_link in all_page_links:
        print 'adding ', page_link
        all_blog_links += find_all_blog_links(page_link)
    link_file = open('blog_links.csv', 'wb')
    csv_writer = csv.writer(link_file)
    csv_writer.writerows(all_blog_links)

for link in all_blog_links:
    print 'working on blog -> ', link
    blog = Blog(link)
    blog.save_blog_content()