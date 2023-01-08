import json
import math
import os
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from tempfile import mkdtemp
from urllib.parse import urlparse

import boto3
import httpx
from dateutil.relativedelta import relativedelta
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
KINESIS_SIZE_LIMIT = 1000000  # actually, it is 1048576


class main_driver:

    def __init__(self):
        # options = webdriver.ChromeOptions()
        # options.add_argument("--headless")
        # options.add_argument("--disable-gpu")
        # options.add_argument("--single-process")
        # options.add_argument("--no-sandbox")
        # options.add_argument("--disable-dev-shm-usage")
        # options.add_argument("--window-size=1700x800")
        self.driver = webdriver.Chrome()


    def get_element(self, selector_tool, selector):
        try:
            return selector_tool.find_element(By.CSS_SELECTOR, selector)
        except NoSuchElementException:
            return None

    def element_present(self, selector: str):
        def out(element_selector):
            return self.get_element(element_selector, selector)
        return out

    def page_loaded(self, driver):
        """
        Check if page is loaded by running a javascript command to check if it's loaded.

        :param driver: chrome driver
        :return: driver execution result
        """
        return driver.execute_script("return document.readyState === 'complete';")

    def scroll_to_end(self, object_to_select, selector: str, timeout: int, num_items: int = None):
        """
        Grab next item that fits selector, continue to scroll page items are collected.

        :param selector: selector for item to get
        :param timeout:
        :param num_items:
        :return:
        """
        script = """
    const elem = arguments[0];
    if(elem === null) {
        return elem;
    }
    elem.scrollIntoView();
    elem.classList.add("scraped");
    elem.style.backgroundColor = "red";
    return elem;
    """
        iterations = 0
        while True:
            try:
                element = WebDriverWait(object_to_select, timeout).until(self.element_present(f"{selector}:not(.scraped)"))
            except TimeoutException:
                break
            yield element

            self.driver.execute_script(script, element)
            iterations += 1
            if num_items is not None and num_items <= iterations:
                break

    def collect_main_links(self):
        self.driver.get("https://disclosures.utah.gov/Search/PublicSearch")
        WebDriverWait(self.driver, 15, 0.25).until(self.page_loaded)
        tab_ids = ["ELECT"] #['PCC', 'CORP', 'ELECT', 'INDEXP', 'LABOR', 'PAC', 'PIC', 'PARTY']
        discovered_links = []
        for item in self.scroll_to_end(self.driver, ".ui-accordion-header", 8):
            item.click()

        #store links from each tab section
        for tab_id in tab_ids:
            print(tab_id)
            WebDriverWait(self.driver, 8).until(self.element_present(f"html body div#wrapper div#main div#rightColumn div#content div.searchBoxContainerSolid div#accordion.ui-accordion.ui-widget.ui-helper-reset.ui-accordion-icons div.loadContainer.{tab_id}.ui-accordion-content.ui-helper-reset.ui-widget-content.ui-corner-bottom fieldset ul.dis-searchlist"))
            alphabetical_sections = self.driver.find_elements(By.CSS_SELECTOR, f"html body div#wrapper div#main div#rightColumn div#content div.searchBoxContainerSolid div#accordion.ui-accordion.ui-widget.ui-helper-reset.ui-accordion-icons div.loadContainer.{tab_id}.ui-accordion-content.ui-helper-reset.ui-widget-content.ui-corner-bottom fieldset ul.dis-searchlist")
            for individual_alphabetical_sections in alphabetical_sections:

                for individual_link in self.scroll_to_end(individual_alphabetical_sections, "a", .6):
                    discovered_links.append(individual_link.get_attribute('href'))

        print(len(discovered_links))

        #download from each link
        for individual_link in discovered_links:
            try:
                self.driver.get(individual_link)
                WebDriverWait(self.driver, 15, 0.25).until(self.page_loaded)
                # file_to_download_obj = self.driver.find_element(By.XPATH, "/html/body/div[2]/div[2]/div[2]/div[2]/div/div/ul[3]/li/a")
                # file_to_download_obj.click()
                # time.sleep(1)
                year_tabs = self.driver.find_elements(By.CSS_SELECTOR, ".ui-state-default.ui-corner-top a")
                for tab in year_tabs:
                    print(tab.get_attribute('innerHTML'))
                    tab.click()
                    time.sleep(2)
                    links = self.driver.find_elements(By.CSS_SELECTOR, ".dis-csv-list li a")
                    print(len(links))
                    file_to_download_obj = links[len(links)-1]
                    file_to_download_obj.click()
                    time.sleep(1)
                    # dialogue_container_css = ".ui-dialog.ui-widget.ui-widget-content"
                    # dialogue_button_css = ".ui-button.ui-widget.ui-state-default.ui-corner-all.ui-button-text-only"
                    # dialog_button = self.driver.find_element(By.CSS_SELECTOR, f"{dialogue_container_css}>button{dialogue_button_css}")
                    # dialog_button.click()

            except Exception as e:
                # pass
                print(e)

       #self.driver.quit()

if __name__ == '__main__':
    driver_obj = main_driver()
    driver_obj.collect_main_links()

 