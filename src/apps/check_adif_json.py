#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent

if __name__ == "__main__":
    from fake_useragent import UserAgent

    ua = UserAgent()
    URL = "https://www.adif.es/w/79100-granollers-centre"
    options = Options()
    options.add_argument("--headless")
    options.add_argument(f'user-agent={ua.random}')
    driver = webdriver.Chrome(options=options)
    driver.get(URL)
    with open('granillers.html', 'w') as file:
        file.write(driver.page_source)
    driver.quit()