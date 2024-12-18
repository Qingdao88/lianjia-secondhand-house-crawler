import mysql.connector
import requests
from bs4 import BeautifulSoup
import csv

# 连接到 MySQL 数据库
conn = mysql.connector.connect(
    host="localhost",  # 数据库地址，通常是 localhost
    user="root",  # 你的 MySQL 用户名
    password="mlyzga78",  # 你的 MySQL 密码
    database="RealEstateDB"  # 你要连接的数据库名称
)
table_name = "HouseInfo"  # 数据表的名字
cursor = conn.cursor()  # 创建一个游标对象（cursor），用于执行 SQL 查询

headers = {  # 必须要设置这个伪装，否则网站检测出是爬虫不让访问
    # "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/529.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"
}

def write_to_csv(house_name, community_name, address, house_type, area_size, floor_count, total_price, unit_price,
                 agent_name, agent_phone):
    file_path = "house_data.csv"  # 定义CSV文件路径，可以根据需求修改
    header = ["house_name", "community_name", "address", "house_type", "area_size", "floor_count", "total_price",
              "unit_price", "agent_name", "agent_phone"]  # CSV文件的表头
    row_data = [house_name, community_name, address, house_type, area_size, floor_count, total_price, unit_price,
                agent_name, agent_phone]  # 要写入的一行数据

    with open(file_path, 'a', newline='', encoding='utf-8') as csvfile:  # 'a'表示追加模式
        writer = csv.writer(csvfile)
        if csvfile.tell() == 0:  # 判断文件是否为空，若为空则写入表头
            writer.writerow(header)
        writer.writerow(row_data)
        print("数据写入csv成功")

def insert_data_to_db(house_name, community_name, address, house_type, area_size, floor_count, total_price, unit_price,
                      agent_name,
                      agent_phone):
    insert_query = f"INSERT INTO {table_name} (house_name, community_name, address, house_type, area_size, floor_count, total_price, unit_price, agent_name, agent_phone) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    values = (house_name, community_name, address, house_type, area_size, floor_count, total_price, unit_price, agent_name, agent_phone)
    try:
        cursor.execute(insert_query, values)
        conn.commit()  # 提交事务，使插入操作生效
        print("数据插入MySQL成功")
    except mysql.connector.Error as err:
        print(f"数据插入MySQL失败: {err}")


def get_one_page_data(target_url):
    response = requests.get(target_url, headers=headers)  # 发送 GET 请求，获取网页内容
    soup = BeautifulSoup(response.text, 'html.parser')  # 使用 BeautifulSoup 解析网页内容

    room_div = soup.find('div', class_="room")

    house_name = soup.find('h1', class_="main").text
    community_name = soup.find('a', class_="info").text
    address = soup.find('span', class_="info").text
    house_type = room_div.find('div', class_="mainInfo").text
    area_size = soup.find('div', class_="area").find('div', class_="mainInfo").text
    floor_count = room_div.find('div', class_="subInfo").text
    total_price = soup.find('span', class_="total").text + "万"
    unit_price = soup.find('span', class_="unitPriceValue").text
    agent_name = soup.find('a', class_="ke-agent-sj-name").text
    agent_phone = soup.find('div', class_="ke-agent-sj-phone").text

    print(house_name, community_name, address, house_type, area_size, floor_count, total_price, unit_price, agent_name, agent_phone)
    # insert_data_to_db(house_name, community_name, address, house_type, area_size, floor_count, total_price, unit_price, agent_name, agent_phone)
    write_to_csv(house_name, community_name, address, house_type, area_size, floor_count, total_price, unit_price, agent_name, agent_phone)


def get_targets(pg_url):
    response = requests.get(pg_url, headers=headers)  # 发送 GET 请求，获取网页内容
    soup = BeautifulSoup(response.text, 'html.parser')  # 使用 BeautifulSoup 解析网页内容
    raw_title_divs = soup.find_all("div", class_="title")
    targets = []
    for title_div in raw_title_divs:
        if title_div.text == "人机验证":
            raise Exception("已被网站的反爬措施限制，换台计算机试试")
        target = title_div.find('a')
        if target is not None:
            try:
                targets.append(target['href'])
            except KeyError:
                print("用户未登录，当前爬取的页面url为：", pg_url)
    return targets


def traverse_each_pg(start, end):
    base_url = "https://sz.lianjia.com/ershoufang/pg"
    for i in range(start, end + 1):
        pg_url = base_url + str(i)
        targets = get_targets(pg_url)
        for target in targets:
            get_one_page_data(target)


def clear_table_data():
    try:
        # 使用DELETE语句清空表数据，这里假设你的表名为HouseInfo，根据实际情况调整
        delete_query = f"DELETE FROM {table_name}"
        cursor.execute(delete_query)
        conn.commit()  # 提交事务，使删除操作生效
        print(f"{table_name}数据表中的数据已清空")
    except mysql.connector.Error as err:
        print(f"清空数据表时出错: {err}")


if __name__ == '__main__':
    clear_table_data()
    traverse_each_pg(1, 2)

cursor.close()  # 关闭游标
conn.close()  # 关闭数据库连接
