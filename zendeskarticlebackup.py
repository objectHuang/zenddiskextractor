import os
import datetime
import csv
 
import requests
from bs4 import BeautifulSoup
import shutil

session = requests.Session()
session.auth = credentials
 
zendesk = 'https://e1helpcenter.zendesk.com'
language = 'en-us'
 
date = datetime.date.today()
export_path = os.path.join(str(date), language)
 

log = []
 
endpoint = zendesk + '/api/v2/help_center/en-us/articles.json'.format(locale=language.lower())
count = 0
batchsize = 10
while endpoint:
 
    response = session.get(endpoint)
    if response.status_code != 200:
        print('Failed to retrieve articles with error {}'.format(response.status_code))
        exit()
    data = response.json()
 
    for article in data['articles']:
        if article['body'] is None:
            continue
          

        pathsuffix = count//batchsize
        export_path = os.path.join('articleexport', str(pathsuffix))
        if not os.path.exists(export_path):
            os.makedirs(export_path)

        tree=BeautifulSoup(article['body'], 'html.parser')
        images = tree.find_all('img')
        for image in images:
            src = image['src']
            if src[:4] != 'http': continue
            response = session.get(src, stream=True)
 
            file_name = src.split('/')[-1]
            image_dir = src.split('/')[-2]
            image_path = os.path.join(export_path,'data', image_dir)
            if not os.path.exists(image_path):
                os.makedirs(image_path)
            #file_name = str(article['id']) + '_' + image_dir + '_' + file_name
            with open(os.path.join(image_path, file_name), mode='wb') as f:
                for chunk in response.iter_content():
                    f.write(chunk)
            print('{image} copied!'.format(image=file_name))
 
            image['src'] = src.replace('https://helpcenter.ef.com/hc/article_attachments/', '')
 
        title = '<h1>' + article['title'] + '</h1>'
        filename = '{id}.html'.format(id=article['id'])    
        with open(os.path.join(export_path,'data', filename), mode='w', encoding='utf-8') as f:
            f.write(title + '\n' + str(tree))
 
        print('{id} copied!'.format(id=article['id']))
 
        log.append((article['title'], article['title'], filename.replace('.html',''), 'data/' + filename))

        count = count + 1

        if count%batchsize == 0:
            with open(os.path.join(export_path, 'Article.csv'), mode='wt', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(('Title','Summary','URLName','Question__c'))
                for article in log:
                    writer.writerow(article)
            shutil.make_archive('article' + str(pathsuffix), 'zip', export_path)
 
    endpoint = data['next_page']    
    
    
 