# EncryptedWordExtractionFromGitHubRepos

GitHub 上にあるファイルから、暗号化文字列（例：APIキーなど）を自動抽出する<br>
Auto extraction program of encrypted strings (i.e. API key) from any files on GitHub

# Usage

以下の行のコードをご自身のものに置き換えてご利用ください。<br>
Please replace the following specific names to yours.

  - 'chrome driver path'
  - 'repository name'
  - <api access token>

```python
chrome_driver_path = 'chrome driver path'

# git関連の設定
repository_path = 'repository name'
if not os.path.isdir(repository_path):
    git.Git().clone("https://<api access token>:x-oauth-basic@github.com/<your github domain>/" + repository_path + ".git")
else:
    pass
```

