import time
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from my_class import ChromeDriver


def scrape_amazon():

    interval: int = 300  # 無限ループで調査する案件のインターバル
    count: int = 1

    while True:

        chrome_driver = ChromeDriver()
        chrome_driver.log(f"{count}回目のスクレイピング開始")
        url_count: int = len(chrome_driver.target_urls)
        chrome_driver.log(f"調査対象url数:{url_count}")

        with ThreadPoolExecutor(max_workers=url_count) as executor:
            futures: list = [
                executor.submit(chrome_driver.check_item_stock, url)
                for url in chrome_driver.target_urls
            ]
            wait(futures, return_when=ALL_COMPLETED)
            chrome_driver.log("全件スクレイピング処理完了")

        chrome_driver.to_csv(chrome_driver.result)
        chrome_driver.log(f"{count}回目結果のCSV書き込み完了")

        time.sleep(interval)
        count += 1


if __name__ == "__main__":
    scrape_amazon()
