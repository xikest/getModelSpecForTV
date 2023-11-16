import time
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import re
from ..tools import WebDriver
class Rtings():
    def __init__(self, webdriver_path: str, browser_path: str=None, enable_headless=True):
        self.web_driver = WebDriver(executable_path=webdriver_path, browser_path=browser_path, headless=enable_headless)
        self.wait_time = 1

    def get_score(self, url:str="https://www.rtings.com/tv/reviews/sony/a95l-oled", format_df=True) :
        """
        return type
        -> dict|pd.DataFrame
        """

        driver = self.web_driver.get_chrome()
        maker = url.split("/")[-2]
        model = url.split("/")[-1]
        url = url.lower()
        print(f"connecting to {url} for score")
        # 웹 페이지 로드
        driver.get(url)
        time.sleep(self.wait_time)

        # scorecard-row-content 클래스를 가진 요소들을 선택
        elements = driver.find_elements(By.CLASS_NAME, "scorecard-row-content")
        maker_dict = {}
        try:
            score_dict = {}
            for element in elements:
                label = element.find_element(By.CLASS_NAME, 'scorecard-row-name').text.strip()
                score = element.find_element(By.CLASS_NAME, 'e-score_box-value ').text.strip()
                score_dict[label] = score

            # WebDriver 종료
            driver.quit()

            model_dict = {model:score_dict}
            maker_dict = {maker:model_dict}

            rows = []
            # 딕셔너리를 순회하며 데이터프레임 행으로 추가
            for maker, models in maker_dict.items():
                for model, scores in models.items():
                    for score_type, score in scores.items():
                        rows.append({'Maker': maker, 'Model': model, 'Score Type': score_type, 'Score': score})
            scores_df = pd.DataFrame(rows)
            scores_dict = scores_df.to_dict()
            # print("df")
            # print(dict_data)
            if format_df:
                return scores_df
            else:
                return scores_dict

        except Exception as e:
            print(f"get specification error: {e}")
            # WebDriver 종료
            driver.quit()



    def get_commetns(self, url:str="https://www.rtings.com/tv/reviews/sony/a95l-oled", format_df=True, min_sentence_length = 0):
        """
        return dict or DataFrame

        """

        # Selenium을 사용하여 웹 드라이버 시작
        driver = self.web_driver.get_chrome()
        maker = url.split("/")[-2]
        product = url.split("/")[-1]
        url = url.lower()
        # url = url +"#page-comments"
        print(f"connecting to {url} for comments")
        driver.get(url)
        time.sleep(self.wait_time)
        ## Load More 버튼 열기
        while True:
            try:
                button_div = driver.find_element(By.CLASS_NAME, "comment_list-footer")
                button = button_div.find_element(By.CLASS_NAME, "e-button")
                button.click()
                time.sleep(1)
            except:
                break
        try:
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            comment_contents = soup.find_all('div', class_='comment_list-item-content e-discussion_content is-newest')
            comments_list = []
            for idx, comment_content in enumerate(comment_contents):
                quote_controls = comment_content.find('div', class_='quote-controls')
                if quote_controls:
                    quote_controls.decompose()
                quote_content = comment_content.find('div', class_='quote-content')
                if quote_content:
                    quote_content.decompose()
                comment_text = comment_content.get_text(strip=True, separator='\n')
                comment_text = re.sub(r'https?://\S+', '', comment_text)

                # min_sentence_length 길이 이상의 문장만 분석
                if len(comment_text.split()) >= min_sentence_length:
                    comments_list.append(
                        {'idx': idx, 'maker': maker, 'product': product, 'sentences': comment_text})
            comments_df = pd.DataFrame(comments_list).set_index("idx")
            comments_dict = comments_df.to_dict()
        finally:
            driver.quit()

        if format_df:
            return comments_df
        else:
            return comments_dict

    def get_measurement_reuslts(self, url: str = "https://www.rtings.com/tv/reviews/sony/a95l-oled") ->pd.DataFrame:

        driver = self.web_driver.get_chrome()
        maker = url.split("/")[-2]
        product = url.split("/")[-1]
        url = url.lower()
        print(f"connecting to {url} for detail")
        driver.get(url)
        time.sleep(self.wait_time)
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # 딕셔너리 초기화

        # # product_page-category 텍스트 찾기
        # product_category = test_group.find('a', class_='e-anchor').get_text(strip=True)
        # print(f"product_category: {product_category}")
        # 딕셔너리 초기화
        results_list = []
        category = ""

        test_groups = soup.find_all('div', class_='test_group e-simple_grid-item-2-pad')
        for test_group in test_groups:
            # test_group-category 텍스트 찾기
            # category = test_group.find('div', class_='test_group-category').get_text(strip=True)
            header_element = test_group.find('div', class_='test_group-header')
            category_element = header_element.find('div', class_='test_group-category')
            if category_element:
                category = category_element.get_text(strip=True)
                category_element.extract()
            # span 태그 내의 텍스트 추출 및 '_'로 구분
            scores_headder = '(><)_'.join(header_element.stripped_strings)
            # test_value is-number 찾기
            test_values = test_group.find_all('div', class_='test_value is-number')
            # 리스트 초기화
            for test_value in test_values:
                # test_value-label과 test_result_value 찾기
                label = test_value.find('span', class_='test_value-label').get_text(strip=True)
                result_value = test_value.find('span',
                                               class_='test_result_value e-test_result review-value-score').get_text(strip=True)
                # 딕셔너리에 추가
                results_list.append([maker, product, category, scores_headder, label, result_value])
            # 리스트를 데이터프레임으로 변환


        results_df = pd.DataFrame(results_list,
                                  columns=["maker", "product", "category", "scores_header", "label", "result_value"])
        # scores_header_list 생성 및 수정
        scores_header_list = results_df.scores_header.map(lambda x: x.split("_"))

        scores_header_list_s = []
        for scores_header in scores_header_list:
           if len(scores_header) <2:
               scores_header_list_s.append(["(><)", scores_header[0]])
           else:
               scores_header_list_s.append([scores_header[0], scores_header[1]])

        # print(scores_header_list_s)

           # scores_header_df 생성
        scores_header_df = pd.DataFrame(scores_header_list_s, columns=["score", "header"])
        scores_header_df["score"] = scores_header_df["score"].map(lambda x:x.replace("(><)", ""))
        # results_df와 scores_header_df 병합
        results_df = pd.concat([results_df, scores_header_df], axis=1)
        results_df = results_df[["maker", "product", "category", "header", "score", "label", "result_value"]]
        # 결과 확인

        # print(results_df.head())

        return results_df
            # data_df["category"] = category
            # stacked_df = data_df.set_index('category').set_index('index', append=True).stack()
            # data_df = data_df.set_index(["category", "index"])


        #
        #
        # # 데이터프레임으로 변환
        # df = pd.concat(results).reset_index().drop('index', axis=1)
        # df.columns = ['category', 'label','value']
        # df["maker"] = maker
        # df["product"] = product
        # return df

