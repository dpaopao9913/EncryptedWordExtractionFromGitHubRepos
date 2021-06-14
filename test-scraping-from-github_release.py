import json
import requests
import csv
import time
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
import re
import os
import git


g_year = ["2018", "2019", "2020", "2021"]
g_month = ["01","02","03","04","05","06","07","08","09","10","11","12"]
g_language = ["Python"]
g_sleep_intreval = 7

chrome_driver_path = 'chrome driver path'

# git関連の設定
repository_path = 'repository name'
if not os.path.isdir(repository_path):
    git.Git().clone("https://<api access token>:x-oauth-basic@github.com/<your github domain>/" + repository_path + ".git")
else:
    pass


# ファイル出力パス
filename_encrypted_words = 'encrypted_words.csv'
filename_extracted_repos = 'extracted_repos.csv'
g_encrypted_words_path = os.getcwd() + '/' + filename_encrypted_words
g_extracted_repos_path = os.getcwd() + '/' + filename_extracted_repos

# 前回までで暗号化抽出済みのレポジトリURLがあれば読み込む
g_already_searched_repos_list = []
if os.path.isfile(filename_extracted_repos):
    with open(filename_extracted_repos) as f:
        reader = csv.reader(f, delimiter='\n')
        for row in reader:
            g_already_searched_repos_list.append(row[0])
    print(g_already_searched_repos_list)
else:
    print('暗号化抽出済みのレポジトリURLリストはありません')



def git_push(filename):
    """
    addしてcommitしてpushする関数
    """
    try:
        repo = git.Repo.init()
        repo.index.add(filename)
        commit_phrase = 'add ' + filename
        repo.index.commit(commit_phrase)
        origin = repo.remote(name="origin")
        origin.push()
        return "Success"
        
    except:
        return "Error"




###################################################### 本番用関数 ######################################################

# driver が開いているURLに含まれるリンクをすべて再帰的に走査して、コードが書かれているファイルをすべてリスト code_file_name_list に追加する
def getCodeFileNameList(driver_current_url, code_lines, links_in_repo, code_file_name_list):
    
    if len(code_lines) != 0:                                # コードファイルである
        code_file_name_list.append(driver_current_url)
    else:                                                   # コードファイルではない
        # 再帰的にこのリンクを辿っていき、コードファイルを見つけたら、そのURLをリストに追加
        for link in links_in_repo:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument("--no-sandbox")
            options.add_argument("--log-level=3")
            options.add_argument("--disable-dev-shm-usage")
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            driver_2 = webdriver.Chrome(chrome_driver_path, options=options)  # 今は chrome_options= ではなく options=

            driver_2.get(link)

            ################## 再帰中のエラー'StaleElementReferenceException'回避用に準備 ##################
            driver_current_url_2 = driver_2.current_url

            # code_lines の要素があれば、driver が開いているURLはコードファイル
            code_lines_2 = driver_2.find_elements_by_xpath('//table[@class="highlight tab-size js-file-line-container"]')
            
            # links_in_repo の要素があれば、driver が開いているURLはフォルダ（またはその他ファイル）
            aaa = driver_2.find_elements_by_xpath('//a[@class="js-navigation-open Link--primary"]')

            # 'StaleElementReferenceException'エラー回避用
            try:
                links_in_repo_2 = [i.get_attribute('href') for i in aaa]
            except StaleElementReferenceException:
                print("StaleElementReferenceException が再帰中に発生しました。再試行します")
                aaa = driver_2.find_elements_by_xpath('//a[@class="js-navigation-open Link--primary"]')
                links_in_repo_2 = [i.get_attribute('href') for i in aaa]
            ##################################################################################################

            # リンク先のファイル数が多すぎたら、処理時間の都合上スキップする
            max_link_num = 30
            if len(links_in_repo_2) <= max_link_num:
              getCodeFileNameList(driver_current_url_2, code_lines_2, links_in_repo_2, code_file_name_list)
            else:
              print('%s のリンク数が多すぎる（%d 個）ためスキップ' % (link, len(links_in_repo_2)))
            
            driver_2.close()

    


# code_line に暗号化された文字列が含まれているかどうかチェック
#   IsEncrypted           : F=含まれていない, T=含まれている
#   encrypted_word_list   : 暗号化された文字列（Fの場合は''）
def checkEncryptedWord(code_line):
    
    IsEncrypted = False
    encrypted_word_list = []

    # 暗号化文字列の特例に使うパラメータ
    word_length_lower_limit = 25
    word_length_upper_limit = 45
    isIncludeDigit = False
    isIncludeAlphabet = False


    #################  独自のアルゴリズム  ################################
    temp_list = re.findall('[a-z0-9\+=]+', code_line, flags=re.IGNORECASE)

    for word in temp_list:
        if word_length_lower_limit <= len(word) and len(word) <= word_length_upper_limit: # 文字列の長さをチェック
            isIncludeDigit = bool(re.search(r'\d', word))
            isIncludeAlphabet = bool(re.search(r'[a-zA-Z]', word))
            if isIncludeDigit and isIncludeAlphabet:                   # 文字列に英字と数字両方あるかどうかチェック
                encrypted_word_list.append(word)
    #######################################################################

    if len(encrypted_word_list) != 0:
        IsEncrypted = True
    
    return IsEncrypted, encrypted_word_list




#####################################################################################################
# 
# Scraping code from GitHub repositories
# https://blog.codecamp.jp/python-github-autoaggregate / https://www.youtube.com/watch?v=xfcgLHselcY
# API  sample_URL = "https://api.github.com/search/repositories?q=created%3A" + 2018-01 + "+language%3A" + Dart
#
#####################################################################################################
def extractEncryptedStringFromGithub():
    for l in g_language:
        print(l)
        for y in g_year:
            for m in g_month:
                for page_n in range(10):
                    check_point = y + "年" + m + "月"
                    print(check_point)
                    url = "https://api.github.com/search/repositories?q=created%3A" + y + "-" + m + "+language%3A" + l + "&per_page=100&page=" + str(page_n+1)
                    print('query: %s' % url)

                    # 時間計測開始
                    start_page_n = time.time()

                    response = requests.get(url)

                    data = json.loads(response.text)
                    print("total_count: %d" % (data['total_count']))
                    print("result num: %d" % (len(data['items'])))


                    for person_n in range(len(data['items'])):
                        # [n]番目の人物のレポジトリURLを取得
                        repos_url = data['items'][person_n]['owner']['repos_url']

                        # [n]番目の人物のユーザー名とレポジトリ名を取得
                        user_name = data['items'][person_n]['owner']['login']
                        repository_name = data['items'][person_n]['name']

                        print("repo url[%d]: %s" % (person_n, repos_url))
                        print("user name: %s" % (user_name))
                        print("repo name: %s" % (repository_name))

                        # 時間計測開始
                        start_person_n = time.time()

                        # レポジトリURLから言語が「Python」であるURLを取得
                        response = requests.get(repos_url)
                        data2 = json.loads(response.text)

                        # 言語「Python」のリポジトリ数をカウント
                        counter = 0
                        list_rep_urls = []
                        for i in range(len(data2)):
                            if data2[i]['language'] == l:
                                counter += 1
                                temp_url = data2[i]['html_url']
                                print(temp_url)
                                list_rep_urls.append(temp_url)
                        print('lang: %s, repo num: %d' % (l, counter))


                        # レポジトリURLからコードファイルを抽出
                        for rep_url in list_rep_urls:

                            # レポジトリをチェック済みかどうか確認
                            isAlreadyCheckedRepo = False
                            for r_url in g_already_searched_repos_list:
                                if r_url == rep_url:
                                    isAlreadyCheckedRepo = True
                                    print('レポジトリURL: %s をスキップ' % (rep_url))
                                    break
                            if isAlreadyCheckedRepo:
                                continue

                            options = webdriver.ChromeOptions()
                            options.add_argument('--headless')
                            options.add_argument("--no-sandbox")
                            options.add_argument("--log-level=3")
                            options.add_experimental_option('excludeSwitches', ['enable-logging'])
                            driver = webdriver.Chrome(chrome_driver_path, options=options)  # 今は chrome_options= ではなく options=
                            
                            driver.get(rep_url)
                            print('レポジトリURL（ルート）: %s' % (driver.current_url))


                            ######################################################################################
                            #
                            #   HTMLコードの中に、
                            #       <a class="js-navigation-open Link--primary" があれば、このタグ<a>のテキストはファイルリンク
                            #       <table class='highlight tab-size js-file-line-container があれば、このタグ<table>のテキストはプログラミングコード
                            #
                            ######################################################################################

                            # レポジトリ内のファイルリンクを取得
                            links_in_root_repo = driver.find_elements_by_xpath('//a[@class="js-navigation-open Link--primary"]') 
                            print('レポジトリURL（ルート）に含まれるファイル&フォルダ数: %d' % (len(links_in_root_repo)))

                            # stale element reference: element is not attached to the page documentエラー
                            #   https://buralog.jp/python-selenium-stale-element-reference-element-is-not-attached-to-the-page-document-error/                   
                            try:
                                links_in_root_repo_ = [a.get_attribute('href') for a in links_in_root_repo]
                            except StaleElementReferenceException:
                                print("StaleElementReferenceException がルート1で発生しました。再試行します")
                                links_in_root_repo = driver.find_elements_by_xpath('//a[@class="js-navigation-open Link--primary"]')
                                links_in_root_repo_ = [a.get_attribute('href') for a in links_in_root_repo]
                        

                            # 各ファイル名（またはフォルダ名）を取得
                            for link in links_in_root_repo_:
                                driver_tmp = webdriver.Chrome(chrome_driver_path, options=options)
                                driver_tmp.get(link)
                                print('  レポジトリURL: %s' % link)

                                ################## 再帰中のエラー'StaleElementReferenceException'回避用に準備 ##################
                                driver_current_url = driver_tmp.current_url

                                # code_lines の要素があれば、driver が開いているURLはコードファイル
                                code_lines = driver_tmp.find_elements_by_xpath('//table[@class="highlight tab-size js-file-line-container"]')
                                
                                # links_in_repo の要素があれば、driver が開いているURLはフォルダ（またはその他ファイル）
                                aaa = driver_tmp.find_elements_by_xpath('//a[@class="js-navigation-open Link--primary"]')


                                # 'StaleElementReferenceException'エラー回避用
                                try:
                                    links_in_repo = [i.get_attribute('href') for i in aaa]
                                except StaleElementReferenceException:
                                    print("StaleElementReferenceException がルート2で発生しました。再試行します")
                                    aaa = driver_tmp.find_elements_by_xpath('//a[@class="js-navigation-open Link--primary"]')
                                    links_in_repo = [i.get_attribute('href') for i in aaa]
                                ##################################################################################################
            
                                code_file_name_list = []
                                getCodeFileNameList(driver_current_url, code_lines, links_in_repo, code_file_name_list)
                                print('  コードファイルの数（再帰）: %d' % (len(code_file_name_list)))

                                # code_file_name_list の各コードファイルURLにあるプログラミングコードから暗号化された文字列を抽出する
                                for code_file_url in code_file_name_list:
                                    driver_tmp2 = webdriver.Chrome(chrome_driver_path, options=options)
                                    driver_tmp2.get(code_file_url)
                                    code_lines = driver_tmp2.find_elements_by_xpath('//table[@class="highlight tab-size js-file-line-container"]')  # コードの行
                                    
                                    # 1行ずつコードを確認して、暗号化文字列があるかどうか捜索
                                    for cl in code_lines:
                                        # print('line: %s' % cl.text)     # テキストの確認
                                        IsEncrypted, encrypted_word_list = checkEncryptedWord(cl.text)
                                        if IsEncrypted:     # 暗号化された文字列を見つけたら、ファイルへ出力
                                            print(' ***  暗号化文字列を発見: *** ')
                                            with open(g_encrypted_words_path, "a", encoding='utf-8') as f:
                                                f.write(code_file_url + ",")
                                                for encrypted_word in encrypted_word_list:
                                                    f.write(encrypted_word + ",")
                                                    print('  %s' % encrypted_word)
                                                f.write("\n")
                                            # githubへ出力ファイルをプッシュ
                                            git_push(g_encrypted_words_path)

                                    driver_tmp2.close()

                                driver_tmp.close()

                            driver.close()


                            # 暗号化文字列の抽出が完了したレポジトリURLをファイルに書き出す
                            with open(g_extracted_repos_path, "a", encoding='utf-8') as f:
                                f.write(rep_url + "\n")
                            # githubへ出力ファイルをプッシュ
                            git_push(g_extracted_repos_path)


                        # 時間計測終了
                        elapsed_time_person_n = time.time() - start_person_n
                        print ("経過時間:{0}".format(elapsed_time_person_n) + "[sec]")

                        # スリープするかどうかチェック
                        if elapsed_time_person_n < g_sleep_intreval:
                            time.sleep(g_sleep_intreval - elapsed_time_person_n)    # API呼び出し制限：6回/分
            
            
                    # 時間計測終了
                    elapsed_time_page_n = time.time() - start_page_n
                    print ("経過時間:{0}".format(elapsed_time_page_n) + "[sec]")

                    # スリープするかどうかチェック
                    if elapsed_time_page_n < g_sleep_intreval:
                        time.sleep(g_sleep_intreval - elapsed_time_page_n)    # API呼び出し制限：6回/分



if __name__=='__main__':

    extractEncryptedStringFromGithub()