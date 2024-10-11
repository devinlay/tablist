from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.selenium_manager import SeleniumManager
from selenium.webdriver.chrome.options import Options
import tempfile
import re



from reportlab.lib.styles import ParagraphStyle as PS
from reportlab.platypus import PageBreak
from reportlab.platypus.paragraph import Paragraph
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.units import cm
from reportlab.platypus import KeepTogether
from reportlab.lib import styles

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from pdftemplate import CustomDocTemplate

import multiprocessing
from multiprocessing import freeze_support
import os

import mysql.connector

db_host = os.environ.get('DB_HOST')
db_port = 25060
db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PASSWORD')
    
def fetch_playlist(link):

    pattern = re.compile(r'playlist/(.*)\?')

    playlist_id = re.search(pattern, link).group(1)
    #playlist_id = "22dT3kNU4CYV7GeHRiUCxG"
    print(playlist_id)

    client_credentials_manager = SpotifyClientCredentials()
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    results = sp.playlist_items(playlist_id = playlist_id)

    playlist_name = sp.user_playlist(user=None, playlist_id=playlist_id, fields="name")['name']

    artists = []
    songs = []
    pattern = r'(?:(?:\s+-\s+)?\s*(?:\(|\[|\{)?(?:\d{4})?\s*-?\s*(?:Remaster(?:ed)?)(?:\d{4})?\s*(?:\)|\]|\})?)(.*)|\s*-\s*(.*)|\(feat.*'
    pattern2 = r'[^a-zA-Z0-9\s]+'
    for idx, item in enumerate(results['items']):
        track = item['track']
        artists.append(track['artists'][0]['name'])
        songs.append(re.sub(pattern2, '', re.sub(pattern, '', track['name']).strip()))
        print(songs[idx], " - ", artists[idx])
    return artists, songs, playlist_name


def find_tab(i, artist, song ):
    correct_artist = artist
    correct_song = song
    print("Assigning env vars")

    print(f"Attempting connection to {db_host}:{db_port}")
    mydb = mysql.connector.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database="defaultdb"
    )

    mydbcursor = mydb.cursor()
    #instead of always scraping, check db for tab first
    #if not in database, scrape, then put it in database
    query = "SELECT tab FROM songs WHERE artist = %s AND song_title = %s"
    mydbcursor.execute(query, (correct_artist, correct_song))
    result = mydbcursor.fetchall()
    if result:
        mydbcursor.close()
        return result[0][0], correct_artist + ' - ' + correct_song
        
    else:
        mydbcursor.close()
        # try:
        print("starting driver")
        #use recursion if selenium screws up. what can go wrong?    
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--window-size=1920,1080")

        driver = webdriver.Chrome(options = options)

        driver.get('https://www.ultimate-guitar.com/')
        print("driver on website")
        #Navigating UG to get tabs    

        
        #print(to_search[0][0]+" - "+to_search[0][1])
        #search_bar = driver.find_element(By.XPATH, ".//input[@class = 'Xp1h4 BmE8Q kvpVz']") need to use wait instead for stability purposes 
        search_bar = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, ".//input[@class = 'Xp1h4 BmE8Q kvpVz']")))
        search_button = driver.find_element(By.CLASS_NAME, 'rPQkl.mcpNL.IxFbd.CcsqL.qOnLe.QlmHX')

        search_bar.send_keys(correct_artist+" - "+correct_song)

        try:
            search_button.click()
        except:
            print("stale element")

        #use waits whenever moving to a new page to ensure content has loaded
        try:
            element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@class = 'LQUZJ']")))
        except:
            return f"Sorry, unable to find tab for [{correct_artist} - {correct_song}]", f"{correct_artist} - {correct_song} - Tab not found" 
        #print(element.text)

        current_artist = element.find_element(By.XPATH, ".//div[@class= 'lIKMM lz4gy']").text
        
        if current_artist == correct_artist:
            print('artist found')

        tabs = driver.find_elements(By.XPATH, ".//div[@class= 'LQUZJ']")

        #print(tabs[0])
        acceptable_tabs = []

        pattern = rf'^{re.escape(correct_song)}(?:\s*\(ver \d+\))?\*?$'
        compiled_pattern = re.compile(pattern, re.IGNORECASE)

        #print(tabs[0].find_element(By.XPATH, ".//div[@class= 'lIKMM g7KZB']").text+" - "+ tabs[0].find_element(By.XPATH, ".//div[@class= 'lIKMM PdXKy']").text)

        if tabs[0].find_element(By.XPATH, ".//div[@class= 'lIKMM PdXKy']").text == 'Tab' and re.search(compiled_pattern,tabs[0].find_element(By.XPATH, ".//div[@class= 'lIKMM g7KZB']").text):
            acceptable_tabs.append(tabs[0])
            #print("initial tab added")



        for tab in tabs[1:]:
            try:
                artist = tab.find_element(By.XPATH, ".//div[@class= 'lIKMM lz4gy']").text #if this finds text, no further listings should be valid
            except:
                print("examining listing")
                listing_title = tab.find_element(By.XPATH, ".//div[@class= 'lIKMM g7KZB']").text
                listing_type = tab.find_element(By.XPATH, ".//div[@class= 'lIKMM PdXKy']").text
                print(listing_title+" - "+listing_type)
                if listing_type == 'Tab' and re.search(pattern, listing_title, re.IGNORECASE):
                    acceptable_tabs.append(tab)
                    print("tab added")
            else:
                print("wrong artist detected")
                break
            #main idea: identify listings that are tabs with matching title and artist
        
        best_rating = 0
        br_index = int()
        r = float(3.5)
        w = float(50)
        print(len(acceptable_tabs))
        mydbcursor = mydb.cursor()
        if len(acceptable_tabs) == 0:
            print("Sorry, no tabs were found for ["+correct_artist+" - "+correct_song+"]")
            return f"Sorry, unable to find tab for [{correct_artist} - {correct_song}]", f"{correct_artist} - {correct_song} - Tab not found"
        elif len(acceptable_tabs) == 1: 
            print("only one tab found, no sorting necessary")
            acceptable_tabs[0].find_element(By.XPATH, ".//a[@class= 'aPPf7 HT3w5 lBssT']").click()
            element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//section[@class = 'OnD3d kmZt1']"))) #tab itself
            #print(element.text)
            try:
                author = driver.find_elements(By.XPATH, "//a[@class = 'aPPf7 fcGj5']")[1].text #gets author's username
            except:
                author = "Unregistered user"
            url = driver.current_url
            textLines = [f"Source: {url}", f"Author: {author}"]
            textLines.extend(driver.find_element(By.XPATH, "//div[@class = 'P5g5A _PZAs']").text.split('\n')) #gets info like tuning, key, capo
            textLines.extend(element.text.split('\n')) #adds the tab, splitting it by line
            separator = '\n'
            textLines = separator.join(textLines)
            #print(len(textLines))
            
            
                
        else: #need to determine the best tab 
            #use bayesian probability to avoid automatically selecting a 5-star tab with only 1 rating vs 4.5 star tab with many ratings
            for idx, tab in enumerate(acceptable_tabs):
                try:
                    full_stars = len(tab.find_elements(By.XPATH, ".//span[@class= 'kd3Q7 DSnE7']"))
                    half_stars = len(tab.find_elements(By.XPATH, ".//span[@class= 'kd3Q7 RCXwf DSnE7']"))
                    rating = float(full_stars + float(half_stars*0.5))
                    num_rating = int(re.sub(',','',tab.find_element(By.XPATH, ".//div[@class= 'djFV9']").text))
                    #print(f"{rating} stars")
                    #print(f"{num_rating} reviews")
                    bayesian_rating = float((r*w + rating*num_rating)/(w+num_rating))
                    #print(bayesian_rating)
                    if bayesian_rating > best_rating:
                        best_rating = bayesian_rating
                        br_index = idx
                except:
                    pass
            #print(best_rating)
            
            acceptable_tabs[br_index].find_element(By.XPATH, ".//a[@class= 'aPPf7 HT3w5 lBssT']").click()
            element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//section[@class = 'OnD3d kmZt1']")))
            #print(element.text)
            try:
                author = driver.find_elements(By.XPATH, "//a[@class = 'aPPf7 fcGj5']")[1].text #gets author's username
            except:
                author = "Unregistered user"
            url = driver.current_url
            textLines = [f"Source: {url}", f"Author: {author}"]
            textLines.extend(driver.find_element(By.XPATH, "//div[@class = 'P5g5A _PZAs']").text.split('\n')) #gets info like tuning, key, capo
            textLines.extend(element.text.split('\n')) #adds the tab, splitting it by line
            separator = '\n'
            textLines = separator.join(textLines)
            #print(len(textLines))
            

        # order[i] = textLines
        # title[i] = correct_artist+' - '+correct_song
        
        driver.quit()
        query = "INSERT INTO songs (artist, song_title, tab) VALUES (%s, %s, %s)"
        mydbcursor.execute(query, (correct_artist, correct_song, textLines))
        mydb.commit()
        mydbcursor.close()
        return textLines, correct_artist+' - '+correct_song



        # except Exception as e:
        #     print(e)
        #     print("Selenium error occurred, trying again")
        #     driver.quit()
        #     return find_tab(correct_artist,correct_song,i)

def build_entry(title, textLines, story):
    tab_style = PS(name = 'tab',
                fontSize=10,
                fontName='Courier-Bold')
    h1 = PS(name = 'h1',
            fontSize = 10,
            fontName ='Courier-Bold')
    
    story.append(Paragraph(title, h1))
    ignore_indices = []
    textLines = re.split('\n', textLines)
    if len(textLines) == 1:
        story.append(Paragraph(textLines[0], tab_style))
        story.append(PageBreak())
        return
    for i, line in enumerate(textLines):
        if ignore_indices.__contains__(i):
            continue
        line = re.sub(r'\s', "&nbsp;", line)
        if re.match(r'^\w\|', line): 
            ignore_indices = [i+1, i+2, i+3, i+4, i+5]
            text = ""
            for j in range(i, i+6):
                textLines[j] = re.sub(r'\s', "&nbsp;", textLines[j])
                if j != i+5:
                    text+=(textLines[j]+'<br/>')
                else:
                    text+=(textLines[j])
            story.append(KeepTogether(Paragraph(text, tab_style)))
            #story.append(Spacer(20*cm, .25*cm))
        else:
            story.append(Paragraph(line, tab_style))
    story.append(PageBreak())



def main(link):
    
    with tempfile.NamedTemporaryFile(suffix='.pdf', dir = '', delete=False) as temp_file:    
        #link = input("Please paste a link to your Spotify playlist:")
        artists, songs, playlist_name = fetch_playlist(link = link)
        doc = CustomDocTemplate(temp_file.name)
        #setting up pdf
        #def main():
        toc = TableOfContents()
        
    
        story = []
        style_sheet = styles.getSampleStyleSheet()
        story.append(Paragraph(f"Tablist for {playlist_name}", style = style_sheet['title']))
        story.append(toc)
        story.append(PageBreak())


        #Fetching playlist

        to_search = list(zip(range(1, len(artists)+1), artists, songs))
        print(to_search)

        print(f"{db_host}:{db_port}")

        print("Starting process pool")
        pool = multiprocessing.Pool()
        tabs = pool.starmap(find_tab, to_search) #finish adjusting from processes to pool
        pool.close()
        pool.join()
        # manager = multiprocessing.Manager()
        # order = manager.dict()
        # title = manager.dict()
        # processes= []
        # for i, search in enumerate(to_search):
        #     p = multiprocessing.Process(target=find_tab, args=(search[0], search[1], order, title, i))
        #     p.start()
        #     processes.append(p)

        for i, tab in enumerate(tabs):
            #p.join()
            print(f"Process {i+1} has completed, now trying to append to story")
            try:
                build_entry(tab[1], tab[0], story)
                
                print(f"Process {i+1} success")
            except:
                print(f"Process {i+1} failure")
            
        if len(story)>2:
            try:
                doc.multiBuild(story)
                print(f"PDF successfully created")
            except Exception as e:
                print(f"An error occurred while building the PDF: {e}")
        return temp_file.name, playlist_name
         
    
if __name__ == "__main__":
    freeze_support()
    main()  
            
    


    
    

# results = driver.find_element(By.CLASS_NAME, 'LQUZJ' )

# print(results.text)
# auth_manager = SpotifyClientCredentials()
# sp = spotipy.Spotify(auth_manager=auth_manager)

# playlists = sp.user_playlists('spotify')
# while playlists:
#     for i, playlist in enumerate(playlists['items']):
#         print("%4d %s %s" % (i + 1 + playlists['offset'], playlist['uri'],  playlist['name']))
#     if playlists['next']:
#         playlists = sp.next(playlists)
#     else:
#         playlists = None

# def main():
#     print("Hello world")

# if __name__ == "__main__":
#     main()