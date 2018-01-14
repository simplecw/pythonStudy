import requests
from bs4 import BeautifulSoup
import pymysql
import random
import string
import time
import os
from requests.auth import HTTPProxyAuth


def test():
    proxy = get_proxy_server_list()

    for i in range(1, 100):
        print(random.choice(proxy))

def get_movie_url():
    """
    将豆瓣单部电影的URL保存到数据库中
    """

    # 构建会话
    cookies = prepare_cookies()
    headers = prepare_heads()

    proxy = get_proxy_server_list()

    db = get_db_connect()

    loop_num = 0

    auth = HTTPProxyAuth('username', 'mypassword')

    try:
        for year in range(1950, 1955):
            page_start = 0

            while True:
                home_url = generate_movie_brief_url(year, page_start)
                # home_url = "https://www.baidu.com"
                print("home_url is {0}".format(home_url))
                r = requests.get(home_url, cookies=cookies, headers=headers, proxies=random.choice(proxy), auth=auth)
                # r = requests.get(home_url, cookies=cookies, headers=headers, proxies={"https": "https://115.215.51.38:33652"})

                content = r.content.decode()

                # 如果当前也为最后一页，则退出循环
                if_last_page = is_last_page(content)

                if if_last_page:
                    # 如果当前也为最后一页，则退出循环
                    break
                else:
                    # 如果当前不是最后一页，增加起始位置
                    page_start = page_start + 20

                douban_movie_url = parse_douban_movie_url_from_brief(content)

                for url in douban_movie_url:
                    save_movie_url(url,db)

                # time.sleep(0.5)

                loop_num = loop_num + 1

                if loop_num % 5 == 0:
                    # 更新cookie
                    cookies = prepare_cookies()

        db.commit()

    except Exception as e:
        print(e)
        # 如果发生错误则回滚
        db.rollback()

        # 关闭数据库连接
    db.close()

    return


def is_last_page(html_content):
    """
    从豆瓣列表页中解析获得电影页面url
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # 取得编剧信息
    attr_title = soup.find("a", class_="nbg")
    if attr_title is None:
        result = True
    else:
        result = False

    return result


def parse_douban_movie_url_from_brief(html_content):
    """
    从豆瓣列表页中解析获得电影页面url
    """
    soup = BeautifulSoup(html_content, "html.parser")

    content = soup.find_all("a","nbg")

    href_content = [value['href'] for value in content]

    return href_content


def generate_movie_brief_url(year, page_start):
    """
    根据年份和页起始位置生成豆瓣的目录页url
    """
    return "https://movie.douban.com/tag/" + str(year) + "?start="+str(page_start) + "&type=T"


def prepare_heads():
    """
    准备请求的header内容
    """

    headers = {'User-Agent':
                   'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36'}

    return headers


def prepare_cookies():
    """
    准备请求的cookie内容
    """
    # 注：bid值可能需要定时跟换

    bid_value = "bid=%s" % "".join(random.sample(string.ascii_letters + string.digits, 11))

    cookies = {"Cookie": 'll="108311"; _ga=GA1.2.740277123.1448884744; _gat=1; {0}; ps=y; '.format(bid_value)}
    print(cookies)

    return cookies


def generate_test_data():

    home_url = "https://movie.douban.com/tag/1860?start=20&type=T"

    # 构建会话
    session = requests.Session()
    # 　登录后才能访问的url
    r = session.get(home_url)

    content = r.content.decode()

    session.close()

    return content


def get_data_from_movie_page(page_url):
    """
    从单个电影页面中解析电影数据
    """

    # 取得豆瓣电影ID
    douban_movie_id = page_url.replace('https://movie.douban.com/subject/', '').replace('/', '')

    # 构建会话
    cookies = prepare_cookies()
    headers = prepare_heads()

    # 　登录后才能访问的url
    r = requests.get(page_url, cookies=cookies, headers=headers)

    content = r.content.decode()

    soup = BeautifulSoup(content, "html.parser")

    # 取得片名信息
    movie_name = soup.find("span", property="v:itemreviewed")
    if movie_name is None:
        movie_name_return = None
    else:
        movie_name_return = movie_name.text

    # 取得导演信息
    direct_name_arr = soup.find_all("a", rel="v:directedBy")
    if direct_name_arr is None:
        direct_dict = None
    else:
        direct_dict = {collect_celebrity_key(directName['href']): directName.text for directName in direct_name_arr}

    # 取得上映年信息
    year = soup.find("span", class_="year")
    if year is None:
        year_return = None
    else:
        year_return = year.text.replace("(", "").replace(")", "")

    # 取得编剧信息
    attr_title = soup.find("span", text="编剧")
    if attr_title is None:
        attr_dict = None
    else:
        attr_value_content = attr_title.next_sibling.next_sibling
        attr_value_arr = attr_value_content.find_all("a")
        attr_dict = {collect_celebrity_key(attr_value['href']): attr_value.text for attr_value in attr_value_arr}

    # 取得主演信息
    actor_title = soup.find("span", text="主演")
    if actor_title is None:
        actor_dict = None
    else:
        actor_value_content = actor_title.next_sibling.next_sibling
        actor_value_arr = actor_value_content.find_all("a")
        actor_dict = {collect_celebrity_key(actor_value['href']): actor_value.text for actor_value in actor_value_arr}

    # 取得类型信息
    genre_arr = soup.find_all("span", property="v:genre")
    if genre_arr is None:
        genre_text_arr = None
    else:
        genre_text_arr = [genre.text for genre in genre_arr]

    # 取得国家信息
    country_title = soup.find("span", text="语言:")
    if country_title is None:
        country_value = None
    else:
        country_value = country_title.previous_sibling.previous_sibling.previous_sibling

    # 取得语言信息
    language_title = soup.find("span", text="语言:")
    if language_title is None:
        language_value = None
    else:
        language_value = language_title.next_sibling

    # 取得上映时间信息
    initial_release_date_arr = soup.find_all("span", property="v:initialReleaseDate")
    if initial_release_date_arr is None:
        initial_release_date_list = None
    else:
        initial_release_date_list = [initial_release_date.text for initial_release_date in initial_release_date_arr]

    # 取得片长信息
    runtime = soup.find("span", property="v:runtime")
    if runtime is None:
        runtime_return = None
    else:
        runtime_return = runtime.text.strip()

    # 取得又名信息
    another_name_title = soup.find("span", text="又名:")
    if another_name_title is None:
        another_name = None
    else:
        another_name = another_name_title.next_sibling

    # 取得IMDB链接信息
    another_name_title = soup.find("span", text="又名:")
    if another_name_title is None:
        imdb_link_return = None
    else:
        imdb_link = another_name_title.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling
        imdb_link_return = imdb_link["href"]

    # 取得海报信息
    post = soup.find("img", rel="v:image")
    if post is None:
        post_return = None
    else:
        post_return = post['src'].replace("s_ratio_poster","l")

    # 取得豆瓣得分信息
    average = soup.find("strong", property="v:average")
    if average is None:
        average_return = None
    else:
        if average.text.strip() == "":
            average_return = None
        else:
            average_return = float(average.text)

    # 取得评价人数信息
    votes = soup.find("span", property="v:votes")
    if votes is None:
        votes_return = None
    else:
        if votes.text.strip() == "":
            votes_return = None
        else:
            votes_return = int(votes.text.strip())

    return (douban_movie_id, movie_name_return, direct_dict, year_return, attr_dict, actor_dict, genre_text_arr,
            country_value, language_value, initial_release_date_list, runtime_return, another_name, imdb_link_return,
            post_return, average_return, votes_return)


def collect_celebrity_key(celebrity_content):
    """
    从豆瓣演职人员link中提取演职人员id
    """
    return celebrity_content.replace("celebrity", "").replace(r"/", "")


def save_movie_url(movie_url, db):
    """
    将豆瓣单部电影的URL保存到数据库中
    """
    # 使用 cursor() 方法获取操作游标
    cursor = db.cursor()

    # SQL 插入语句
    sql = "INSERT INTO movieurllist (MOVIE_URL) VALUES ('" + movie_url + "')"

    # 执行 sql 语句
    cursor.execute(sql)

    return


def get_db_connect():
    """
    取得db链接
    """

    # db = pymysql.connect("localhost", "root", "761211", "douban", charset="utf8")
    db = pymysql.connect("localhost", "root", "761211", "history_tool", use_unicode=True, charset="utf8")

    return db


def save_movie_detail_data(db, douban_movie_id, movie_name, direct_dict, year, attrs_dict, actor_dict, genre_arr,
                           country, language, initial_release_date_list, runtime, another_name, imdb_link, post,
                           average, votes):
    """
    将豆瓣单部电影的URL保存到数据库中
    """

    # 保存电影数据
    if initial_release_date_list is not None:
        initial_release_date = " / ".join(initial_release_date_list)

    save_movie_main_data(db, douban_movie_id, movie_name, year, country, language, initial_release_date, runtime,
                         another_name, imdb_link, post, average, votes)

    # 保存导演数据
    if direct_dict is not None:
        save_celebrity(db, douban_movie_id, direct_dict, 0)

    # 保存编剧数据
    if attrs_dict is not None:
        save_celebrity(db, douban_movie_id, attrs_dict, 1)

    # 保存演员数据
    if actor_dict is not None:
        save_celebrity(db, douban_movie_id, actor_dict, 2)

    # 保存电影类型数据
    if genre_arr is not None:
        save_genre(db, douban_movie_id, genre_arr)

    return


def save_genre(db, douban_movie_id, genre_arr):
    """
    保存电影住数据

    :param db: dbconnect对系那个
    :param douban_movie_id: 豆瓣电影id
    :param genre_arr: 电影类型
    :return:
    """
    with db.cursor() as cursor:
        for genre in genre_arr:
            # Create a new record
            sql = "INSERT INTO `MOVIE_GENRE` (`MOVIE_DOUBAN_ID`, `GENRE`) VALUES (%s, %s)"
            cursor.execute(sql, (douban_movie_id, genre))


def save_celebrity(db, douban_movie_id, celebrity_dict, employee_type):
    """
    保存电影演职员信息

    :param db: dbconnect对系那个
    :param douban_movie_id: 豆瓣电影id
    :param celebrity_dict: 演职员信息
    :param employee_type: 演职员类型
            0:导演; 1:编剧; 2:演员;
    :return:
    """
    with db.cursor() as cursor:
        for k, v in celebrity_dict.items():

            # 正常情况下豆瓣的演职员有对应的编码，如果从网页上未取得编码，则放弃该人员数据
            if k.isdigit():
                # 用豆瓣演职员编码到CELEBRITY表中查询是否有记录，如没有，插入该人员记录
                sql = "SELECT CELEBRITY_ID FROM CELEBRITY WHERE CELEBRITY_ID = %s;"
                cursor.execute(sql, k)

                if cursor.rowcount == 0:
                    # Create a new record
                    sql = "INSERT INTO `CELEBRITY` (`CELEBRITY_ID`, `EMPLOYEE_NAME`) VALUES (%s, %s)"
                    cursor.execute(sql, (k, v))

                # 到MOVIE_CELEBRITY表中，用人员id，电影id和身份查询是否有记录，没有则创建记录。
                sql = "SELECT CELEBRITY_ID FROM MOVIE_CELEBRITY " \
                      "WHERE MOVIE_DOUBAN_ID = %s AND CELEBRITY_ID = %s AND EMPLOYEE_TYPE = %s;"
                cursor.execute(sql, (douban_movie_id, k, employee_type))

                if cursor.rowcount == 0:
                    # Create a new record
                    sql = "INSERT INTO `MOVIE_CELEBRITY` (`MOVIE_DOUBAN_ID`, `CELEBRITY_ID`, `EMPLOYEE_TYPE`) " \
                          "VALUES (%s, %s, %s)"
                    cursor.execute(sql, (douban_movie_id, k, employee_type))


def save_movie_main_data(db, douban_movie_id, movie_name, year, country, language, initial_release_date, runtime,
                         another_name, imdb_link, post, average, votes):
    """
    保存电影住数据

    :param db: dbconnect对系那个
    :param douban_movie_id: 豆瓣电影id
    :param movie_name: 电影名称
    :param year: 放映年
    :param country:国家
    :param language: 语言
    :param initial_release_date:放映日期
    :param runtime: 时长
    :param another_name:又名
    :param imdb_link: imdb link
    :param post: 海报link
    :param average: 豆瓣得分
    :param votes: 豆瓣评分人数
    :return:
    """

    with db.cursor() as cursor:
        # Create a new record
        # sql = "INSERT INTO `users` (`email`, `password`) VALUES (%s, %s)"
        sql = "INSERT INTO `MOVIE` (`MOVIE_NAME`, `MOVIE_DOUBAN_ID`, `YEAR`,`INITIAL_RELEASE_DATE`,`COUNTRY`," \
              "`LANGUAGE`,`RUNTIME`,`IMDB_LINK`,`ANOTHER_NAME`,`POST_URL`,`AVERAGE`,`VOTES`) VALUES " \
              "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        cursor.execute(sql, (movie_name.encode('utf-8'), douban_movie_id, year, initial_release_date, country,
                             language, runtime, imdb_link, another_name, post, average, votes))


def get_proxy_server():
    """
    从XiciDaili.com上抓取代理服务器
    :return:
    """
    os.chdir('/home/chenwei/文档/project/doubanMovie/')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Mobile Safari/537.36'}
    url = 'http://www.xicidaili.com/nn/1'
    s = requests.get(url, headers=headers)
    soup = BeautifulSoup(s.text, 'lxml')
    ips = soup.select('#ip_list tr')
    fp = open('host.txt', 'a')
    for i in ips:
        try:
            ipp = i.select('td')
            if ipp[5].text == "HTTPS":
                ip = ipp[1].text
                host = ipp[2].text
                fp.write(ip)
                fp.write('\t')
                fp.write(host)
                fp.write('\n')
        except Exception as e:
            print('no ip !')
            print(e)
    fp.close()


def check_proxy_server():
    """
    通过访问百度校验代理服务器是否可用
    :return:
    """
    os.chdir('/home/chenwei/文档/project/doubanMovie/')
    # headers = {'User-Agent':'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Mobile Safari/537.36'}
    url = 'https://www.baidu.com'
    fp = open('host.txt', 'r')
    ips = fp.readlines()
    proxys = list()
    i = 0
    for p in ips:
        ip = p.strip('\n').split('\t')
        proxy = 'https:\\' + ip[0] + ':' + ip[1]
        proxies = {'https': proxy}
        proxys.append(proxies)
    for pro in proxys:
        try:
            s = requests.get(url, proxies=pro)
            i = i + 1
            print(i)
            print(s)
        except Exception as e:
            print(e)


def get_proxy_server_list():
    """
    从配置文件中取得代理服务器列表
    :return: 代理服务器列表
    """
    os.chdir('/home/chenwei/文档/project/doubanMovie/')
    fp = open('host.txt', 'r')
    ips = fp.readlines()
    proxys = list()
    for p in ips:
        ip = p.strip('\n').split('\t')
        proxy = 'http://' + ip[0] + ':' + ip[1]
        proxies = {'http': proxy, 'https': proxy}
        proxys.append(proxies)

    return proxys


def get_data_from_movie_page_main():
    """
    遍历所有的电影页面
    取得电影信息
    """
    db = get_db_connect()

    fo = open("foo.txt", "a")

    douban_movie_id = 0

    try:

        movie_url_list = get_all_movie_url(db)

        for movie_url in movie_url_list:
            try:

                # print(movie_url[1])
                (douban_movie_id, movie_name_return, direct_dict, year, attr_dict, actor_dict, genre_arr, country,
                 language, initial_release_date_list, runtime, another_name, imdb_link, post,average, votes) = \
                    get_data_from_movie_page(movie_url[1])

                save_movie_detail_data(db, douban_movie_id, movie_name_return, direct_dict, year, attr_dict, actor_dict,
                                       genre_arr,country, language, initial_release_date_list, runtime, another_name,
                                       imdb_link, post, average, votes)

                update_movie_url_status(db, movie_url[0])

                db.commit()

            except Exception as e:
                # 记下出错的电影id
                fo.write(str(e) + "\n")
                fo.write("影片id = " + douban_movie_id + "\n")

                print(e)
                # 如果发生错误则回滚
                db.rollback()

    except Exception as e:
        print(e)
        # 如果发生错误则回滚
        db.rollback()

    # 关闭数据库连接
    db.close()

    # 关闭文件
    fo.close()

    return


def update_movie_url_status(db, movie_id):
    """
    取得所有的电影url

    :param db: dbconnect数据库连接对象
    :return:
   """
    with db.cursor() as cursor:
        sql = "UPDATE movieurllist SET is_finish = 1 WHERE id = %s;"
        cursor.execute(sql, movie_id)

        return


def get_all_movie_url(db):
    """
    取得所有的电影url

    :param db: dbconnect对系那个
    :return: 所有的电影url列表
   """
    with db.cursor() as cursor:
        sql = "SELECT id, movie_url FROM movieurllist WHERE is_finish = 0 ORDER BY id limit 10;"
        cursor.execute(sql)

        return cursor.fetchall()


if __name__ == '__main__':
    # htmlContent = generate_test_data()
    # isLastPage(htmlContent)

    get_data_from_movie_page_main()