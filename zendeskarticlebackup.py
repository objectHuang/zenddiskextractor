import os
import datetime
import csv
import time
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
logfull = []
endpoint = zendesk + '/api/v2/help_center/en-us/articles.json'.format(locale=language.lower())
count = 0
batchsize = 40
downloadcount = 0
while endpoint:
    if not(downloadcount%50):
        time.sleep(10)
        session = requests.Session()
        session.auth = credentials

    response = session.get(endpoint)
    downloadcount = downloadcount + 1
    if response.status_code != 200:
        print('Failed to retrieve articles with error {}'.format(response.status_code))
        exit()
    data = response.json()
 
    for article in data['articles']:
        if article['body'] is None and not(article['draft'] == 'true') and not(article['outdated']=='true'):
            continue
            count = count + 1
        
        pathsuffix = count//batchsize
        export_path = os.path.join('articleexport', str(pathsuffix))
        if not os.path.exists(export_path):
            os.makedirs(export_path)
            os.makedirs(os.path.join(export_path, 'data'))

        tree=BeautifulSoup(article['body'], 'html.parser')
        title = '<h1>' + article['title'] + '</h1>'
        filename = '{id}.html'.format(id=article['id'])
        images = tree.find_all('img')
        for image in images:
            src = image['src']
            if src[:28] != 'https://helpcenter.ef.com/hc': continue
            
            if not(downloadcount%50):
                time.sleep(5)
                session = requests.Session()
                session.auth = credentials
            response = session.get(src, stream=True)
            downloadcount = downloadcount + 1
            imagefile_name = src.split('/')[-1]
            image_dir = src.split('/')[-2]

            image_path = os.path.join(export_path,'data', filename.replace('.html', ''))
            if not os.path.exists(image_path):
                os.makedirs(image_path)

            newimagefile_name = image_dir + '_' + imagefile_name
            #file_name = str(article['id']) + '_' + image_dir + '_' + file_name
            with open(os.path.join(image_path, newimagefile_name), mode='wb') as f:
                for chunk in response.iter_content():
                    f.write(chunk)
            print('{image} copied!'.format(image=newimagefile_name))
            print(image['src'])
            image['src'] = filename.replace('.html', '') + '/' + newimagefile_name + ''
            print(image['src'])
 
        sectionid = article['section_id']
        secctioniurl = zendesk + '/api/v2/help_center/en-us/sections/' + str(sectionid) + '.json'
        #e1helpcenter.zendesk.com/api/v2/help_center/en-us/sections/201934601.json
        print(secctioniurl)
        session = requests.Session()
        session.auth = credentials
        sectionresponse = session.get(secctioniurl)
        
        section = sectionresponse.json()
        if 'section' in section: 
            sectionname = section['section']['name']
            sectiontype = section['section']['sorting']
            sectionposition = section['section']['position']

            categoryid = section['section']['category_id']
            categoryurl = zendesk + '/api/v2/help_center/en-us/categories/' + str(categoryid) + '.json'
            session = requests.Session()
            session.auth = credentials
            categoryresponse = session.get(categoryurl)

            category = categoryresponse.json()
            categoryname = category['category']['name']
            categoryposition = category['category']['position']
        else:
            sectionname = 'unknown'
            sectiontype = 'unknown'
            sectionposition = 0

            categoryid = 0
            categoryurl = zendesk + '/api/v2/help_center/en-us/categories/' + str(categoryid) + '.json'
            session = requests.Session()
            session.auth = credentials
            
            categoryname = 'unknown'
            categoryposition = 0
        
        

        with open(os.path.join(export_path,'data', filename), mode='w', encoding='utf-8') as f:
            f.write(title + '\n' + str(tree))

        print('{id} copied!'.format(id=article['id']))

        log.append((article['title'], article['title'], filename.replace('.html',''), 'data/' + filename))
        logfull.append((article['title'], article['title'], filename.replace('.html',''), 'data/' + filename, sectionid, sectionposition,sectionname, sectiontype, categoryid,categoryposition,categoryname))

        count = count + 1

        if count%batchsize == 0:
            with open(os.path.join(export_path, 'Article.csv'), mode='wt', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(('Title','Summary','URLName','Article_Content__c'))
                for article in log:
                    writer.writerow(article)
                log = []
            
            # with open(os.path.join(export_path, 'AllFields.csv'), mode='wt', encoding='utf-8') as f:
            #     writer = csv.writer(f)
            #     writer.writerow(('Title','Summary','URLName','Article_Content__c', 'sectionid', 'sectionposition','sectionname','sectiontype','categoryid','categorypoistion','categoryname'))
            #     for article in logfull:
            #         writer.writerow(article)
            #     logfull = []
            
            shutil.make_archive('article' + str(pathsuffix), 'zip', export_path)
 
    endpoint = data['next_page'] 
 