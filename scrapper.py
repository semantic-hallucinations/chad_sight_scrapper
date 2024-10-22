from abc import ABC, abstractmethod
import json
import time
import typing

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
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

        
            js = self.driver.execute_script

            processed_comments = set()
            load_more = True

            # Элемент, содержащий список комментариев
            comments_list = self.driver.find_element(By.CLASS_NAME, "business-reviews-card-view__reviews-container")  
            scrolled_container = self.driver.find_element(By.CLASS_NAME, "scroll__container")  # Элемент контейнера для прокрутки

            while load_more:
                # Получаем видимые комментарии
                visible_comments = comments_list.find_elements(By.CLASS_NAME, "business-review-view__info")  # Замените на класс комментариев
                if len(visible_comments) == 0:
                    print("No comments found")
                    return

                # Обрабатываем видимые комментарии
                for comment_element in visible_comments:
                    comment_text = comment_element.text
                    if comment_text in processed_comments:
                        continue

                    # Запоминаем уникальные комментарии
                    processed_comments.add(comment_text)
                    print(f"New comment: {comment_text}")

                try:
                    # Прокручиваем до конца списка комментариев
                    js("arguments[0].scrollIntoView(true);", visible_comments[-1])
                    time.sleep(2)  # Небольшая пауза для загрузки новых элементов

                    # Ожидаем появления новых комментариев
                    wait.until(lambda driver: len(comments_list.find_elements(By.CLASS_NAME, "business-review-view__info")) > len(visible_comments))

                except TimeoutException:
                    print("No more comments to load!")
                    load_more = False

                finally:
                    # Проверка: если новых комментариев не добавилось, останавливаем прокрутку
                    new_visible_comments = comments_list.find_elements(By.CLASS_NAME, "business-review-view__info")
                    if len(new_visible_comments) == len(processed_comments):
                        load_more = False

            print("Finished scrolling and scraping comments.")

            # comments = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'business-review-view__body-text'))))
            # usernames = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'business-review-view__author-name')))

            # for i in range(len(comments)):
            #     username = usernames[i].text
            #     comment = comments[i].text
            #     print(i, username, comment)

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
    # scrapper.get_sorce_code("https://yandex.by/maps/org/cinema_bar/239834013499/")
    # scrapper.get_sorce_code("https://yandex.by/maps/org/kostel_sviatykh_symona_ta_oleny/1013424966/?ll=27.547675%2C53.896320&z=17")
    scrapper.get_sorce_code("https://yandex.by/maps/org/lyubimoye_mesto/183920941504/?ll=29.224177%2C53.141682&z=14")
    # scrapper.get_url("МинскБары.json")
    scrapper.close_driver()


if __name__ == "__main__":
    main()