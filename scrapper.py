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
        new_json = []
        with open(filename, encoding="utf-8") as HohichJSON:
            content = json.loads(HohichJSON.read())
            for place in content:
                place = json.loads(place)
                x = self.get_source_code(place["url"], place)
                new_json.append(x)

        with open(filename, "w", encoding="utf-8") as json_file:
            json.dump(new_json, json_file, ensure_ascii=False, indent=4) 

    def get_source_code(self, URI: str, old_json: dict = None) -> dict:
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
            time.sleep(2)

        
            js = self.driver.execute_script

            processed_comments = []
            load_more = True

            # Элемент, содержащий список комментариев
            comments_list = self.driver.find_element(By.CLASS_NAME, "business-reviews-card-view__reviews-container")  

            while load_more:
                # Получаем видимые комментарии
                visible_comments = comments_list.find_elements(By.CLASS_NAME, "business-review-view__info")
                if len(visible_comments) == 0:
                    print("No comments found")
                    return

                # Обрабатываем видимые комментарии
                for comment_element in visible_comments:
                    try:
                        try:
                            user_link_element = comment_element.find_element(By.CLASS_NAME, "business-review-view__link")
                            user_name = user_link_element.find_element(By.TAG_NAME, "span").text
                            user_link = user_link_element.get_attribute("href")
                        except:
                            user_name_element = comment_element.find_element(By.CLASS_NAME, "business-review-view__author-name")
                            user_name = user_name_element.find_element(By.TAG_NAME, "span").text
                            user_link = "deleted_account"
                        
                        rating_element = comment_element.find_element(By.CSS_SELECTOR, "span[itemprop='reviewRating']")
                        rating = rating_element.find_element(By.CSS_SELECTOR, "meta[itemprop='ratingValue']").get_attribute("content")
                        
                        comment_text_element = comment_element.find_element(By.CLASS_NAME, "business-review-view__body-text")
                        comment_text = comment_text_element.text

                        if any(comment['comment'] == comment_text for comment in processed_comments):
                            continue

                        # Запоминаем уникальные комментарии
                        processed_comments.append({
                            "author": user_name,
                            "author_url": user_link,
                            "comment": comment_text,
                            "rating": rating
                        })
                    
                    except Exception as e:
                        print("scip error comment", e)
                try:
                    # Прокручиваем до конца списка комментариев
                    js("arguments[0].scrollIntoView(true);", visible_comments[-1])
                    time.sleep(2)

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
            try:
                return self.make_json(processed_comments, old_json)
            except:
                print("Ссылка получена не из jsona")

        except Exception as e:
            print("что-то не так", e)

    def make_json(self, processed_comments, old_json: dict) -> dict:
        old_json["reviews"] = processed_comments
        return old_json 
    
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
    # scrapper.get_source_code("https://yandex.by/maps/org/cinema_bar/239834013499/")
    # scrapper.get_sorce_code("https://yandex.by/maps/org/lyubimoye_mesto/183920941504/?ll=29.224177%2C53.141682&z=14")
    scrapper.get_url("ГомельМузеи.json")
    scrapper.close_driver()


if __name__ == "__main__":
    main()