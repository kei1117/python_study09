import os
from dotenv import load_dotenv
from datetime import datetime
import time
import tweepy
import pandas as pd


from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import Chrome  # type: ignore
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException


class Utils:
    LOG_FILE_PATH: str = "logs/log_{datetime}.log"
    log_file_path: str = LOG_FILE_PATH.format(
        datetime=datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    )
    EXP_CSV_PATH: str = "results/tweeted_list.csv"

    def __init__(self):
        print("Utils unit")
        self.result: list[str] = []

    def makedir_for_filepath(self, filepath):
        # exist_ok=Trueとすると、フォルダが存在してもエラーにならない
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

    def log(self, txt):
        now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        logStr = "[%s: %s] %s" % ("log", now, txt)
        # ログ出力
        self.makedir_for_filepath(self.log_file_path)
        with open(self.log_file_path, "a", encoding="utf-8_sig") as f:
            f.write(logStr + "\n")
        print(logStr)

    # csv出力
    def to_csv(self, result):
        df = pd.DataFrame(result)
        self.makedir_for_filepath(self.EXP_CSV_PATH)
        df.to_csv(
            self.EXP_CSV_PATH,
            header=False,
            index=False,
            mode="a",
            encoding="utf_8_sig",
        )

    def tweet(self, url: str) -> None:
        # .envファイルを読み込み
        load_dotenv()
        consumer_key: str = os.environ["consumer_key"]
        consumer_secret: str = os.environ["consumer_secret"]
        access_token: str = os.environ["access_token"]
        access_token_secret: str = os.environ["access_token_secret"]

        # Twitterオブジェクトの生成
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)

        now = datetime.now().strftime("%Y年%m月%d日%H時%M分")
        # tweetを投稿
        try:
            api.update_status(f"{now}--在庫あり。{url}")
            self.log(f"[在庫あり_tweet成功] (url: {url})")
            self.result.append(url)
        except Exception as e:
            self.log(f"[在庫あり_tweet失敗:{e}] (url: {url}) ")
            return


class ChromeDriver(Utils):
    def __init__(self):

        print("ChromeDriver init!")
        super().__init__()  # Utilクラスをinit

        # 調査対象のurlを定義しているcsvを読み込み
        try:
            df_target_urls = pd.read_csv(
                "target_urls.csv", header=None, dtype=str, encoding="utf-8-sig"
            )
            self.target_urls: list[str] = list(df_target_urls[0])
        except FileNotFoundError as e:
            self.log(f"[target_urls_listが見つかりません!:{e}]")
            return
        except Exception as e:
            self.log(f"[target_urls_list読み込みエラー:{e}]")
            return

        # 過去にtweet済の案件を保存しているcsvを読み込み
        try:
            df_tweeted_list = pd.read_csv(
                "results/tweeted_list.csv", header=None, dtype=str, encoding="utf-8-sig"
            )
            self.tweeted_list: list[str] = list(df_tweeted_list[0])
        except FileNotFoundError as e:
            self.log(f"[target_urls_listが見つかりません!:{e}]")
            self.tweeted_list = []
        except Exception as e:
            self.log(f"[tweeted_list読み込みエラー:{e}]")
            self.tweeted_list = []

    def set_driver(self):
        USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
        options = Options()

        # 起動オプションの設定
        options.add_argument(f"--user-agent={USER_AGENT}")  # ブラウザの種類を特定するための文字列
        options.add_argument("log-level=3")  # 不要なログを非表示にする
        options.add_argument("--ignore-certificate-errors")  # 不要なログを非表示にする
        options.add_argument("--ignore-ssl-errors")  # 不要なログを非表示にする
        options.add_experimental_option(
            "excludeSwitches", ["enable-logging"]
        )  # 不要なログを非表示にする
        options.add_argument("--incognito")  # シークレットモードの設定を付与
        options.add_argument("--headless")  # ヘッドレスモードの設定を付与

        # ChromeのWebDriverオブジェクトを作成する。
        service = Service(ChromeDriverManager().install())
        return Chrome(service=service, options=options)

    def check_item_stock(self, url: str) -> None:
        driver = self.set_driver()
        driver.get(url)
        time.sleep(3)
        try:
            driver.find_element(By.ID, "add-to-cart-button")
            if url in self.tweeted_list:
                self.log(f"[在庫あり_過去tweet済] (url: {url})")
                return
            else:
                self.tweet(url)
        except NoSuchElementException:
            self.log(f"[在庫なし] (url: {url})")
            if url in self.tweeted_list:
                self.tweeted_list.remove(url)
            return
        except Exception as e:
            self.log(f"[スクレイピングエラー:{e}] (url: {url})")
            return
        finally:
            driver.close()
            driver.quit()
