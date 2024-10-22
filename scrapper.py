from abc import ABC, abstractmethod
import json
import time
import typing

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager 

from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager


class CommentScrapper(ABC):
    def __init__(self):
        self.driver = None

    @abstractmethod
    def create_driver(self):
        pass

    def get_url(self, filename: str) -> None:
        with open(filename, encoding="utf-8") as HohichJSON:
            content = json.loads(HohichJSON.read())
            for place in content:
                place = json.loads(place)
                self.get_sorce_code(place["url"], place)

    def get_sorce_code(self, URI: str, old_json=None) -> None:
        try:
            self.driver.get(url=URI)
        except:
            print("страница не прогружается")
        try:
            wait = WebDriverWait(self.driver, 15)
            # Прокрутка к элементу
            reviews_tab = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@class, 'tabs-select-view__label') and text()='Отзывы']")))
            ActionChains(self.driver).move_to_element(reviews_tab).perform()
            self.driver.execute_script("arguments[0].style.border='3px solid red'", reviews_tab)

            # Ожидание возможных анимаций
            time.sleep(2)

            reviews_tab.send_keys(Keys.ENTER)
            time.sleep(3)

            # Скрапинг комментариев
            comments = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'business-review-view__body-text')))
            usernames = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'business-review-view__author-name')))

            for i in range(len(comments)):
                username = usernames[i].text
                comment = comments[i].text
                print(username, comment)

        except Exception as e:
            print("что-то не так", e)

    
    def close_driver(self):
        self.driver.quit()


class ChromeCommentScrapper(CommentScrapper):
    def create_driver(self):
        service = ChromeService(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service)

    

class FirefoxCommentScrapper(CommentScrapper):
    def create_driver(self):
        service = FirefoxService(GeckoDriverManager().install())
        self.driver = webdriver.Firefox(service=service)


class ScrapperFactory():
    @staticmethod
    def make_scrapper(browser: str) -> CommentScrapper:
        if browser.lower() == "chrome":
            scrapper =  ChromeCommentScrapper()
        elif browser.lower() == "firefox":
            scrapper = FirefoxCommentScrapper()
            
        else:
            raise ValueError("extention for this browser does not exist")
        scrapper.create_driver()
        return scrapper

def main() -> None:
    scrapper = ScrapperFactory.make_scrapper("Chrome")
    scrapper.get_sorce_code("https://yandex.by/maps/org/cinema_bar/239834013499/")
    # scrapper.get_sorce_code("https://yandex.by/maps/org/produkty/143566380911/?ll=28.913311%2C53.162192&z=16")
    # scrapper.get_url("МинскБары.json")
    scrapper.close_driver()


if __name__ == "__main__":
    main()