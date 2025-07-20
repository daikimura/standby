#!/bin/bash
# Raspberry Piセットアップスクリプト

# 必要なパッケージをインストール
sudo apt update
sudo apt install -y python3-full python3-venv

# 日本語フォントをインストール
sudo apt install -y fonts-noto-cjk fonts-noto-cjk-extra

# 仮想環境を作成
python3 -m venv ~/standby_env

# 依存関係をインストール
~/standby_env/bin/pip install -r ~/standby/requirements.txt

# 自動起動の設定
mkdir -p ~/.config/autostart/
# $USERを実際のユーザー名に置換してコピー
sed "s/\$USER/$USER/g" ~/standby/standby.desktop > ~/.config/autostart/standby.desktop
chmod +x ~/.config/autostart/standby.desktop

# アプリケーションメニューに追加
mkdir -p ~/.local/share/applications/
cp ~/standby/standby.desktop ~/.local/share/applications/
chmod +x ~/.local/share/applications/standby.desktop

# デスクトップにアイコンを配置
mkdir -p ~/Desktop/
# $USERを実際のユーザー名に置換してコピー
sed "s/\$USER/$USER/g" ~/standby/standby.desktop > ~/Desktop/standby.desktop
chmod +x ~/Desktop/standby.desktop

# アプリケーションメニュー用にも$USERを置換
sed "s/\$USER/$USER/g" ~/standby/standby.desktop > ~/.local/share/applications/standby.desktop
chmod +x ~/.local/share/applications/standby.desktop

echo "セットアップが完了しました！"