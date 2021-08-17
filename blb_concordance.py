from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time


class BLBConcordance:
    def __init__(self):
        self.browser = self.setWebDriver()
        self.pagesTag = []
        self.ref = []
        self.verse = []
        print('---- Blue Letter Bible Concordance -----\n')

    def setWebDriver(self):
        print("\nSetting up web driver...\n")
        path = {'.\chromedriver_win32\chromedriver.exe'}
        options = Options()
        options.add_argument("--incognito --headless")
        return webdriver.Chrome(path, options=options)

    def getSearchInput(self):
        self.searchTerm = input('Enter search term: ')

    # Check if there is any result to the search term throw if there is none
    def checkResult(self):
        self.browser.get(
            f'https://www.blueletterbible.org/search/search.cfm?Criteria="{self.searchTerm}"&t=KJV#s=s_primary_0_1'
        )
        try:
            result = self.browser.find_element_by_css_selector(
                "div.columns.tablet-2.tablet-order-2.show-for-tablet.text-center"
            )
            return True
        except NoSuchElementException:
            print(f'There is no result for {self.searchTerm}')
            return False

    # Get the result pagination
    def scrapResultPage(self):
        self.pages = self.browser.find_elements_by_css_selector(
            '#pageCont_TR > td > p')
        if (self.pages != []):
            for button in self.pages:
                tag = button.find_element_by_tag_name('a').get_attribute('rel')
                self.pagesTag.append(tag)
        else:
            # Append one page to the pagesTag if there is no pagination
            self.pagesTag.append("s_primary_0_1")

    # Split ref - verse into ref, verse
    def splitRefandVerse(self, verse):
        parts = verse.split("\n")[1].split("-")
        self.ref.append(parts[0])
        self.verse.append(parts[1])

    # Get all references from all pagination
    def scrapReferences(self):
        startTime = time.time()

        if (self.checkResult()):
            print('\nScraping references...\n')
            self.scrapResultPage()

            for tag in self.pagesTag:

                # Go to specific result page
                url = f'https://www.blueletterbible.org/search/search.cfm?Criteria="{self.searchTerm}"&t=KJV#s={tag}'
                self.browser.get(url)

                # Wait for result dom to load
                try:
                    delay = 5  # seconds
                    WebDriverWait(self.browser, delay).until(
                        EC.visibility_of_all_elements_located(
                            (By.CSS_SELECTOR, "div.tools.row.align-middle")))
                except TimeoutException:
                    print(tag)

                # Retrieve all result dom elements
                verses = self.browser.find_elements_by_css_selector(
                    "div.tools.row.align-middle")

                # Split and store references and verses
                for verse in verses:
                    self.splitRefandVerse(str(verse.text))

            print('\nFinished scraping references...\n')

            # Combine references and verses into a dictionary
            data = {"reference": self.ref, "verse": self.verse}

            # Print scraping time
            print(
                f'----- Scraping time: {round((time.time() - startTime),2)} seconds -----'
            )
            return data
        else:
            return None

    # def splitRefandVerse(self, verse):
    #     parts = verse.split("-")
    #     self.ref.append(parts[0])
    #     self.verse.append(parts[1])

    # def scrapReferences(self):
    #     action = ActionChains(self.browser)
    #     startTime = time.time()

    #     if (self.checkResult()):
    #         print('\nScraping references...\n')
    #         self.scrapResultPage()

    #         for tag in self.pagesTag:

    #             # Go to specific result page
    #             url = f'https://www.blueletterbible.org/search/search.cfm?Criteria="{self.searchTerm}"&t=KJV#s={tag}'
    #             self.browser.get(url)

    #             try:
    #                 delay = 5  # seconds
    #                 WebDriverWait(self.browser, delay).until(
    #                     EC.visibility_of_all_elements_located(
    #                         (By.CSS_SELECTOR, "div.tools.row.align-middle")))
    #             except TimeoutException:
    #                 print(tag)

    #             # Check all verses into clipboard
    #             selectCheckBoxes = self.browser.find_elements_by_css_selector(
    #                 "img.copyBox.selected")
    #             for box in selectCheckBoxes:
    #                 box.click()

    #             # Split and store references and verses
    #             verses = self.browser.find_element_by_id(
    #                 "copyAct").get_attribute(
    #                     "data-clipboard-text").splitlines()
    #             for verse in verses:
    #                 self.splitRefandVerse(verse)

    #         print('\nFinished scraping references...\n')

    #         # Combine references and verses into a dictionary
    #         data = {"reference": self.ref, "verse": self.verse}

    #         # Print scraping time
    #         print(
    #             f'----- Scraping time: {round((time.time() - startTime),2)} seconds -----'
    #         )
    #         return data
    #     else:
    #         return None

    # Output the verses and reference into an excel file
    def outputToExcel(self, data):
        df = pd.DataFrame(data)

        with pd.option_context('display.max_rows', None, 'display.max_columns',
                               None):
            print(df)

        outputToExcel = input('\nOutput to an excel file? [Y] / [N] : ')
        if (outputToExcel == 'Y' or outputToExcel == 'y'):
            fileName = f'BLB-{self.searchTerm}'
            df.to_excel(f'{fileName}.xlsx', sheet_name=fileName)
            print(f'\nFinished output to excel filename: {fileName}.xlsx\n')

    # Destroy webdriver
    def tearDown(self):
        self.browser.close()
        print('\n----- THE END -----\n')


if __name__ == '__main__':
    concordance = BLBConcordance()
    concordance.getSearchInput()
    res = concordance.scrapReferences()
    if (res != None):
        concordance.outputToExcel(res)
    concordance.tearDown()