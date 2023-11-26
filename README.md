이 프로젝트는 웹사이트에서 제품 모델 사양을 가져오고 분석하는 기능을 제공합니다.

## 실행 데모
이 프로젝트는 웹사이트에서 제품 정보를 수집하고 분석 합니다.
사용법은 아래의 note를 참고 하세요.
> **Demo Note book**  
> [market model information](https://colab.research.google.com/github/xikest/research_market_tv/blob/main/quick_guide_market_models.ipynb)  
> [model scores & measurement](https://colab.research.google.com/github/xikest/research_market_tv/blob/main/quick_guide_market_rtings.ipynb)  
> [text analysis](https://colab.research.google.com/github/xikest/research_market_tv/blob/main/quick_guide_textanalysis.ipynb)


## 주의사항
Selenium을 사용하여 웹 스크래핑을 수행하므로 Chrome 웹 드라이버가 필요합니다.   
Chrome 웹 드라이버를 설치하고 경로를 올바르게 설정해야 합니다.

## 설치
프로젝트를 사용하기 위해 다음 단계를 따르세요  
다음 명령을 실행하여 라이브러리를 설치합니다

```bash
pip install -U mkt-retv
```

다음 코드로 필요한 패키지 및 도구를 설치 합니다.

```python
from market_research.tools.installer import Installer
Installer.install_chrome_and_driver()
```

## 라이선스
이 프로젝트는 MIT 라이선스를 따릅니다.

## 후원
만약 이 프로젝트가 도움이 되었다면, 커피 한 잔의 후원은 큰 격려가 됩니다. ☕️

