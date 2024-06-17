from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from pymongo import MongoClient

import time
import re

client = MongoClient('localhost', 27017)   # mongoDB는 27017 포트로 돌아갑니다.
db = client.dbjungle

def insert_all():
    path = "D:\\Hanubas proj\\Jungle_Book\\1. Newbie in Krafton Jungle\\Chapter_05_AWS\\gstar2023_games\\chromedriver.exe"
    service = Service(executable_path=path)
    driver = webdriver.Chrome(service=service)

    gstar_url = 'https://chat.openai.com/'
    driver.get(gstar_url)

    time.sleep(3)

    driver.find_element(By.XPATH, '//*[@id="__next"]/div[1]/div[2]/div[1]/div/div/button[1]/div').click()

    time.sleep(2)

    driver.find_element(By.XPATH, '/html/body/div/main/section/div/div/div/div[4]/form[2]/button').click()

    time.sleep(2)

    driver.find_element(By.XPATH, '//*[@id="identifierId"]').click()
    driver.find_element(By.XPATH, '//*[@id="identifierId"]').click()
    time.sleep(0.5)
    driver.find_element(By.XPATH, '//*[@id="identifierId"]').send_keys("po127992")
    time.sleep(0.5)
    driver.find_element(By.XPATH, '//*[@id="identifierId"]').send_keys(Keys.ENTER)

    time.sleep(2)

    driver.find_element(By.XPATH, '//*[@id="password"]/div[1]/div/div[1]/div').click()
    driver.find_element(By.XPATH, '//*[@id="password"]/div[1]/div/div[1]/div').click()
    time.sleep(0.5)
    driver.find_element(By.XPATH, '//*[@id="password"]/div[1]/div/div[1]/div').send_keys("wh0knowb@s")

    time.sleep(3)
        
    input = driver.find_element(By.XPATH, '//*[@id="prompt-textarea"]')
    input.click()
    input.send_keys(Keys.CONTROL + "a")
    input.send_keys("TRPG 게임을 하자. 하나의 스토리를 작성할 건데 내가 한 문장을 말할 때마다 개연성이 있게 네가 이어서 한 문장씩 말하는거야.")
    input.send_keys(Keys.ENTER)
    
    time.sleep(10)

    output = driver.find_element(By.XPATH, '//*[@id="__next"]/div[1]/div[2]/main/div[2]/div[1]/div/div/div/div[3]/div/div/div[2]/div[2]/div[1]/div/div/p')
    print(output.text)

            
if __name__ == '__main__':

    # 영화 사이트를 scraping 해서 db 에 채우기
    insert_all()