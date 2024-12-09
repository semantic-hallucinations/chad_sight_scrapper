from abc import ABC, abstractmethod
import json
import time
import logging
import os

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logging.basicConfig(level=logging.DEBUG)

class CommentScrapper(ABC):
    def __init__(self):
        self.driver = None

    @abstractmethod
    def create_driver(self):
        pass

    def get_url(self, filename: str) -> None:
        """
        Читает файл JSON с URL-ами, обрабатывает каждый URL и записывает комментарии в файл.
        """
        new_json = []
        with open(filename, encoding="utf-8") as HohichJSON:
            print("loads1")
            content = json.load(HohichJSON)
            for place in content:
                print("after loads2")
                x = self.get_source_code(place["url"], place)
                new_json.append(x)
        filename = os.path.basename(filename)
        with open("/app/data/"+f"{filename}", "w", encoding="utf-8") as json_file:
            json.dump(new_json, json_file, ensure_ascii=False, indent=4)

    def get_source_code(self, URI: str, old_json: dict = None) -> dict:
        """
        Скрапит комментарии с указанного URL и записывает их в JSON-файл.
        """
        try:
            self.driver.get(url=URI)
        except Exception as e:
            print("Страница не прогружается:", e)
        try:
            wait = WebDriverWait(self.driver, 15)
            reviews_tab = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//a[contains(@class, 'tabs-select-view__label') and text()='Отзывы']")))
            ActionChains(self.driver).move_to_element(reviews_tab).perform()
            self.driver.execute_script("arguments[0].style.border='3px solid red'", reviews_tab)
            time.sleep(2)

            reviews_tab.send_keys(Keys.ENTER)
            time.sleep(2)

            processed_comments = []
            load_more = True
            comments_list = self.driver.find_element(By.CLASS_NAME, "business-reviews-card-view__reviews-container")

            while load_more:
                visible_comments = comments_list.find_elements(By.CLASS_NAME, "business-review-view__info")
                if not visible_comments:
                    print("No comments found")
                    return old_json

                for comment_element in visible_comments:
                    try:
                        user_name, user_link, rating, comment_text = self.parse_comment(comment_element)
                        if any(comment['comment'] == comment_text for comment in processed_comments):
                            continue

                        comment_data = {
                            "author": user_name,
                            "author_url": user_link,
                            "comment": comment_text,
                            "rating": rating
                        }
                        processed_comments.append(comment_data)

                    except Exception as e:
                        print("Ошибка обработки комментария:", e)

                try:
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", visible_comments[-1])
                    time.sleep(2)
                    wait.until(lambda driver: len(comments_list.find_elements(By.CLASS_NAME, "business-review-view__info")) > len(visible_comments))
                except TimeoutException:
                    load_more = False

            return self.make_json(processed_comments, old_json)
        except Exception as e:
            print("Что-то пошло не так:", e)

    def parse_comment(self, comment_element):
        """
        Извлекает данные из HTML-элемента комментария.
        """
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

        return user_name, user_link, rating, comment_text

    def make_json(self, processed_comments, old_json: dict) -> dict:
        """
        Обновляет старый JSON с новыми комментариями.
        """
        old_json["reviews"] = processed_comments
        return old_json

    def close_driver(self):
        self.driver.quit()


class ChromeCommentScrapper(CommentScrapper):
    def create_driver(self):
        selenium_host = os.getenv("SELENIUM_HOST", "http://localhost:4444/wd/hub")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Remote(command_executor=selenium_host, options=options)


class FirefoxCommentScrapper(CommentScrapper):
    def create_driver(self):
        selenium_host = os.getenv("SELENIUM_HOST", "http://localhost:4444/wd/hub")
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Remote(command_executor=selenium_host, options=options)


class ScrapperFactory:
    @staticmethod
    def make_scrapper(browser: str) -> CommentScrapper:
        if browser.lower() == "chrome":
            scrapper = ChromeCommentScrapper()
        elif browser.lower() == "firefox":
            scrapper = FirefoxCommentScrapper()
        else:
            raise ValueError("Браузер не поддерживается")
        scrapper.create_driver()
        return scrapper


def process_input_folder(scrapper: CommentScrapper, input_folder: str) -> None:
    """
    Обрабатывает все JSON-файлы в указанной папке.
    """
    if not os.path.exists(input_folder):
        print(f"Папка {input_folder} не найдена.")
        return

    files = [f for f in os.listdir(input_folder) if f.endswith('.json')]

    if not files:
        print(f"В папке {input_folder} нет JSON-файлов для обработки.")
        return

    for file_name in files:
        file_path = os.path.join(input_folder, file_name)
        print(f"Обрабатывается файл: {file_name}")
        try:
            scrapper.get_url(file_path)
        except Exception as e:
            print(f"Ошибка при обработке {file_name}: {e}")


def main() -> None:
    scrapper = ScrapperFactory.make_scrapper("chrome")
    input_folder = "output"
    process_input_folder(scrapper, input_folder)
    print(f"Обработался файл")
    scrapper.close_driver()


if __name__ == "__main__":
    main()
