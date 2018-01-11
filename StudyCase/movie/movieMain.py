import requests
from bs4 import BeautifulSoup
import pymysql
import random
import string
import time

def getMovieURL():

    # 构建会话
    cookies = prepareCookies()
    headers = prepareHeads()

    '''
    将豆瓣单部电影的URL保存到数据库中
    '''
    db = getDbConnect()

    roopNum = 0

    try:
        for year in range(1960,1980):
            pageStart = 0

            while True:
                home_url = generateMovieBriefUrl(year,pageStart)
                print("home_url is {0}".format(home_url))
                r = requests.get(home_url, cookies=cookies, headers=headers)

                strContent = r.content.decode()

                #如果当前也为最后一页，则退出循环
                ifLastPage = isLastPage(strContent)

                if ifLastPage:
                    # 如果当前也为最后一页，则退出循环
                    break
                else:
                    # 如果当前不是最后一页，增加起始位置
                    pageStart = pageStart + 20

                doubanMovieUrl = parseDoubanMovieUrlFromBrief(strContent)

                for url in doubanMovieUrl:
                    saveMovieUrl(url,db)

                time.sleep(0.5)

                roopNum = roopNum + 1

                if roopNum%5 == 0:
                    # 更新cookie
                    cookies = prepareCookies()

        db.commit()

    except:
        # 如果发生错误则回滚
        db.rollback()

        # 关闭数据库连接
    db.close()

    return


def isLastPage(htmlContent):
    '''
    从豆瓣列表页中解析获得电影页面url
    '''
    soup = BeautifulSoup(htmlContent, "html.parser")

    # 取得编剧信息
    attrsTitle = soup.find("a",class_="nbg")
    if attrsTitle == None:
        result = True
    else:
        result = False

    return result
#
# else:
#     aContent = soup.find("p", text="豆瓣上暂时还没有人给电影标注")
#     if aContent is not None:
#         result = True
#     else:
#         result = False
#
# return result


# aContent = soup.find("p",text = "没有找到符合条件的电影")
    #
    # if aContent is not None:
    #     result = True
    # else:
    #     aContent = soup.find("p", text="豆瓣上暂时还没有人给电影标注")
    #     if aContent is not None:
    #         result = True
    #     else:
    #         result = False
    #
    # return result

def parseDoubanMovieUrlFromBrief(htmlContent):
    '''
    从豆瓣列表页中解析获得电影页面url
    '''
    soup = BeautifulSoup(htmlContent, "html.parser")

    aContent = soup.find_all("a","nbg")

    hrefConteng = [value['href'] for value in aContent]

    return hrefConteng

def generateMovieBriefUrl(year,pageStart):
    '''
    根据年份和页起始位置生成豆瓣的目录页url
    '''
    return "https://movie.douban.com/tag/" + str(year) + "?start="+str(pageStart)+"&type=T"


def prepareHeads():
    '''
    准备请求的header内容
    '''

    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36'}

    return headers

def prepareCookies():
    '''
    准备请求的cookie内容
    '''
    #注：bid值可能需要定时跟换

    bidValue = "bid=%s" % "".join(random.sample(string.ascii_letters + string.digits, 11))

    cookies = {"Cookie":'ll="108296"; _ga=GA1.2.740277333.1448884744; _gat=1; {0}; ps=y; '.format(bidValue)}
    print(cookies)

    # 如果上面代码无效，可以试试以下代码
    # cookies = requests.cookies.RequestsCookieJar()
    # cookies.set('bid', 'ehjk9OLdwha', domain='.douban.com', path='/')
    # cookies.set('11', '25678', domain='.douban.com', path='/')



    return cookies

def generateTestData():

    home_url = "https://movie.douban.com/tag/1860?start=20&type=T"

    # 构建会话
    session = requests.Session()
    # 　登录后才能访问的url
    r = session.get(home_url)

    strContent = r.content.decode()

    # print(strContent)

    session.close()

    return strContent

def getDataFromMoviePage(pageUrl):
    '''
    从单个电影页面中解析电影数据
    '''

    # 构建会话
    cookies = prepareCookies()
    headers = prepareHeads()

    # 　登录后才能访问的url
    r = requests.get(pageUrl,cookies=cookies,headers=headers)
    # print(r.cookies)

    strContent = r.content.decode()

    # print(strContent)

    soup = BeautifulSoup(strContent, "html.parser")

    #取得片名信息
    movieName = soup.find("span", property="v:itemreviewed")
    if movieName == None:
        movieNameReturn = None
    else:
        movieNameReturn = movieName.text

    #取得导演信息
    directNameArr = soup.find_all("a", rel="v:directedBy")
    if directNameArr == None:
        directDict = None
    else:
        directDict = {collectCelebrityKey(directName['href']): directName.text for directName in directNameArr}

    # 取得上映年信息
    year = soup.find("span", class_="year")
    if year == None:
        yearReturn = None
    else:
        yearReturn = year.text.replace("(","").replace(")","")

    # 取得编剧信息
    attrsTitle = soup.find("span", text="编剧")
    if attrsTitle == None:
        attrsDict = None
    else:
        attrsValueContent = attrsTitle.next_sibling.next_sibling
        attrsValueArr = attrsValueContent.find_all("a")
        attrsDict = {collectCelebrityKey(attrsValue['href']): attrsValue.text for attrsValue in attrsValueArr}

    # 取得主演信息
    actorTitle = soup.find("span", text="主演")
    if actorTitle == None:
        actorDict = None
    else:
        actorValueContent = actorTitle.next_sibling.next_sibling
        actorValueArr = actorValueContent.find_all("a")
        actorDict = {collectCelebrityKey(actorValue['href']): actorValue.text for actorValue in actorValueArr}

    # 取得类型信息
    genreArr = soup.find_all("span", property="v:genre")
    if genreArr == None:
        genreDict = None
    else:
        genreDict = [genre.text for genre in genreArr]

    #### 取得国家信息
    countryTitle = soup.find("span", text="语言:")
    if countryTitle == None:
        countryValue = None
    else:
        countryValue = countryTitle.previous_sibling.previous_sibling.previous_sibling

    # 取得语言信息
    languageTitle = soup.find("span", text="语言:")
    if languageTitle == None:
        languageValue = None
    else:
        languageValue = languageTitle.next_sibling

    # 取得上映时间信息
    initialReleaseDateArr = soup.find_all("span", property="v:initialReleaseDate")
    if initialReleaseDateArr == None:
        initialReleaseDateDict = None
    else:
        initialReleaseDateDict = [initialReleaseDate.text for initialReleaseDate in initialReleaseDateArr]

    # 取得片长信息
    runtime = soup.find("span", property="v:runtime")
    if runtime == None:
        runtimeReturn = None
    else:
        runtimeReturn = runtime.text

    # 取得又名信息
    anotherNameTitle = soup.find("span", text="又名:")
    if anotherNameTitle == None:
        anotherName = None
    else:
        anotherName = anotherNameTitle.next_sibling

    ### 取得IMDB链接信息
    anotherNameTitle = soup.find("span", text="又名:")
    if anotherNameTitle == None:
        imdbLinkReturn = None
    else:
        imdbLink = anotherNameTitle.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling
        imdbLinkReturn = imdbLink["href"]

    # 取得海报信息
    post = soup.find("img", rel="v:image")
    if post == None:
        postReturn = None
    else:
        postReturn = post['src'].replace("s_ratio_poster","l")

    # 取得豆瓣得分信息
    average = soup.find("strong", property="v:average")
    if average == None:
        averageReturn = None
    else:
        averageReturn = average.text

    # 取得评价人数信息
    votes = soup.find("span", property="v:votes")
    if votes == None:
        votesReturn = None
    else:
        votesReturn = votes.text

    return (movieNameReturn,directDict,yearReturn,attrsDict,actorDict,genreDict,countryValue,languageValue,initialReleaseDateDict,runtimeReturn,anotherName,imdbLinkReturn,postReturn,averageReturn,votesReturn)

def collectCelebrityKey(celebrityContent):
    '''
    从豆瓣演职人员link中提取演职人员id
    '''
    return celebrityContent.replace("celebrity","").replace(r"/","")

def saveMovieUrl(movieUrl,db):

    '''
    将豆瓣单部电影的URL保存到数据库中
    '''
    # 使用 cursor() 方法获取操作游标
    cursor = db.cursor()

    # SQL 插入语句
    sql = "INSERT INTO MOVIEURLLIST(MOVIE_URL) VALUES ('" + movieUrl + "')"

    # 执行 sql 语句
    cursor.execute(sql)

    return

def getDbConnect():
    '''
    取得db链接
    '''
    db = pymysql.connect("localhost", "root", "761211", "douban")

    return db

def test():

    return db

if __name__ == '__main__':
    # htmlContent = generateTestData()
    # isLastPage(htmlContent)

    # getDataFromMoviePage('https://movie.douban.com/subject/3233060/')

    getMovieURL()

    # print(test())

    # (movieName, directDict, year, attrsDict, actorDict, genreDict, countryValue, languageValue, initialReleaseDateDict,
    #  runtime, anotherName, imdbLink, post, average, votes) = getDataFromMoviePage('https://movie.douban.com/subject/1291843/')
    #
    # print(movieName, directDict, year, attrsDict, actorDict, genreDict, countryValue, languageValue, initialReleaseDateDict,
    #  runtime, anotherName, imdbLink, post, average, votes)

    # getDataFromMoviePage('https://www.douban.com')

    # saveMovieUrl()

    # test()