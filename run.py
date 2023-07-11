import json
import os

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright


class WebScraper:
    def __init__(self):
        load_dotenv('.env')
        self.all_quotes = []
        self.PROXY = os.getenv('PROXY')
        self.INPUT_URL = os.getenv('INPUT_URL')
        self.OUTPUT_FILE = os.getenv('OUTPUT_FILE')
        if self.PROXY:
            proxy_parts = self.PROXY.split('@')
            credentials, self.server = proxy_parts
            self.username, self.password = credentials.split(':')

    def scrap_page(self, page):
        page.wait_for_selector('.quote')
        page_quotes = page.query_selector_all('.quote')
        quotes = []
        for div in page_quotes:
            text = div.query_selector('.text').inner_text().replace(
                '\u201c', '').replace('\u201d', '')
            author = div.query_selector('.author').inner_text()
            tags = [tag.inner_text() for tag in div.query_selector_all('.tag')]
            quote_dictionary = {
                "text": text,
                "by": author,
                "tags": tags
            }
            quotes.append(quote_dictionary)
        #all_quotes = self.all_quotes + quotes
        return quotes

    def go_to_next_page(self, page, is_last_page=False):
        next_button = page.query_selector('a:has-text("next")')
        if next_button:
            next_button.click()
            page.wait_for_load_state()
        else:
            is_last_page = True
        return is_last_page

    def all_pages_loop(self, page):
        while True:
            try:
                self.all_quotes = self.all_quotes + self.scrap_page(page)
            except:
                print('Scraping problem occured!')
                return 1
            try:
                last_page = self.go_to_next_page(page)
                if last_page == True:
                    break
            except:
                print("Paginatin problem occured!")
                return 1
        return 0


def main():
    quotesToScrape = WebScraper()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=False,
            proxy={'server': quotesToScrape.server, 'username': quotesToScrape.username, 'password': quotesToScrape.password})
        page = browser.new_page()
        try:
            page.goto(quotesToScrape.INPUT_URL)
        except:
            print('Page can not be reached!')
            return 1
        exe = quotesToScrape.all_pages_loop(page)
        if exe == 1:
            return 1
        final = json.dumps(quotesToScrape.all_quotes, indent=2)
        with open(quotesToScrape.OUTPUT_FILE, "w") as outfile:
            outfile.write(final)
        browser.close()


if __name__ == '__main__':
    main()
