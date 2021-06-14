# EncryptedWordExtractionFromGitHubRepos

GitHub 上にあるファイルから、暗号化文字列（例：APIキーなど）を自動抽出する<br><br>
Auto extraction program of encrypted strings (i.e. API key) from any files on GitHub.

以下の暗号化文字列の抽出アルゴリズムは一旦それっぽい文字列を抽出できるように書いていますが、適宜お好みで変更して使ってください。<br><br>
The following excrypted word extraction algorithm is just my preference, please change when you use based on your preferences.

<br><br>

```python
#################  独自のアルゴリズム  ################################
  temp_list = re.findall('[a-z0-9\+=]+', code_line, flags=re.IGNORECASE)

  for word in temp_list:
      if word_length_lower_limit <= len(word) and len(word) <= word_length_upper_limit: # 文字列の長さをチェック
          isIncludeDigit = bool(re.search(r'\d', word))
          isIncludeAlphabet = bool(re.search(r'[a-zA-Z]', word))
          if isIncludeDigit and isIncludeAlphabet:                   # 文字列に英字と数字両方あるかどうかチェック
              encrypted_word_list.append(word)
  #######################################################################
```

<br><br>

# Usage

以下の行のコードをご自身のものに置き換えてご利用ください。<br>
Please replace the following specific names to yours.

  - 'chrome driver path'
  - 'repository name'
  - \<api access token\>

<br><br>

```python
chrome_driver_path = 'chrome driver path'

# git関連の設定
repository_path = 'repository name'
if not os.path.isdir(repository_path):
    git.Git().clone("https://<api access token>:x-oauth-basic@github.com/<your github domain>/" + repository_path + ".git")
else:
    pass
```

