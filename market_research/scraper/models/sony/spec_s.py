from bs4 import BeautifulSoup
import requests
import time
import pandas as pd
from tqdm import tqdm
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from market_research.tools import FileManager
from market_research.scraper._scaper_scheme import Scraper

class ModelScraper_s(Scraper):
    def __init__(self, enable_headless=True,
                 export_prefix="model_sony_gobal", intput_folder_path="input",  output_folder_path="results",
                 verbose: bool = False, wait_time=2):

        super().__init__(enable_headless=enable_headless, export_prefix=export_prefix,  intput_folder_path=intput_folder_path, output_folder_path=output_folder_path)

        self.tracking_log = verbose
        self.wait_time = wait_time
        self.file_manager = FileManager
        self.log_dir = "logs/sony/models"
        if self.tracking_log:
            FileManager.make_dir(self.log_dir)

    def get_models_info(self, foramt_output:str='df', fastmode:bool=False):
        url_series_set = self._get_url_series()
        url_series_dict = {}
        for url in url_series_set:
            url_models = self._get_models(url=url)
            url_series_dict.update(url_models)
        print("number of total model:", len(url_series_dict))

        if fastmode:
            model_list = list(url_series_dict.keys())
            return model_list

        dict_models = {}
        for key, url_model in tqdm(url_series_dict.items()):
            try:
                dict_info = self._get_model_info(url_model)
                dict_models[key] = dict_info
                dict_spec = self._get_global_spec(url=url_model)
                dict_models[key].update(dict_spec)
            except Exception as e:
                print(f"Failed to get info from {key}")
                pass

        if foramt_output == "df":
            df_models = pd.DataFrame.from_dict(dict_models).T
            FileManager.df_to_excel(df_models.reset_index(), file_name=self.output_xlsx_name, sheet_name="raw_na", mode='w')
            return df_models
        else:
            return dict_models


    def _get_url_series(self) -> set:
        """
        Get the series URLs by scrolling down the main page.
        """
        url = "https://electronics.sony.com/tv-video/televisions/c/all-tvs/"
        prefix = "https://electronics.sony.com/"
        step = 200
        url_series = set()
        try_total = 5
        for _ in range(try_total):
            driver = self.web_driver.get_chrome()
            try:
                driver.get(url=url)
                time.sleep(self.wait_time)
                scroll_distance_total = self.web_driver.get_scroll_distance_total()
                scroll_distance = 0

                while scroll_distance < scroll_distance_total:
                    for _ in range(2):
                        html = driver.page_source
                        soup = BeautifulSoup(html, 'html.parser')
                        elements = soup.find_all('a', class_="custom-product-grid-item__product-name")
                        for element in elements:
                            url_series.add(prefix + element['href'].strip())
                        driver.execute_script(f"window.scrollBy(0, {step});")
                        time.sleep(self.wait_time)
                        scroll_distance += step
                driver.quit()
                break
            except Exception as e:
                driver.quit()
                print(f"Try collecting {_ + 1}/{try_total}")
                # print(e)
        print("The website scan has been completed.")
        print(f"number of total series: {len(url_series)}")
        return url_series

    def _get_models(self, url: str, prefix="https://electronics.sony.com/", static_mode=True) -> dict:
        """
        Extract all model URLs from a given series URL.
        """
        try_total = 5
        for cnt_try in range(try_total):
            try:
                dict_url_models = {}
                for _ in range(3):
                    if static_mode:
                        response = requests.get(url)
                        page_content = response.text
                    else:
                        driver = self.web_driver.get_chrome()
                        driver.get(url=url)
                        time.sleep(self.wait_time)
                        page_content = driver.page_source
                    soup = BeautifulSoup(page_content, 'html.parser')
                    elements = soup.find_all('a', class_='custom-variant-selector__item')

                    for element in elements:
                        try:
                            element_url = prefix + element['href']
                            label = self.file_manager.get_name_from_url(element_url)
                            dict_url_models[label] = element_url.strip()
                        except Exception as e:
                            print(f"Getting series error ({e})")
                            pass
                if self.tracking_log:
                    print(f"SONY {self.file_manager.get_name_from_url(url)[4:]} series: {len(dict_url_models)}")
                for key, value in dict_url_models.items():
                    if self.tracking_log:
                        print(f'{key}: {value}')
                return dict_url_models
            except Exception as e:
                print(f"_get_models try: {cnt_try + 1}/{try_total}")

    def _get_model_info(self, url: str) -> dict:
        """
        Extract model information (name, price, description) from a given model URL.
        """
        response = requests.get(url)
        if self.tracking_log:
            print(" Connecting to", url)
        page_content = response.text
        soup = BeautifulSoup(page_content, 'html.parser')
        dict_info = {}
        label = soup.find('h2', class_='product-intro__code').text.strip()
        dict_info["model"] = label.split()[-1]
        dict_info["price"] = soup.find('div', class_='custom-product-summary__price').text.strip()
        dict_info.update(self._extract_model_info(dict_info.get("model")))
        dict_info["description"] = soup.find('h1', class_='product-intro__title').text.strip()
        return dict_info

    def _get_global_spec(self, url: str) -> dict:
        """
        Extract global specifications from a given model URL.
        """
        try_total = 10
        model = None
        driver = None
        for cnt_try in range(try_total):
            try:
                dict_spec = {}
                driver = self.web_driver.get_chrome()
                driver.get(url=url)
                model = self.file_manager.get_name_from_url(url)
                dir_model = f"{self.log_dir}/{model}"
                stamp_today = self.file_manager.get_datetime_info(include_time=False)
                stamp_url = self.file_manager.get_name_from_url(url)
                if self.tracking_log:
                    self.file_manager.make_dir(dir_model)
                if self.tracking_log:
                    driver.save_screenshot(f"./{dir_model}/{stamp_url}_0_model_{stamp_today}.png")
                time.sleep(self.wait_time)

                element_spec = driver.find_element(By.ID, "PDPSpecificationsLink")
                self.web_driver.move_element_to_center(element_spec)
                if self.tracking_log:
                    driver.save_screenshot(f"./{dir_model}/{stamp_url}_1_move_to_spec_{stamp_today}.png")
                time.sleep(self.wait_time)

                element_click_spec = driver.find_element(By.ID, 'PDPSpecificationsLink')
                element_click_spec.click()
                time.sleep(self.wait_time)

                if self.tracking_log:
                    driver.save_screenshot(
                        f"./{dir_model}/{stamp_url}_2_after_click_specification_{stamp_today}.png")
                try:
                    element_see_more = driver.find_element(By.XPATH,'//*[@id="PDPOveriewLink"]/div[1]/div/div/div[2]/div/app-product-specification/div/div[2]/div[3]/button')
                    self.web_driver.move_element_to_center(element_see_more)
                    if self.tracking_log:
                        driver.save_screenshot(f"./{dir_model}/{stamp_url}_3_after_click_see_more_{stamp_today}.png")
                    element_see_more.click()
                except:
                    if self.tracking_log:
                        print("Cannot find the 'see more' button on the page; trying to search for another method.")
                    element_see_more = driver.find_element(By.XPATH,
                                                            '//*[@id="PDPOveriewLink"]/div[1]/div/div/div[2]/div/app-product-specification/div/div[2]/div[2]/button')
                    self.web_driver.move_element_to_center(element_see_more)
                    if self.tracking_log:
                        driver.save_screenshot(
                            f"./{dir_model}/{stamp_url}_3_after_click_see_more_{stamp_today}.png")
                    element_see_more.click()
                time.sleep(self.wait_time)
                driver.find_element(By.ID, "ngb-nav-0-panel").click()
                for _ in range(15):
                    elements = driver.find_elements(By.CLASS_NAME,"full-specifications__specifications-single-card__sub-list")
                    for element in elements:
                        soup = BeautifulSoup(element.get_attribute("innerHTML"), 'html.parser')
                        dict_spec.update(self._soup_to_dict(soup))
                    ActionChains(driver).key_down(Keys.PAGE_DOWN).perform()
                if self.tracking_log:
                    driver.save_screenshot(f"./{dir_model}/{stamp_url}_4_end_{stamp_today}.png")
                driver.quit()
                if self.tracking_log:
                    print(f"Received information from {url}")
                return dict_spec
            except Exception as e:
                print(f"An error occurred on page 3rd : {model} try {cnt_try + 1}/{try_total}")
                print(e)
                driver.quit()
                pass

    def _extract_model_info(self, model):
        """
        Extract additional information from the model name.
        """
        dict_info = {}
        dict_info["year"] = model.split("-")[1][-1]
        dict_info["series"] = model.split("-")[1][2:-1]
        dict_info["size"] = model.split("-")[1][:2]
        dict_info["grade"] = model.split("-")[0]

        year_mapping = {
            "N": 2025,
            "M": 2024,
            'L': 2023,
            'K': 2022,
            'J': 2021,
            # Add additional mappings as needed
        }

        try:
            dict_info["year"] = year_mapping.get(dict_info.get("year"))
        except:
            dict_info["year"] = ""

        return dict_info

    def _soup_to_dict(self, soup):
        """
        Convert BeautifulSoup soup to dictionary.
        """
        try:
            h4_tag = soup.find('h4').text.strip()
            p_tag = soup.find('p').text.strip()
        except :
            try:
                h4_tag = soup.find('h4').text.strip()
                p_tag = ""
            except Exception as e:
                print("Parser error", e)
                h4_tag = "Parser error"
                p_tag = "Parser error"
        return {h4_tag: p_tag}
