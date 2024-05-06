import pandas as pd
import numpy as np

class DataCleanup_s:
    """
    cleanup = DataCleanup(df)
    df = cleanup.get_df_cleaned()
    df_prices = cleanup.get_price_df()
    """
    def __init__(self, df, stop_words=None):
        self.df = df.copy()
        self.df_prices = None
        if stop_words is None:
            stop_words = self._call_stop_words()
        self.stop_words = [stop_word.lower() for stop_word in stop_words]
        self.stop_words.extend(["model","size"])
        self._preprocess_df()
        self._create_price_df()
        self._cleanup_columns()

    def _call_stop_words(self):
        stop_words_list = ["price", "description",
                                  "weight", "dimension", "stand", "W x H", "W x H x D", "Wi-Fi", "atore", "audio",
                                  "frame", "length", "qty",
                                  "power", "usb", "channels", "language", "timer", "apple", "TALKBACK", "voice", "sensor",
                                  "system", "channel", "storage", "cable",
                                  "style", "protection", "hdmi", "energy", "sound", "camera", "subwoofer", "satellite",
                                  "input", "output", "caption", "headphone", "radio", "text", "internet", "dsee", "speaker",
                                  "bluetooth", "accessories", "mercury", "remote", "smart", "acoustic", "support",
                                  "wallmount", "network", "android", "ios", "miracast",
                                  "operating", "store", "clock", "rs-232c", "menu", "mute", "4:3", "hdcp",
                                  "built", "tuners", "demo", "presence", "switch", "reader", "face", "surround", "phase",
                                  "batteries", "info", "Parental", "setup", "aspect", "dashboard", "formats", "accessibility",
                                  "ci+",
                                  "bass", "shut", "sorplas", "volume", "wireless", "china",
                                  "hole", "program", "manual", "latency",
                                  "twin","h x v", "motion","calman"]
        return stop_words_list


    def _preprocess_df(self):
        self.df = self.df.sort_values(["year", "series", "size", "grade"], axis=0, ascending=False)
        def transform_text(x):
            if isinstance(x, str):
                x = x.replace("  ", " ")  # 두 개의 공백을 하나로 변경
                x = x.replace("™", "")  # ™ 제거
                x = x.replace("®", "")  # ® 제거
                x = x.replace("\n\n", "\n ")  # 이중 줄바꿈을 단일 줄바꿈으로 변경
                x = x.replace(" \n", "\n ")  # 공백 후 줄바꿈 처리
                x = x.strip()  # 앞뒤 공백 제거
                x = x.lower()  # 모두 소문자로 변경
            return x

        self.df = self.df.applymap(transform_text)
        self.df.columns = [transform_text(x) for x in self.df.columns]

    def _create_price_df(self):
        # 가격 데이터 추출 및 분리
        def parse_prices(price):
            if isinstance(price, str) and len(price) > 0:
                price_parts = price.split(" ")
                if len(price_parts) < 2:
                    return [price_parts[0], price_parts[0]]
                return price_parts
            return np.nan

        ds_prices = self.df['price'].apply(parse_prices).dropna()

        # 가격 정보 리스트로 변환 및 할인율 계산
        list_prices = [
            [idx, prices[0], prices[1],
             (1 - float(prices[0].replace(',', '').replace('$', '')) /
              float(prices[1].replace(',', '').replace('$', ''))) * 100]
            for idx, prices in zip(ds_prices.index, ds_prices.values)]

        # 새로운 DataFrame 생성
        df_prices = pd.DataFrame(list_prices, columns=["idx", "price_now", "price_release", "price_discount"])
        df_prices.set_index("idx", inplace=True)

        # 원래 DataFrame과 병합
        self.df = pd.merge(df_prices, self.df, left_index=True, right_index=True, how='right').drop(["price"], axis=1)

        # 관련된 열만 선택
        self.df_prices = self.df[
            ["year", "display type", "size", "series", "model", "price_release", "price_now", "price_discount",
             "description"]
        ]


    def get_price_df(self):
        if self.df_prices is not None:
            return self.df_prices.sort_values(["price_discount", "year", "display type", "series", "size", ],
                                              ascending=False)

    def _cleanup_columns(self):
        col_remove = []
        for column in self.df.columns:
            for stop_word in self.stop_words:
                if stop_word in column:
                    col_remove.append(column)
        self.df = self.df.drop(col_remove, axis=1)
        self.df = self.df.drop_duplicates()
        self.df = pd.merge(self.df_prices[['model', 'size']], self.df, left_index=True, right_index=True)

    def get_df_cleaned(self):
        if self.df is not None:
            df = self.df.set_index(["year", "series", "display type"]).drop(
                ["model", "size", "grade"], axis=1)
            df = df.fillna("-")
            return df