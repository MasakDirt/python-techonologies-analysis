import re
import time
from datetime import date

import scrapy
from scrapy import Request
from scrapy.http import Response
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from technologies_analysis.collections import MONTHS_UA, TECHNOLOGIES


class DouSpider(scrapy.Spider):
    name = "dou"
    allowed_domains = ["jobs.dou.ua"]
    start_urls = ["https://jobs.dou.ua/vacancies/?category=Python"]

    def parse(self, response: Response, **kwargs) -> dict:
        html_source = self._load_all_vacancies(response.url)
        response = response.replace(body=html_source)

        for vacancy in response.css(".l-vacancy"):
            yield Request(
                url=vacancy.css(".title .vt::attr(href)").get(),
                callback=self._parse_detail_url,
                meta={
                    "title": vacancy.css(".title .vt::text").get(),
                    "publish_date": self._parse_ukr_date(
                        vacancy.css(".date::text").get()
                    ),
                    "company": vacancy.css(
                        ".title > strong > a::text"
                    ).get().replace("\xa0", ""),
                }
            )

    def _parse_ukr_date(self, publish_date_str: str) -> date:
        day, month = publish_date_str.split()
        month_num = MONTHS_UA[month]
        return date(date.today().year, month_num, int(day))

    def _load_all_vacancies(self, url: str) -> str:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")

        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)

        try:
            load_more = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".more-btn > a")
                )
            )

            while True:
                driver.execute_script(
                    "arguments[0].scrollIntoView(true);", load_more
                )

                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, ".more-btn > a")
                    )
                ).click()

                time.sleep(1)

                load_more = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, ".more-btn > a")
                    )
                )

                if not load_more.is_displayed():
                    break

        except Exception as e:
            print(f"Error occurred while loading vacancies: {e}")
        finally:
            page_source = driver.page_source
            driver.quit()

        return page_source

    def _parse_detail_url(self, response: Response) -> dict:
        salary = response.css(".salary::text").re_first(
            r"\$(\d+).*?–?\s*(\d+)?"
        )
        description = response.css(".vacancy-section").get()
        technologies_found = [
            tech for tech in TECHNOLOGIES if
            re.search(rf"\b{tech}\b", description, re.IGNORECASE)
        ]

        yield {
            "title": response.meta["title"],
            "publish_date": response.meta["publish_date"],
            "company": response.meta["company"],
            "company_description": response.css(
                ".l-t::text"
            ).get().replace("\xa0", "").strip(),
            "place": response.css(".sh-info .place::text").get(),
            "salary": int(salary) if salary else salary,
            "technologies": ", ".join(technologies_found),
        }
