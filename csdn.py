from urllib import request
import math
from http import cookiejar
import re
from bs4 import BeautifulSoup
import pdfkit
import time
import random
import os
import sqlite3  
import multiprocessing
import threading
from PyPDF2 import PdfFileReader, PdfFileWriter
import sys

class CSDN(object):
    def __init__(self, username):
        super (CSDN, self).__init__()

        self.username = username;
        self.baseUrl = 'https://blog.csdn.net/%s/article/list/' % username;



        self.conn = sqlite3.connect('csdn.db')
        self.cursor = self.conn.cursor()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS %s( 
            id         INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            url        TEXT,
            title      TEXT,
            srcHtml    BLOB
            ) 
            ''' % self.username) 

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS %s_Index( 
            id         INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            url        TEXT,
            indexHtml    BLOB
            ) 
            ''' % self.username) 

        self.articleNumber = 0

        self.merge = PdfFileWriter()

    def __del__(self):
        print('结束了')
        self.conn.commit()
        self.conn.close()


    def insert2Db(self, url, title, srcHtml, cleanedHtml):
        print(url)
        self.cursor.execute('''select count(*) from "%s" where url = "%s"''' % (self.username, url))
        if not self.cursor.fetchone()[0]:
            self.cursor.execute('INSERT INTO %s (url, title, srcHtml)  VALUES (?,?,?)'  % (self.username,), ( url, title, memoryview(srcHtml.encode(encoding="utf-8"))) );


    def getArticleByUrl(self, url, articleName):
        while True:
            try:
                html = request.urlopen(url).read().decode('utf-8');
                break;
            except:
                print("获取 <%s> 时,发生故障! %s\n" % (articleName, url)) 
                time.sleep(random.randint(5, 10))

        data = html

        return data

    def getArticlesInPage(self, html):
        soup = BeautifulSoup(html, "lxml")

        articleList = soup.find(class_ = 'article-list').find_all(class_ = 'article-item-box')

        for article in articleList:
            article= article.find('a')

            href = article.get('href')
            title = article.get_text("|", strip=True)[2:]

            self.cursor.execute('''select count(*) from "%s" where url = "%s"''' % (self.username, href))
            if not self.cursor.fetchone()[0]:
                srcHtml = self.getArticleByUrl(href, title)
                cleanedData = ''#self.cleanHtmlData(srcHtml)

                self.insert2Db(href, title, srcHtml, cleanedData)
            else:
                #print('文章"%s"已经存在' % (title, ))
                pass

    def getPageByIndex(self, pageIndex):
        url = self.baseUrl + str(pageIndex)

        self.cursor.execute('''select count(*) from "%s_Index" where url = "%s"''' % (self.username, url))
        if  self.cursor.fetchone()[0]:
            #print("爬过了%s" % url)
            return True




        # print(url)

        # headers = {
        #     'Host': 'blog.csdn.net',
        #     'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
        # }

        # request = urllib.request.Request(url=url, headers=headers, method='GET')
        # response = self.opener.open(request)
        # print(response)
        # html = response.read().decode('utf-8');
        #html = html.decode('utf-8');

        while True:
            try:
                html = request.urlopen(url).read().decode('utf-8');
                break;
            except:
                print("当前第%d页,发生故障!\n" % pageIndex) 
                time.sleep(5)
            
        soup = BeautifulSoup(html, "lxml")
        #print(soup.prettify())

        if html.find('class="no-data') != -1 and html.find('<h6>空空如也</h6>') != -1:
            return False;
        else:

            self.cursor.execute('INSERT INTO %s_Index (url, indexHtml)  VALUES (?,?)'  % (self.username,), ( url, memoryview(html.encode(encoding="utf-8"))) );

            self.getArticlesInPage(html)
            return True;


    def cleanHtmlData(self, html):
        cleanedData = ''
        soup = BeautifulSoup(html, "lxml")
        # article_title_box = soup.find(class_='article-title-box')
        # article_info_box = soup.find(class_='article-info-box')
        # article_content = soup.find(id = 'article_content')
        # article_bar_bottom = soup.find(class_='article-bar-bottom')
        blog_content_box = soup.find(class_='blog-content-box')

        cleanedData += '''
            <!DOCTYPE html>
            <html lang="zh-CN">
                <head>
                    <meta charset="UTF-8">
                    %s
                <link rel="stylesheet" href="https://csdnimg.cn/release/phoenix/template/css/detail-60a2c245da.min.css">
                <link rel="stylesheet" href="https://csdnimg.cn/release/phoenix/themes/skin3-template/skin3-template-88717cedf2.min.css">

                <script type="text/javascript">
                var username = "";
                </script>

                <script src="https://csdnimg.cn/public/common/libs/jquery/jquery-1.9.1.min.js" type="text/javascript"></script>

                <!-- 新版上报 -->
                <!-- 新版上报end -->
                <link rel="stylesheet" href="https://csdnimg.cn/public/sandalstrap/1.3/css/sandalstrap.min.css"> 
                </head>
                <body>    
        
                    <link rel="stylesheet" href="https://csdnimg.cn/release/phoenix/template/css/blog_code-c3a0c33d5c.css">
                    <div class="container clearfix pt0" id="mainBox">
        ''' % (soup.title.prettify())


        cleanedData += '<main style="width: 100%;">'
        cleanedData += blog_content_box.prettify()
        # cleanedData += article_title_box.prettify()
        # cleanedData += article_info_box.prettify()
        # cleanedData += article_content.prettify()
        # cleanedData += article_bar_bottom.prettify()
        cleanedData += '''<div class="recommend-box">
                            <div style="background: #fff; border: dashed 1px #666; padding-left: 1em; padding-top: 1em; padding-bottom: 1em;">
                                <span style="font-size: 0.8em; font-weight: bold;">
                                    此PDF由<a style="color:#0000ff" href="http://www.github.com/spygg"  target="_blank">spygg</a>生成,请尊重原作者版权!!!
                                    <br/>
                                    我的邮箱:liushidc@163.com
                                </span>
                                </div> 
                        </div>
                    </main>
      
                </div>

            <script>
                var recommendCount = 0;
                var articleTit = "";
                var articleId = "";
                var commentscount = 0;

                //1禁止评论，2正常
                var commentAuth = 1;
                //百度搜索
                var baiduKey = "";
                var needInsertBaidu = "";
            </script>
            <script src="https://csdnimg.cn/release/phoenix/template/js/detail-effe72036e.min.js"></script>
            </body>
        </html>'''
        

        cleanedData = cleanedData.replace('class="hide-article-box', 'style="display:none;" class="hide-article-box')
        cleanedData = cleanedData.replace('class="float-right', '')
        return cleanedData


    def doConvert(self, id, html):
        #pdfkit.from_file("dhtml/%s.html" % fileName, 'pdf/%s.pdf' % fileName) 
        if not os.path.exists('pdf'):
            os.mkdir('pdf')

        if not os.path.exists('pdf/%d.pdf' % id ):
            pdfkit.from_string(html, 'pdf/%d.pdf' % id )


    def doMerge(self):
        pageIndex = 0
        for i in range(0, self.articleNumber):
            pdf = PdfFileReader(open('pdf/%d.pdf' % (self.articleNumber - i), "rb"))

            pageCount = pdf.getNumPages() 
            title = pdf.getDocumentInfo().title.replace(' - CSDN博客', '')
            #print(title, pageCount)
            self.merge.appendPagesFromReader(pdf)
            self.merge.addBookmark(title, pageIndex)
            pageIndex += pageCount

        #设置最大递归深度,不然报错
        sys.setrecursionlimit(5000)
        self.merge.write(open("%s.pdf" % self.username, "wb"))
        sys.setrecursionlimit(1000)

    def startThreadPool(self):

        processList = []

        #降序排列
        self.cursor.execute('select id, srcHtml from %s' % (self.username))

        result = self.cursor.fetchall()
        self.articleNumber = len(result)
        print("一共 %d篇文章" % self.articleNumber)

        for (id, srcHtml) in result:
            cleanedHtml = self.cleanHtmlData(srcHtml.decode('utf-8'))
            #process = multiprocessing.Process(target = self.doConvert, args = (id, cleanedHtml))
            process = threading.Thread(target = self.doConvert, args = (id, cleanedHtml))
            processList.append(process)

        k = 0
        while k < len(processList):
            temProcessList = []
            for i in range(0, 30):
                processList[k].start()
                temProcessList.append(processList[k])
                #print('启动%d' % k)
                k = k + 1
                if k >= len(processList):
                    break

            for tmpProcess in temProcessList:
                tmpProcess.join()


        

if __name__ == '__main__':

    #username = 'spygg'
    username = 'leixiaohua1020'
    csdn = CSDN(username)

    i = 1;
    while(True):
        pageNumber = csdn.getPageByIndex(i)
        print('正在获取第%d页文章索引页.' % i)
        if pageNumber:
            pass
        else:
            break;

        i = i + 1;


    csdn.startThreadPool()

    csdn.doMerge()

    
