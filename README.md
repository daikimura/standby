# Standby

Googleカレンダーの予定と天気情報を表示するPythonアプリケーションです。PyGameを使用して描画します。Raspberry Piでの使用を想定しています。

## 必要条件

- Python 3
- Raspberry Pi (推奨: Raspberry Pi 4以上)

## セットアップ

1. リポジトリをクローン
```
git clone https://github.com/yourusername/standby.git ~/standby
cd ~/standby
```

2. セットアップスクリプトを実行:
```
bash setup.sh
```

3. Google Calendar APIのcredentials.jsonを取得し、プロジェクトルートに配置

4. 手動セットアップの場合:
```
# 必要なパッケージをインストール
sudo apt update
sudo apt install -y python3-full python3-venv

# 仮想環境を作成
python3 -m venv ~/standby_env

# 依存関係をインストール
~/standby_env/bin/pip install -r requirements.txt

# 自動起動の設定
mkdir -p ~/.config/autostart/
cp ~/standby/standby.desktop ~/.config/autostart/
chmod +x ~/.config/autostart/standby.desktop
```

## 使用方法

1. デスクトップ上のアイコンをクリックして起動
2. または、コマンドラインから起動:
```
source ~/standby_env/bin/activate
python ~/standby/standby-pygame.py
```
3. 右上の閉じるボタン(X)をクリックするか、'q'キーを押して終了

## ファイル説明

- `standby-pygame.py` - メインアプリケーションファイル 
- `credentials.json` - Google Calendar API認証情報
- `token_personal.pickle`, `token_work.pickle` - 認証トークン
- `Pipfile`, `Pipfile.lock` - 依存関係管理ファイル
- `standby.desktop` - デスクトップエントリファイル
- `icon.png` - アプリケーションアイコン (別途用意する必要あり)