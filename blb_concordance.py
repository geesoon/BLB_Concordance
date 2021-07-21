from os import P_DETACH
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
import pandas as pd


class BLBConcordance:
    def __init__(self):
        self.browser = self.setWebDriver()
        self.pagesTag = []
        print('---- Blue Letter Bible Concordance -----\n')

    def setWebDriver(self):
        print("\nSetting up web driver...\n")
        path = {'.\chromedriver_win32\chromedriver.exe'}
        options = Options()
        options.add_argument("--incognito --headless")
        return webdriver.Chrome(path, options=options)

    def getSearchInput(self):
        self.searchTerm = input('Enter search term: ')

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

    # Get all references from all pagination
    def scrapReferences(self):
        if (self.checkResult()):
            print('\nScraping references...\n')

            self.scrapResultPage()
            verseSelector = 'div.columns.tablet-2.tablet-order-2.show-for-tablet.text-center > p > a'

            refs = []

            for tag in self.pagesTag:
                url = f'https://www.blueletterbible.org/search/search.cfm?Criteria="{self.searchTerm}"&t=KJV#s={tag}'

                self.browser.get(url)
                try:
                    delay = 5  # seconds
                    WebDriverWait(self.browser, delay).until(
                        EC.visibility_of_all_elements_located((
                            By.CSS_SELECTOR,
                            "div.columns.tablet-2.tablet-order-2.show-for-tablet.text-center"
                        )))
                except TimeoutException:
                    print(tag)

                ref = self.browser.find_elements_by_css_selector(verseSelector)
                for el in ref:
                    refs.append(el.get_attribute('innerHTML'))

            print('\nFinished scraping references...\n')
            return refs
        return None

    # Get multi-verses by multi-references
    def getVersesByReferences(self, refs):
        joinedVerses = self.formatRefs(refs)
        print(joinedVerses)

        print('\nScraping verses...\n')

        self.browser.get('https://blueletterbible.org')
        mvForm = self.browser.find_element_by_id("mvFormWidge")
        mvText = self.browser.find_element_by_id('mvTextWidge')
        mvText.send_keys(joinedVerses)
        mvForm.submit()

        # Change the view to multi-verse view
        try:
            delay = 20  # seconds
            WebDriverWait(self.browser, delay).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "button#formatButton")))

            self.browser.find_element_by_id('formatButton').click()
        except TimeoutException:
            print("Verse loading took too much time!")

        # Scrap verses from the verse list
        allVerses = self.browser.find_elements_by_css_selector(
            'div.scriptureText')
        verses = []
        for verse in allVerses:
            verseParts = verse.text.split("-")
            verses.append(verseParts[1])

        print('\nFinished scraping verses for all references...\n')

        return verses

    # Join the list of reference by ';'
    def formatRefs(self, refs):
        return ";".join(refs)

    # Output the verses and reference into an excel file
    def outputToExcel(self, refs, verses):
        print(f'\nNumber of references scraped: {len(refs)}')
        print(f'Number of verses scraped: {len(verses)}\n')

        data = {'ref': refs, 'verse': verses}
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
    refs = concordance.scrapReferences()
    if (refs != None):
        verses = concordance.getVersesByReferences(refs)
        concordance.outputToExcel(refs, verses)

    concordance.tearDown()


    # TODO
    # Use copy and paste method instead of scraping directly
    # Combine multiple searchTerm result in an excel file