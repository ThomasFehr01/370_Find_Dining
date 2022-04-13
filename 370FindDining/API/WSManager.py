from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options
import re


class WSManager:
    def __init__(self):
        """
        Object to deal with all web scrapping
        """
        self._driver = None

    def startDriver(self):
        """
        Starts the headless firefox driver in selenium to be used for scrapping
        """

        options = Options()
        options.headless = True
        self._driver = webdriver.Firefox(options=options, service=Service(GeckoDriverManager().install()))

    def killDriver(self):
        """
        Ends the connection with the selenium driver
        """
        self._driver.quit()

    def scrapeWeb(self, places):
        """
        Performs the web scrapping for a given list of places
        :param places: formatted as a list of tuples where
            places[0] = place_id
            places[1] = corresponding url
        :return: a dictionary formatted {placeID_1:[about_detail_1, about_detail_2, ...], placeID_2:[...], ...}
        """

        details = {}

        for cPlace in places:
            print('Currently Scrapping:', cPlace[0])
            # Load current place url
            details[cPlace[0]] = {}
            self._driver.get(cPlace[1])

            html = self._driver.page_source

            detailIndex = [m.start() for m in re.finditer('/geo/type/establishment_poi/', html)]

            cTags = []

            for i in detailIndex:
                if (html[html[i:].find('[[') + 1]) != 0:
                    cTags.append(html[i + 28: html[i:].find('\\') + i])

            temp = html.find('<meta content="★')

            if temp == -1:
                details[cPlace[0]]['type'] = 'Restaurant'
            else:
                cType = html[temp + 23: temp + 23 + html[temp + 23:].find('"')]
                details[cPlace[0]]['type'] = cType

            details[cPlace[0]]['tags'] = cTags

        return details
