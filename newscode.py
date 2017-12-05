import urllib.request, http.cookiejar
import pyrebase
import json
import ast
import xml.etree.ElementTree
from pprint import pprint
import html2text
from random import randint
import time
import datetime
from bs4 import BeautifulSoup

config = {
    "apiKey": "",
    "authDomain": "",
    "databaseURL": "",
    "storageBucket": "",
    "messagingSenderId": ""
  }

firebase = pyrebase.initialize_app(config)
db = firebase.database()
storage = firebase.storage()
h = html2text.HTML2Text()
cj = http.cookiejar.CookieJar()
sources = ['bbc-news','bloomberg','cnn','business-insider',
           'cnbc','google-news','reuters','the-huffington-post','the-new-york-times',
           'the-wall-street-journal','time','usa-today','associated-press','fortune','independent',
           'new-york-magazine','the-guardian-au','the-guardian-uk','the-telegraph','al-jazeera-english',
           'abc-news-au','breitbart-news','daily-mail','business-insider-uk',
           'financial-times','metro','newsweek','sky-news','reddit-r-all','the-economist']
article_arrays = []
h.ignore_links = True
used_array = []

global dict_db_count
dict_db_count = 'a1'

def main():
    loaded = loadArticles()
    connectArticles(loaded)
    print("done")


    while True:
        time.sleep(5)
        now = datetime.datetime.now()
        if now.minute%30 == 0 or now.minute%30 == 1:
            #print('new')
            loaded = loadArticles()
            connectArticles(loaded)
            print("DONE")




def loadArticles():
    return_array = []
    #sources = getHTMLData('https://newsapi.org/v1/sources')
    #sourcesJso = json.loads(sources.decode('utf-8'))
    for x in sources:
        data = getHTMLData('https://newsapi.org/v1/articles?source='+str(x)+'&apiKey=a7ec66ca3d314a69abb3cf4e639a68a7')
        if data != None:
            jso = json.loads(data.decode('utf-8'))
            for y in jso['articles']:
                new_article =  article(jso['source'],y['author'],y['title'],y['description'],y['url'],y['urlToImage'])
                return_array.append(new_article)
    return(return_array)


#********************************
#         CONNECTIONS
#********************************

def connectArticles(article_array):
    used = []
    cleaned_connections = []

    for x in range(len(article_array)):
        is_used = False
        first = article_array[x]
        if used != []:
            for z in used:
                if z == first:
                    is_used = True

                    break
        if is_used != "":
            used.append(first)
            top = None
            top_score = 0
            for y in range(len(article_array)-1):
                second = article_array[y]
                is_used_2 = False
                if used != []:
                    for z in used:
                        if z == second:
                            is_used_2 = True
                            break
                if is_used_2 != "":
                    if str(first.title) + str(first.description) != str(second.title) + str(second.description):
                        score = compair(convertToArray(str(first.title)+str(first.description)), convertToArray(str(second.title)+str(second.description)))
                        first_check = check_loop(first,second)
                        second_check = check_loop(second,first)
                        if score > top_score and first_check == False and second_check == False:
                            top_score = score
                            top = second
                            #first.connections.append(second)
                            #used.append(second)
            if top != None:
                first.connections.append(top)
    connections_used = []
    for y in range(len(article_array)):
        old = article_array[y].connections

        article_array[y].connections = loop_connections(article_array[y],article_array)
        article_array[y].connections = clean_articles(article_array[y].connections)
        same_count = 0



        connections_good = True
        if connections_used != []:
            for used_con in connections_used:
                #print(used_con)
                copy_count = 0
                copy_trys =  0
                for article in article_array[y].connections:
                    copy_trys = copy_trys + 1
                    for used_article in used_con:
                        #print(article.title)
                        if used_article.title == article.title:
                            copy_count = copy_count + 1
                            break
                if copy_trys > 0:
                    if (float(copy_count)/float(copy_trys))*100 >= 66:
                        connections_good = False
                        break
        if connections_good == True and len(article_array[y].connections) >= 3:
            connections_used.append(article_array[y].connections)
            cleaned_connections.append(article_array[y])
        else:
            print("OUT!!")


    countt = 0
    unix_time = time.time()
    full_send_dict = {}
    full_meta_send = {}
    used_lat = []
    used_lng = []
    for y in range(len(cleaned_connections)):
        if len(cleaned_connections[y].connections) >= 5:
            connections = cleaned_connections[y].connections
            countt = countt + 1

            best_location = get_locations(connections)

            if best_location != '':
                location = getHTMLData('https://maps.googleapis.com/maps/api/place/details/json?placeid='+str(best_location['place_id'])+'&key=AIzaSyDozWao3g9Wz4Zo3efA4_ePwBZtnVgSuDU')
                if location != None:
                    temp_article_dict = {}
                    new_dict = {}
                    jso = json.loads(location.decode('utf-8'))
                    hasResults = False
                    for key in jso:
                        if key == 'result':
                            hasResults = True
                            break
                    if hasResults: 
                        current_lat = float(jso['result']['geometry']['location']['lat'])
                        current_lng = float(jso['result']['geometry']['location']['lng'])
                        location_ready = True
                        dict_key = db.generate_key()
                        dict_key2 = db.generate_key()
                        new_dict = {}
                        meta_dict = {}
                        #print("makeing temp")
                        current_count = 0
                        for b in range(len(connections)):
                            image_path = ''
                            is_in = False
                            if len(used_array) != 0:
                                for e in range(len(used_array)):
                                    if used_array[e] == str(connections[b].author) + str(connections[b].title):
                                        is_in = True
                                        break
                            if is_in != '':
                                temp_article_dict.update({db.generate_key():{"author":connections[b].author, "title": connections[b].title, "description": connections[b].description, "url": connections[b].url, "imageUrl": connections[b].imageUrl}})
                                used_array.append(str(connections[b].author)+str(connections[b].title))
                                current_count = current_count + 1
                            if current_count == 25:
                                break
                        #print("temp done")
                        if temp_article_dict != {}:
                            new_dict.update({dict_key:{"placeName": best_location['terms'][0]['value'],"lat": current_lat, "lng": current_lng,"articles":temp_article_dict}})
                            meta_dict.update({dict_key2:{"placeName": best_location['terms'][0]['value'],"lat": current_lat, "lng": current_lng, 'articleNum': len(temp_article_dict), "key": dict_key}})
                            #print("ready to send")
                            full_send_dict.update(new_dict)
                            full_meta_send.update(meta_dict)
                        #sendToDB(new_dict)
                        #print("sent........")

    while True:
        ret = sendToDB(full_send_dict, "events")
        if ret == True:
            break
    while True:
        ret = sendToDBClean(full_send_dict, "v2Data")
        if ret == True:
            break
    while True:
        ret = sendToDB(full_meta_send, "meta")
        if ret == True:
            break
    global dict_db_count
    time_dict = {"set": dict_db_count,"time": float(time.time())}
    while True:
        ret = sendToDB(time_dict, "setTime")
        if ret == True:
            break
    if dict_db_count == 'a0':
        dict_db_count = 'a1'
    else:
        dict_db_count = 'a0'

    #print("Done")

def check_loop(first, second):
    has = False
    used = [first]
    def loop(ar):
        current = ar
        if len(current.connections) > 1:
            for x in range(len(current.connections)-1):
                is_used = False
                for z in used:
                    if z == current.connections[x+1]:
                        is_used = True
                if is_used == False:
                    used.append(current.connections[x+1])
                    loop(current.connections[x+1])
                    # print(current.connections[x+1])
                    # print(second)
                    if current.connections[x+1] == second:
                        has = True

    loop(first)
    return(has)




def clean_articles(ar):
    used = []
    for article in ar:
        is_used = False
        for z in used:
            if z == article:
                is_used = True
                break
        if is_used == False:
            used.append(article)
    return(used)


def loop_connections(article,full):
    full_path = compiled_connections()
    full_path.list.append(article)
    used = [article]
    def loop(ar):
        current = ar
        if len(current.connections) > 1:
            for x in range(len(current.connections)-1):
                is_used = False
                for z in used:
                    if z == current.connections[x+1]:
                        is_used = True
                if is_used == False:
                    full_path.list.append(current.connections[x+1])
                    used.append(current.connections[x+1])
                    loop(current.connections[x+1])
    loop(article)
    return(odd_man_out(full_path.list,full))


def odd_man_out(list_,full):
    common = []
    used = []
    print("commom")

    for x in range(len(list_)):
         first = convertToArray(list_[x].title+str(list_[x].title))
         for y in range(int(float(len(first)))):
             word_count = 1
             trys = 1
             first_word = first[y]
             is_used = False
             for z in used:
                 if z == first_word:
                     is_used = True
             if is_used == False:
                 used.append(first_word)
                 if len(first_word) >= 5:
                     for w in range(len(list_)):
                         second = convertToArray(list_[w].title+str(list_[w].title))
                         if first != second:
                             trys = trys + 1
                             if does_have(second,first_word) == True:
                                 word_count = word_count + 1

                     if trys > 0:
                        if (float(word_count)/float(trys))*100 >= 66:
                             common.append(first_word)
    print(common)
    #print(common)


    return_array = []
    if len(common) >= 2:
        for z in range(len(list_)):
            good_array = []
            list_to_array = convertToArray(list_[z].title+str(list_[z].title))
            good = True
            correct_count = 0
            for w in range(len(common)):
                if does_have(list_to_array,common[w]) == True:
                    correct_count = correct_count + 1

            if (float(correct_count)/float(len(common)))*100 >= 66:
                return_array.append(list_[z])
        if len(common) >= 2:
            for q in range(len(full)):
                good_array = []
                list_to_array = convertToArray(full[q].title)
                good = True
                correct_count = 0
                for w in range(len(common)):
                    if does_have(list_to_array,common[w]) == True:
                        correct_count = correct_count + 1

                if (float(correct_count)/float(len(common)))*100 >= 66:
                    return_array.append(full[q])


        return(return_array)
    else:
        return([])



def does_have(title, word):
    for x in title:
        if makeAlphaOnly(x) == word:
            return(True)
    return(False)


class compiled_connections():
    def __init__(self):
        self.list = []


def compair(first,second):
    correct_count = 0
    trys = 0
    for x in first:
        if len(str(x)) >= 4:
            one = x
            for y in second:
                if len(str(y)) >= 4:
                    two = y
                    trys = trys + 1
                    if one == two:
                        correct_count = correct_count + 1
    if trys > 0:
        return((float(correct_count)))
    else:
        return(0)



def disectHTML(html,key):
    if html != None:
        soup = BeautifulSoup(html)
        for elem in soup.findAll(['style', 'script', '[document]', 'head', 'title']):
            elem.extract()
        new = ''.join(soup.findAll(text=True))

        count = 0
        temp_word = ""
        full_str = ""
        for x in range(len(new)):
            if new[x:x+1] != '\n':
                count = count + 1
                temp_word = temp_word + new[x:x+1]
            elif count > 40:
                full_str = full_str + temp_word
                temp_word = ""
            else:
                temp_word = ""
        full_str = full_str + temp_word
        return(full_str)
    else:
        return(None)
    # array = convertToArray(str(html))
    # refreshed_text = ''
    # for x in array:
    #     if len(str(x)) < 10 and str(x)[0:1].isalpha():
    #         refreshed_text = refreshed_text + str(x) + ' '
    # return(refreshed_text)

def convertToArray(data_str):
    word = ''
    array = []
    for x in range(len(data_str)):
        if data_str[x:x+1] == " " or data_str[x:x+1] == "-":
            array.append(word)
            word = ""
        elif data_str[x:x+1].isalpha():
            word = word + data_str[x:x+1]

    array.append(word)
    return array

def makeAlphaOnly(str_):
    return_str = ''
    for x in range(len(str_)):
        if str_[x:x+1].isalpha():
            return_str = return_str + str_[x:x+1]
    return(return_str)



def getHTMLData(url):
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders.append(('User-Agent','Mozilla/5.0'))
    data = None
    try:
        data = opener.open(url).read()
    except Exception as e:
        #print("html error")
        pass
    return(data)


class article:
    def __init__(self,source,author,title,description,url,imageUrl):
        self.source = source
        self.author = author
        self.title = title
        self.description = description
        self.url = url
        self.imageUrl = imageUrl
        #self.url_data = (disectHTML(getHTMLData(url),'<div'))
        self.connections = [self]


def sendToDB(full_dict, key):
    try:
        global dict_db_count
        db.child(key).child(str(dict_db_count)).remove()
        db.child(key).child(str(dict_db_count)).update(full_dict)
        return(True)
    except Exception as e:
        return(False)

def sendToDBClean(full_dict, key):
    try:
        global dict_db_count
        db.child(key).remove()
        db.child(key).update(full_dict)
        return(True)
    except Exception as e:
        return(False)









#********************************
#         LOCATION
#********************************


def update_term_list(locations_in_terms,terms):
    if len(locations_in_terms) == 0:
        for term in terms:
            locations_in_terms.append([term['value'],1])
    else:
        for term in terms:
            term_has = False
            for old_term in locations_in_terms:
                if term['value'] == old_term[0]:
                    old_term[1] = old_term[1] + 1
                    term_has = True
                    break
            if term_has == False:
                locations_in_terms.append([term['value'],1])

def convertLocationToArray(data_str):
    word = ''
    array = []
    for x in range(len(data_str)):
        if data_str[x:x+1] == " ":
            array.append(word)
            word = ""
        else:
            word = word + data_str[x:x+1]

    array.append(word)
    return array


def makeAlphaOnly(str_):
    return_str = ''
    for x in range(len(str_)):
        if str_[x:x+1].isalpha():
            return_str = return_str + str_[x:x+1]
    return(return_str)

def isAllAlpha(str_):
    for x in range(len(str_)):
        if str_[x:x+1].isalpha() == False:
            return(False)
    return(True)


def get_locations(article_list):
    full_str = ""
    full_title = ""

    for art in article_list:
        art.url_data = (disectHTML(getHTMLData(art.url),'<div'))
        full_str = full_str + str(art.url_data)
        full_title = full_title + str(art.title)

    def update_term_list(locations_in_terms,terms,type_):
        if len(locations_in_terms) == 0:
            for term in terms:
                locations_in_terms.append([term['value'],1,type_])
        else:
            for term in terms:
                term_has = False
                for old_term in locations_in_terms:
                    if term['value'] == old_term[0]:
                        old_term[1] = old_term[1] + 1
                        term_has = True
                        break
                if term_has == False:
                    locations_in_terms.append([term['value'],1,type_])



    start = False
    temp_word = ""
    temp_word_plus_next_word = ''
    possible_array = []
    title_array = []
    data_array = convertToArray(full_title)
    space = 0
    multiplyer = 1
    while True:
        first = ""
        first_count = 1
        for x in range(multiplyer):
            if first == "":
                first = str(first + data_array[space + x])
            else:
                first = str(first + " " + data_array[space + x])
        space_2 = space
        multiplyer_2 = multiplyer
        if len(first) >= 3 and first[x:x+1].istitle():
            while True:
                second = ""
                for y in range(multiplyer_2):
                    if second == "":
                        second = str(second + data_array[space_2 + x + y])
                    else:
                        second = str(second + " " + data_array[space_2 + x + y])
                if first == second:
                    first_count = first_count + 1
                space_2 = space_2 + 1
                if space_2 >= len(data_array) - multiplyer_2:
                    break
            if first_count >= len(article_list):
                title_array.append(first)

        space = space + 1
        if space >= len(data_array) - multiplyer:
            space = 0
            multiplyer = multiplyer + 1
        if multiplyer >= 3:
            break


    next_word_start = False

    for x in range(len(full_str)):
        if full_str[x:x+1].istitle():
            if full_str[x-3:x-1] == 'in' or full_str[x-4:x-1].lower() == 'the' or full_str[x-3:x-1] == 'at' or full_str[x-3:x-1] == 'to' or full_str[x-3:x-1] == 'of' or full_str[x-5:x-1] == 'from' or full_str[x-5:x-1] == 'a':
                    start = True

        if start == True:
            if full_str[x:x+1] != ' ':
                temp_word = temp_word + full_str[x:x+1]
            elif full_str[x+1:x+2].istitle():
                temp_word = temp_word + ' '
            elif full_str[x+1:x+3] == "of":
                temp_word = temp_word + 'of'

            elif full_str[x+1:x+2] == '.' and full_str[x+2:x+3] != ' ':
                temp_word = temp_word + full_str[x:x+1]
            else:
                # possible_array.append(temp_word)
                # temp_word = ""
                # start = False
                size_good = True
                check_word_size_array = convertToArray(temp_word)
                for word in check_word_size_array:
                    if len(word) > 100:
                        size_good = False
                        break
                if len(temp_word) < 100 and size_good == True and len(temp_word) >= 2 and (temp_word != "Coachella" or temp_word != "Coachella..."):
                    possible_array.append(temp_word)
                next_word_start = True
                temp_word = ""
                start = False


    order_of_repitition = []

    for loc in range(len(possible_array)-1):
        first = possible_array[loc]
        count = 1
        for loc2 in range(len(possible_array)-1):
            second = possible_array[loc2]
            if first == second:
                count = count + 1
        if len(order_of_repitition) < 1:
            order_of_repitition.append([first,count])
        else:
            for order in range(len(order_of_repitition)):
                    if count > order_of_repitition[order][1]:
                        temp_array = []
                        for quick in range(len(order_of_repitition)):
                            if order == quick:
                                temp_array.append([first,count])
                                temp_array.append(order_of_repitition[quick])

                            else:
                                temp_array.append(order_of_repitition[quick])

                        order_of_repitition = temp_array
                        break
                    elif order_of_repitition[order][0] == first:
                        break

                    elif order == len(order_of_repitition)-1:
                        order_of_repitition.append([first,count])
                        break
    cleaned_up_order = []

    if len(order_of_repitition) > 0:
        max_ = float(order_of_repitition[0][1])*float(0.15)
        for order in order_of_repitition:
            amount = 0
            if order[1] >= float(max_):
                cleaned_up_order.append(order)
        order_of_repitition = cleaned_up_order

        #print("cleaned up order")
    print(order_of_repitition)


    final_array = []








    title_order_of_repitition = []

    for loc in range(len(title_array)-1):
        first = title_array[loc]
        count = 0
        for loc2 in range(len(title_array)-1):
            second = title_array[loc2]
            if first == second:
                count = count + 1
        if len(title_order_of_repitition) < 1:
            title_order_of_repitition.append([first,count])
        else:
            for order in range(len(title_order_of_repitition)):
                    if count > title_order_of_repitition[order][1]:
                        temp_array = []
                        for quick in range(len(title_order_of_repitition)):
                            if order == quick:
                                temp_array.append([first,count])
                                temp_array.append(title_order_of_repitition[quick])

                            else:
                                temp_array.append(title_order_of_repitition[quick])

                        title_order_of_repitition = temp_array
                        break
                    elif title_order_of_repitition[order][0] == first:
                        break

                    elif order == len(title_order_of_repitition)-1:
                        title_order_of_repitition.append([first,count])
                        break








    ##print(order_of_repitition)
    #if len(order_of_repitition) > 40:
        #del order_of_repitition[40:len(order_of_repitition)-1]


# https://maps.googleapis.com/maps/api/place/autocomplete/json?input=UK&location=0,0&radius=20000000&key=AIzaSyDozWao3g9Wz4Zo3efA4_ePwBZtnVgSuDU

    countrys = []
    cities_array = []
    large_area_array = []
    establishment_array = []
    saved_list = []
    locations_in_terms = []
    best_location = None
    best_location_score = 0
    best_location_amount = 0
    title_locations = []





    final_list = []

    possible_list = []
    possible_count = 0
    for possible in order_of_repitition:
        temp_str = ""
        #possible[0] = makeAlphaOnly(possible[0])
        if possible[0] == 'US' or possible[0] == 'U.S.':
            possible[0] = 'United States'
        if possible[0] == 'Supreme Court':
             possible[0] = possible[0] + ' United States'
        for x in range(len(possible[0])):
            if possible[0][x:x+1] != ' ':
                temp_str = temp_str + possible[0][x:x+1]
            else:
                temp_str = temp_str + '+'
        caps_check = True
        if len(possible[0]) >= 3:
                x = 0
                if possible[0][x:x+1].isupper() or possible[0][x:x+1].isalpha() == False:
                    if possible[0][x+1:x+2].isupper() or possible[0][x:x+1].isalpha() == False:
                        if possible[0][x+2:x+3].isupper() or possible[0][x:x+1].isalpha() == False:
                            caps_check = False
        if len(temp_str) >= 3 and caps_check == True and temp_str.lower() != "business+insider" and temp_str.lower() != "obama" and temp_str.lower() != "march" and temp_str.lower() != "april" and temp_str.lower() != "bbc" and temp_str.lower() != "web+analytics" and \
         temp_str.lower() != "supreme+court" and temp_str.lower() != "coachella" and temp_str.lower() != "catch" and temp_str.lower() != "earth":
            location = getHTMLData('https://maps.googleapis.com/maps/api/place/autocomplete/json?input='+str(temp_str)+'&location=0,0&radius=20000000&key=AIzaSyDozWao3g9Wz4Zo3efA4_ePwBZtnVgSuDU')
            if location != None:
                jso = json.loads(location.decode('utf-8'))
                if len(jso["predictions"]) > 0:
                    #for a in range(len(jso['predictions'])):
                    possible_correct_locations = []
                    for a in range(len(jso["predictions"])):
                        total_same = 0
                        total_same_trys = 0
                        used_secondary_terms = []
                        possible_array = convertLocationToArray(possible[0])

                        has_count = 0
                        term_array = convertLocationToArray(jso["predictions"][a]['terms'][0]['value'])
                        # for x in possible_array:
                        #     first = makeAlphaOnly("the "+x)
                        #     if does_have(term_array, first) == True:
                        #         has_count = has_count + 1

                        #if (float(has_count)/float(len(term_array)))*100 < 66:
                            #term_array = convertLocationToArray(jso["predictions"][a]['terms'][0]['value'])
                        has_count = 0
                        if len(possible_array) != 0:
                            for x in possible_array:
                                first = makeAlphaOnly(x)
                                if does_have(term_array, first) == True:
                                    has_count = has_count + 1
                            #POSSIBLE GLITCH below
                            #MIGHT CAUSE LCOATION CONFUTION
                            # if (float(has_count)/float(len(term_array)))*100 < 66:
                            #     has = 0
                            #     term_array = convertLocationToArray(jso["predictions"][a]['description'])
                            #     for x in possible_array:
                            #         first = makeAlphaOnly(x)
                            #         if does_have(term_array, first) == True:
                            #             has_count = has_count + 1
                        if (float(has_count)/float(len(term_array)))*100 >= 66 and (jso["predictions"][a]['terms'][0]['value']).lower() != "april":
                            temp_location_score = 0
                            if best_location_score == 0:
                                best_location = jso["predictions"][a]['terms']
                                if jso["predictions"][a]['types'][0] == 'country':
                                    best_location_score = 1
                                elif jso["predictions"][a]['types'][0] == 'administrative_area_level_1':
                                    temp_location_score = 2
                                elif jso["predictions"][a]['types'][0] == 'locality':
                                    temp_location_score = 3
                                else:
                                    best_location_score = 4
                                    best_location_amount = possible[1]
                                update_term_list(locations_in_terms,jso["predictions"][a]['terms'],jso["predictions"][a]['types'][0])
                            else:
                                if jso["predictions"][a]['types'][0] == 'country':
                                    temp_location_score = 1
                                elif jso["predictions"][a]['types'][0] == 'administrative_area_level_1':
                                    temp_location_score = 2
                                elif jso["predictions"][a]['types'][0] == 'locality':
                                    temp_location_score = 3
                                else:
                                    temp_location_score = 4
                                if temp_location_score > best_location_score:
                                    best_location = jso["predictions"][a]['terms']
                                    best_location_score = temp_location_score
                                    best_location_amount = possible[1]

                            possible_correct_locations.append([jso["predictions"][a],possible,temp_location_score,len(order_of_repitition)-possible_count])
                            saved_list.append([jso["predictions"][a],possible,temp_location_score,len(order_of_repitition)-possible_count])
                    if len(possible_correct_locations) != 0:
                        #final_list.append(possible_correct_locations[0])
                        possible_list.append(possible_correct_locations)
                    # elif len(possible_correct_locations) != 0:
                    #     possible_list.append(possible_correct_locations)



                            #break

        possible_count = possible_count + 1

    bias_list = []
    checked_list = []
    used_locations = []
    # for saved in saved_list:
    #     good = False
    #     for saved2 in saved_list:
    #         if saved != saved2:
    #             if saved[0]['terms'][0]['value'] == saved2[0]['terms'][0]['value']:


    for possible_saved in possible_list:
        best_score = 0
        best = None
        for saved in possible_saved:
            score = 0
            #for saved2 in saved_list:
            #if saved != saved2 and saved[0]['terms'][0]['value'] != saved2[0]['terms'][0]['value']:
            if len(saved[0]['terms']) > 1:
                # for pos in order_of_repitition:
                # if saved[0]['terms'][1]['value'] == saved2[0]['terms'][0]['value']:
                #         score = score + 1
                #         break
                for term in range(len(saved[0]['terms'])-1):
                    for pos in order_of_repitition:
                        if saved[0]['terms'][term+1]['value'] == makeAlphaOnly(pos[0]):
                            score = score + 1
                            break


            # if score > 0:
            #     bias_list.append([saved,score+saved[3]])
            # print(score)
            # print(saved[0]['terms'])
            if score > best_score:
                best_score = score
                best = saved
        if best == None:
            best = possible_saved[0]
        #if best != None:
        # print("best group")
        # print(best_score)
        # print(best[0]['terms'])
        final_list.append(best)
        update_term_list(locations_in_terms,best[0]['terms'], best[0]['types'][0])


    print(len(saved_list))




    print(order_of_repitition)
    print("")
    print(locations_in_terms)

    for x in article_list:
        print(x.title)
        print(x.url)
        print("")
    print("*____________________________*")

    top_saved_score = 0
    top_saved = ['',['',0]]
    over_2_on = 1
    for common in locations_in_terms:
        if common[1] >= 2:
            over_2_on = 2
            break
    for saved in final_list:
     score_correct = saved[3] #+ saved[2]
     score_trys = 0
     for term in saved[0]['terms']:
         old_score = score_correct
         for common in locations_in_terms:
             if common[1] >= 2:
                 score_trys = score_trys + common[1]
                 if common[0] == term['value']:
                     score_correct = score_correct + common[1]
                     break
        #  for saved2 in final_list:
        #      if saved != saved2:
        #          if term["value"] == saved2[0]['terms'][0]['value']:

         if score_correct != old_score:
             pass
             #break
     if score_correct > top_saved_score:
         top_saved_score = score_correct
         top_saved = saved
    print(top_saved)

    return(top_saved[0])

main()
