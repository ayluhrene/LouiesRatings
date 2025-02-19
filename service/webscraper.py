from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
import pandas as pd

# for multithreading
import concurrent.futures

NAU_CLASS_DISTRIBUTION_URL = "https://www7.nau.edu/pair/reports/ClassDistribution"

# get data iteratively
def get_all_grade_distribution_data():
    # store sata here
    class_distr_data = list()

    service = Service()
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(NAU_CLASS_DISTRIBUTION_URL)

    # wait until subject term is done loading
    WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.NAME, "ctl00$MainContent$TermList")))
    # select term by name (skip default)
    term_select_element = Select(driver.find_element(By.NAME, "ctl00$MainContent$TermList"))
    for term_idx in range(1, len(term_select_element.options)):
        # get the selected term name
        term = term_select_element.options[term_idx].text

        # select term
        term_select_element.select_by_index(term_idx)

        # wait until subject select is done loading
        WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.NAME, "ctl00$MainContent$SubjectList")))
         # select subject by name
        subject_select_element = Select(driver.find_element(By.NAME, "ctl00$MainContent$SubjectList"))

        """""
        # ---------------------------
        # GRAB ALL CLASSES
        # ---------------------------
        for subject_idx in range(0, len(subject_select_element.options)):
            # get the selected subject name
            subject = subject_select_element.options[subject_idx].text

            # select subject
            subject_select_element.select_by_index(subject_idx)
        # ---------------------------
        """
        # ---------------------------
        # ONLY GRABBING CS CLASSES
        # ---------------------------
        subject_idx = 0
        subject = "CS"
        if subject in [option.text for option in subject_select_element.options]:
            subject_select_element.select_by_visible_text(subject)
        # ---------------------------

            # click submit
            driver.find_element(By.ID, "MainContent_Button1").click()

            # wait until the first table is done loading (max 10 seconds)
            WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.TAG_NAME, "table")))

            # get the html from curent page
            html = driver.page_source

            # use beautful soup to parse
            soup = BeautifulSoup(html, 'html.parser')

            tables = soup.find_all("table")

            # loop through each table
            for table_tag in tables:

                # extract the table
                table = table_tag.find("tbody")

                if table:
                    
                    # loop through each row in the table
                    for row_idx, tr in enumerate(table.find_all("tr")):
                        row_data = [td.text for td in tr.find_all("td")]

                        # skip any rows that are blank
                        if row_data:
                            # assume first row is the header
                            if row_idx == 0:
                                # only need to get the header once
                                if term_idx == 1 and subject_idx == 0:
                                    col_headers = ["Semester", "Subject"] + row_data
                            # otherwise add row to table
                            else:
                                # concat semester and subject info to row data
                                class_distr_data.append([term, subject] + row_data)

                else:
                    print("Table not found.")

            """""
            # go back to select next subject
            driver.back()
            # refetch dropdown
            WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.NAME, "ctl00$MainContent$SubjectList")))
            subject_select_element = Select(driver.find_element(By.NAME, "ctl00$MainContent$SubjectList"))
            """""

        # go back to select next term
        driver.back()
        # refetch dropdown
        WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.NAME, "ctl00$MainContent$TermList")))
        term_select_element = Select(driver.find_element(By.NAME, "ctl00$MainContent$TermList"))
    
    # create data frame
    class_distr_table = pd.DataFrame(class_distr_data, columns=col_headers)

    driver.quit()

    return class_distr_table

# get data in parallel
def get_all_grade_distribution_data_parallel():
    # store data here
    all_class_distr_data = list()

    # open driver for getting all term names
    service = Service()
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(NAU_CLASS_DISTRIBUTION_URL)

    # wait until subject term is done loading
    WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.NAME, "ctl00$MainContent$TermList")))
    # select term by name (skip default)
    term_select_elements = Select(driver.find_element(By.NAME, "ctl00$MainContent$TermList")).options

    # run each webscraping process in parallel for each term
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(fetch_info_single_term, term_select_element.text) for term_select_element in term_select_elements[1:]]
    
    # retreive data
    for future in concurrent.futures.as_completed(futures):
        # add term information to data list
        all_class_distr_data += future.result()
    
    # create data frame
    # class number column header has a space because that is how it is on the website
    col_headers = ["Semester", "Subject", "Class", "Section", "Class NBR ", "Instructor Name", "A", "B", "C", "D", "F", "AU", "P", "NG", "W", "I", "IP", "Pending", "Total"]
    class_distr_table = pd.DataFrame(all_class_distr_data, columns=col_headers)

    class_distr_table["Instructor Name"] = class_distr_table["Instructor Name"].str.split('/')
    class_distr_table = class_distr_table.explode("Instructor Name").reset_index()

    # exit driver
    driver.quit()

    return class_distr_table

    
def fetch_info_single_term(term):
    # store data here
    term_class_distr_data = list()
    col_headers = list()

    # open driver for each thread
    service = Service()
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(NAU_CLASS_DISTRIBUTION_URL)

    # wait until subject term is done loading
    WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.NAME, "ctl00$MainContent$TermList")))
    # get selection box
    term_select_element = Select(driver.find_element(By.NAME, "ctl00$MainContent$TermList"))
    # select term by name
    term_select_element.select_by_visible_text(term)

    # wait until subject select is done loading
    WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.NAME, "ctl00$MainContent$SubjectList")))
        # select subject by name
    subject_select_element = Select(driver.find_element(By.NAME, "ctl00$MainContent$SubjectList"))

    """""
    # ---------------------------
    # GRAB ALL CLASSES
    # ---------------------------
    for subject_idx in range(0, len(subject_select_element.options)):
        # get the selected subject name
        subject = subject_select_element.options[subject_idx].text

        # select subject
        subject_select_element.select_by_index(subject_idx)
    # ---------------------------
    """
    # ---------------------------
    # ONLY GRABBING CS CLASSES
    # ---------------------------
    subject = "CS"
    if subject in [option.text for option in subject_select_element.options]:
        subject_select_element.select_by_visible_text(subject)
    # ---------------------------

        # click submit
        driver.find_element(By.ID, "MainContent_Button1").click()

        # wait until the first table is done loading (max 10 seconds)
        WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.TAG_NAME, "table")))

        # get the html from curent page
        html = driver.page_source

        # use beautful soup to parse
        soup = BeautifulSoup(html, 'html.parser')

        tables = soup.find_all("table")

        # loop through each table
        for table_tag in tables:

            # extract the table
            table = table_tag.find("tbody")

            if table:
                
                # loop through each row in the table
                for row_idx, tr in enumerate(table.find_all("tr")):
                    row_data = [td.text for td in tr.find_all("td")]

                    # skip any rows that are blank
                    if row_data:
                        # assume skip column header
                        if row_idx != 0:
                            # concat semester and subject info to row data
                            term_class_distr_data.append([term, subject] + row_data)

            else:
                print("Table not found.")

        """""
        # go back to select next subject
        driver.back()
        # refetch dropdown
        WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.NAME, "ctl00$MainContent$SubjectList")))
        subject_select_element = Select(driver.find_element(By.NAME, "ctl00$MainContent$SubjectList"))
        """""

    driver.quit()

    return term_class_distr_data

if __name__ == "__main__":
    get_all_grade_distribution_data_parallel()
