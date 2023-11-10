from selenium.webdriver.common.by import By
from ..tools.webdriver import WebDriver
from ..tools.functions import *
import time

class Score():
    def __init__(self):
        self.dictUrlModel = {"sony":"https://www.rtings.com/tv/reviews/sony/",
                             "lge":"",
                             "panasonic":"",
                             "hisense":"",
                             "tpv":"",
                             "sharp":""}

        pass

    def getRthinsScore(self, prefix:str="https://www.rtings.com/tv/reviews/sony/",
                           series:str="x85k", maker=None, trackingLog=False) -> dict:

        # Chrome WebDriver 생성
        wd = WebDriver.getChrome()

        if maker != None:
            try:
                prefix = self.dictUrlModel.get(maker)
            except:
                pass

        url = prefix + series
        url = url.lower()
        if trackingLog == True:
            print(f"TV score info: {url}")
        # 웹 페이지 로드
        wd.get(url)
        time.sleep(1)

        # scorecard-row-content 클래스를 가진 요소들을 선택
        elements = wd.find_elements(By.CLASS_NAME, "scorecard-row-content")

        # 결과를 저장할 딕셔너리 초기화
        dictScores = {}

        try:
            for element in elements:
                label = element.find_element(By.CLASS_NAME, 'scorecard-row-name').text.strip()
                score = element.find_element(By.CLASS_NAME, 'e-score_box-value ').text.strip()
                dictScores[label] = score

            # WebDriver 종료
            wd.quit()
            return dictScores

        except Exception as e:
            print(f"get specification error: {e}")
            # WebDriver 종료
            wd.quit()

            return dictScores

