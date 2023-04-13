# scrape-20minutes

# A Scraper for the French news website 20 Minutes 

This script extracts articles published within a specific time period. It uses asynchronous programming to speed up the process, and the text extraction itself is
done using trafilatura. The article text,as well as additional meta data is then stored in a xml file. Additionally, the script also produces a csv file containing the number 
of articles extracted for each day, the number of tokens and the category the article belongs to (based on the URL). 
