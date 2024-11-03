# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import sqlite3

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from technologies_analysis import settings


DB_NAME = settings.DB_NAME
TABLE_NAME = settings.TABLE_NAME


class TechnologiesAnalysisPipeline:
    def open_spider(self, spider):
        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()
        self.cursor.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
        self.cursor.execute(
            f"""
            CREATE TABLE {TABLE_NAME} (
                title TEXT,
                publish_date DATE,
                company TEXT,
                company_description TEXT,
                place TEXT,
                salary INT,
                technologies TEXT
            )
            """
        )
        self.conn.commit()

    def close_spider(self, spider):
        self.conn.close()

    def process_item(self, item, spider):
        self.conn.execute(
            f"INSERT INTO {TABLE_NAME} VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                item["title"],
                item["publish_date"],
                item["company"],
                item["company_description"],
                item["place"],
                item["salary"],
                item["technologies"],
            )
        )
        self.conn.commit()
        return item
