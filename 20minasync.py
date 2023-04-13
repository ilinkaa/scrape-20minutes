import re
import requests 
from urllib.request import urlopen
from bs4 import BeautifulSoup as BS
import pandas as pd
import urllib
import validators
import trafilatura
from url_parser import parse_url, get_url, get_base_url
from collections import Counter
import numpy as np 
from nltk import word_tokenize
import time
import aiohttp
from aiohttp import ClientTimeout
import asyncio
import xml.etree.ElementTree as ET
from nltk import word_tokenize


prefix = 'https://www.20minutes.fr/archives'
base = "https://www.20minutes.fr"

hdr = { "User-Agent": "Chrome/114.0.0.0 (Windows NT 10.0; Win64; x64)" }


def is_date_correct(date1, date2):
    """ Check if two dates are valid """
    a = True
    if re.match(r'[0-9]{4}\-[0-9]{2}\-[0-9]{2}',str(date1)) and re.match(r'[0-9]{4}\-[0-9]{2}\-[0-9]{2}',str(date2)):
        
        a = True
    else:
        a = False
    return a 




def gen_dates(date1, date2):
    """ Generates list of dates for the time period entered to access the URLs """
    dates = ""
    bool1 = is_date_correct(date1, date2)
    if bool1 == True:    
        mydates = pd.date_range(date1, date2).tolist()
        dates = []
        for i in mydates:
            cc = i.strftime('%Y/%m-%d')
            dates.append(cc)
    else: 
        print("Falsches Datum. Bitte Datum im 'YYYY-MM-DD' Format eingeben ")    
    return dates


def verify_links(dates):
    """ Validates links """
    linkje = prefix + "/"+dates
    if validators.url(linkje):
        return linkje
    else:
        print("not valid")    


temp = gen_dates("2020-10-01","2020-10-03")
liens_essai = []
for i in temp:
    liens_essai.append(verify_links(i))

print(liens_essai)

# ecrire les fonctions pour 
# un lien journalier, obtenir les liens du jour 

async def other_write(session,i):
    """ Awaits url and extract text from article with Trafilatura """
    try:
        article = await session.get(i, headers = hdr, timeout = 30)
        print(article.url)
        regexp = re.compile(r'-direct-')
        if regexp.search(str(article.url)):
            pass
        else:
            articleText = trafilatura.extract(await article.text(), output_format="xml",favor_precision=True, tei_validation = True)
        #print(articleText)
        return articleText
    except Exception as e:
        print(e)


async def get_daily(session,i):
    """ Fetches list of URLs for articles on a specific day for each day inside the time period """
    try:
        pageContent = await session.get(i, headers = hdr, timeout = 30)
        counter = 0
        pourt = BS(await pageContent.text(), "lxml")
        articlesThatDay =[]
        for ultag in pourt.find_all('ul',{'class':'spreadlist'}):
                for litag in ultag.find_all("a", href = True):
                    link = base + litag["href"]
                    counter = counter +1
                    txt = await other_write(session,link)
                    #print(txt)
                    #print(counter)
                    if txt != None:
                        articlesThatDay.append(txt)
        return articlesThatDay
       
    except Exception as e:
        print(e)




def processlist(list_of_lists:list):
    """ Gets number of articles collected on a given day """
    list_seule = sum(list_of_lists,[])
    res=Counter(list_seule)
    return res 

def tokenize(stri):
    """ Number of tokens collected on a given day """
    return len(word_tokenize(stri, language="french"))


def process_xml(texte):
    """ Writes text to xml """
    
    data = '<X>' + texte + '</X>'
  
    df = pd.DataFrame(columns=['Date','Articles', 'Tokens'])
    bs_data = BS(data, 'xml')
    docs = bs_data.find_all("doc")
    
    dates = []
    for i in docs:
        if i.get("date") not in dates:
            dates.append(i.get("date"))
    df["Date"] = dates
    df = df.set_index("Date")        
    dict_date = dict()
    dict_cats = dict()
    for i in docs: 
        date = i.get("date")
        if date not in dict_date.keys():
            dict_date[date] = 1
        else:
            dict_date[date] = dict_date[date] +1 
    
    for i in dict_date.keys():
    
        df.at[i, "Articles"] = dict_date[i]
        b_name = bs_data.find_all('doc', {'date':str(i)})
        list_cat_day = []
        for el in b_name:
            dict_cats = ()
            cat_temp = el.get("source")
            cat = re.findall(r".fr\/([^\/]*)\/",str(cat_temp))
            list_cat_day.append(cat)
        
        daily_cats = processlist(list_cat_day)
        for j in daily_cats.keys():
            df.at[i,j] = daily_cats[j]
        df1 = df.fillna(value=np.nan)
        df1= df1.fillna(int(0))

        big_liste = []
    for date in dict_date.keys():
        tokensNum = 0 
        doc = bs_data.find_all('doc', {'date':str(date)})
        main_dialy = []
        # main dans articles MAIN = 1 ARTICLE 
        for j in doc:
            # main dans articles MAIN = 1 ARTICLE 
            ps = j.find_all("main")
            # paragraphes dans UN ARTICLE
            len_paragrpah = []
            for i in ps:
                temp = i.find_all("p")
                for pourt in temp:
                    len_paragrpah.append(tokenize(pourt.text))

            main_dialy.append(sum(len_paragrpah))
        tokensNum = tokensNum+1
        daily_toks = sum(main_dialy)
        df.at[date, "Tokens"] = daily_toks
 
    return data, df 




async def main():
    """Retrieves article text asynchronously"""
    data = []
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in liens_essai:
                tasks.append(get_daily(session,i))
        htmls = await asyncio.gather(*tasks)
        data.extend(htmls)
        count = 0
        try:
            txt = ""
            for o in data:
                for j in o:
                    count = count+1
                    txt = txt + j
            return txt
            
        except Exception as e:
            print(e)

start = time.time()
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
txt = asyncio.run(main())

# takes xml file w/ articles and processes it 

new_txt , dataf = process_xml(txt)
with open("20MinutesFINAL.txt","w",encoding ='utf-8') as p:
    p.write(new_txt)
    
dataf.to_csv("data20minutes.csv")
print("--- %s seconds ---" % (time.time() - start))

         

