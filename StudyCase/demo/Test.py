import requests
from bs4 import BeautifulSoup
import pymysql

def test():

    home_url = "https://movie.douban.com/tag/2016?start=20&type=T"

    for year in range(1935,1937):
        pageStart = 0

        # 构建会话
        session = requests.Session()

        while True:
            home_url = generateMovieBriefUrl(year,pageStart)

            print(home_url)

            # 　登录后才能访问的url
            # session.cookies.clear()
            # session.cookies.
            r = session.get(home_url)


            strContent = r.content.decode()

            #如果当前也为最后一页，则退出循环
            ifLastPage = isLastPage(strContent)

            if ifLastPage:
                # 如果当前也为最后一页，则退出循环
                break
            else:
                # 如果当前不是最后一页，增加起始位置
                pageStart = pageStart + 20

            print(session.cookies)

            # parseDoubanMovieUrlFromBrief(strContent)

        session.close()

    return


def isLastPage(htmlContent):
    '''
    从豆瓣列表页中解析获得电影页面url
    '''
    soup = BeautifulSoup(htmlContent, "html.parser")

    aContent = soup.find("p",text = "没有找到符合条件的电影")

    if aContent is not None:
        result = True
    else:
        result = False

    return result

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
    cookies = {"Cookie":'ll="118205"; _ga=GA1.2.740277333.1448884744; _gat=1; bid="iu5QJoQtotc"; ps=y; '}

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

    print(strContent)

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
    print(r.cookies)

    strContent = r.content.decode()

    print(strContent)

    soup = BeautifulSoup(strContent, "html.parser")

    #取得导演信息
    aContent = soup.find("span", property="v:itemreviewed")
    print(aContent.text)

    # aContent = soup.find_all("a", "nbg")
    #
    # hrefConteng = [value['href'] for value in aContent]

    session.close()

    return aContent

def saveMovieUrl(movieUrl):

    db = getDbConnect()

    # 使用 cursor() 方法获取操作游标
    cursor = db.cursor()

    # SQL 插入语句
    sql = "INSERT INTO MOVIEURLLIST(MOVIE_URL) VALUES ('" + movieUrl + "')"

    try:
        # 执行 sql 语句
        cursor.execute(sql)
        # 提交到数据库执行
        db.commit()
    except:
        # 如果发生错误则回滚
        db.rollback()

        # 关闭数据库连接
    db.close()

    return

def getDbConnect():
    db = pymysql.connect("localhost", "root", "761211", "douban")

    return db

if __name__ == '__main__':
    # htmlContent = generateTestData()
    # isLastPage(htmlContent)

    getDataFromMoviePage('https://movie.douban.com/subject/26769449/')

    # getDataFromMoviePage('https://www.douban.com')

    # saveMovieUrl()

    # test()