import os
import pygame
import math
import time
import threading
import argparse
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import pickle

class StandbyDisplay:
    def __init__(self, fullscreen=True):
        # .envファイルを読み込む
        load_dotenv()

        # 環境変数から値を取得
        self.OPENWEATHERMAP_API_KEY = os.getenv('OPENWEATHERMAP_API_KEY')
        self.ZIP_CODE = os.getenv('ZIP_CODE')

        # Google Calendar API設定
        self.SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        self.CREDENTIALS_FILE = 'credentials.json'
        self.TOKEN_FILES = {
            'personal': 'token_personal.pickle',
            'work': 'token_work.pickle'
        }
        pygame.init()
        
        # ディスプレイモードの設定
        if fullscreen:
            # フルスクリーンモードで初期化（Macで高速化するためのフラグを追加）
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
        else:
            # ウィンドウモードで初期化（一般的なディスプレイサイズ）
            self.screen = pygame.display.set_mode((800, 480), pygame.HWSURFACE | pygame.DOUBLEBUF)
            pygame.display.set_caption('Standby Display')

        # 色の定義
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)

        try:
            # Homebrewでインストールされたフォントのパス
            font_paths = [
                '/opt/homebrew/Caskroom/font-noto-sans-cjk/2.004/NotoSansCJK.ttc',  # Apple Silicon Mac
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',  # Raspberry Pi
            ]

            font_path = None
            for path in font_paths:
                if os.path.exists(path):
                    font_path = path
                    break

            if font_path:
                self.font = pygame.font.Font(font_path, 32)
                self.small_font = pygame.font.Font(font_path, 24)
            else:
                print("フォントが見つかりません")
                self.font = pygame.font.SysFont(None, 32)
                self.small_font = pygame.font.SysFont(None, 24)

        except Exception as e:
            print(f"フォントの読み込みに失敗: {e}")
            self.font = pygame.font.SysFont(None, 32)
            self.small_font = pygame.font.SysFont(None, 24)

        # 画面の左半分の中心を計算
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        self.left_half = pygame.Surface((screen_width // 2, screen_height))
        self.right_half = pygame.Surface((screen_width // 2, screen_height))

        # 最後の更新時刻を保存
        self.last_weather_update = int(time.time())

        self._weather_cache = None
        self._calendar_cache = None

        self.last_api_update = 0

        # API更新用のスレッドを開始
        self.api_thread = threading.Thread(target=self._update_api_data, daemon=True)
        self.api_thread.start()

    def _update_api_data(self):
        """APIデータを定期的に更新するスレッド"""
        while True:
            current_time = time.time()
            if current_time - self.last_api_update > 300:  # 5分間隔
                try:
                    self._weather_cache = self.fetch_weather()
                    self._calendar_cache = self.fetch_calendar_events()
                    self.last_api_update = current_time
                except Exception as e:
                    print(f"API更新エラー: {e}")
            time.sleep(1)  # スレッドのスリープ

    def draw_analog_clock(self, current_time, surface):
        # 日付と曜日の表示（時計の上部）
        weekday_names = ['月', '火', '水', '木', '金', '土', '日']
        date_str = f"{current_time.year}年{current_time.month}月{current_time.day}日 ({weekday_names[current_time.weekday()]})"
        date_text = self.font.render(date_str, True, self.WHITE)

        # 日付テキストを時計の上部中央に配置
        date_rect = date_text.get_rect(centerx=surface.get_width() // 2, y=20)
        surface.blit(date_text, date_rect)

        def draw_hand(angle, length, color, thickness):
            rad = math.radians(angle)
            end_x = center[0] + int(length * math.cos(rad) + 0.5)
            end_y = center[1] + int(length * math.sin(rad) + 0.5)
            pygame.draw.aaline(surface, color, center, (end_x, end_y), thickness)

        center = (surface.get_width() // 2, surface.get_height() // 2)
        clock_radius = min(surface.get_width(), surface.get_height()) // 2 - 50

        # 時計の外枠
        pygame.draw.circle(surface, self.WHITE, center, clock_radius, 2)

        # 数字用のフォントを作成
        number_font = pygame.font.Font(None, 36)

        # 目盛りと数字の描画
        for i in range(12):
            angle = i * 30 - 90
            rad = math.radians(angle)

            # 目盛りの描画
            start_x = center[0] + int((clock_radius - 20) * math.cos(rad) + 0.5)
            start_y = center[1] + int((clock_radius - 20) * math.sin(rad) + 0.5)
            end_x = center[0] + int(clock_radius * math.cos(rad) + 0.5)
            end_y = center[1] + int(clock_radius * math.sin(rad) + 0.5)
            pygame.draw.aaline(surface, self.WHITE, (start_x, start_y), (end_x, end_y), 1)

            # 数字の描画
            number = str(12 if i == 0 else i)
            number_rad = math.radians(i * 30 - 90)
            number_x = center[0] + int((clock_radius - 40) * math.cos(number_rad))
            number_y = center[1] + int((clock_radius - 40) * math.sin(number_rad))

            number_surface = number_font.render(number, True, self.WHITE)
            number_rect = number_surface.get_rect(center=(number_x, number_y))
            surface.blit(number_surface, number_rect)

        # 現在時刻の計算（datetime オブジェクトを使用）
        hour = current_time.hour % 12
        minute = current_time.minute
        second = current_time.second
        microsecond = current_time.microsecond

        # すべての針を滑らかに動かす
        precise_second = second + (microsecond / 1_000_000)
        precise_minute = minute + (precise_second / 60)
        precise_hour = hour + (precise_minute / 60)

        # 針の長さを計算
        hour_length = clock_radius * 0.45
        minute_length = clock_radius * 0.65
        second_length = clock_radius * 0.75

        # 針の角度を計算
        hour_angle = precise_hour * 30 - 90
        minute_angle = precise_minute * 6 - 90
        second_angle = precise_second * 6 - 90

        # 針を描画
        draw_hand(hour_angle, hour_length, self.WHITE, 2)
        draw_hand(minute_angle, minute_length, self.WHITE, 2)
        draw_hand(second_angle, second_length, self.RED, 1)

        # 中心点を描画
        pygame.draw.circle(surface, self.RED, center, 3)

    def fetch_weather(self):
        try:
            # 現在の天気のみ取得
            current_url = f"http://api.openweathermap.org/data/2.5/weather?zip={self.ZIP_CODE}&appid={self.OPENWEATHERMAP_API_KEY}&units=metric&lang=ja"
            current_response = requests.get(current_url)
            current_data = current_response.json()

            weather = {
                'temp': round(current_data['main']['temp']),  # 現在の気温
                'condition': current_data['weather'][0]['description'],
                'humidity': current_data['main']['humidity'],
                'last_updated': time.time()
            }

            return weather

        except Exception as e:
            print(f"天気の取得に失敗: {e}")
            return None

    def draw_weather(self, surface):
        if not self._weather_cache:
            return

        start_x = 20
        start_y = 20

        # 現在の天気
        condition_text = self.font.render(self._weather_cache['condition'], True, self.WHITE)
        surface.blit(condition_text, (start_x, start_y))

        # 気温と湿度を横に並べて表示
        temp_text = self.small_font.render(
            f'気温: {self._weather_cache["temp"]}°C', 
            True, self.WHITE
        )
        humidity_text = self.small_font.render(
            f'湿度: {self._weather_cache["humidity"]}%', 
            True, self.WHITE
        )
        surface.blit(temp_text, (start_x, start_y + 50))
        surface.blit(humidity_text, (start_x + 150, start_y + 50))  # 気温の右側に表示

    def get_calendar_service(self, account_type):
        creds = None
        token_file = self.TOKEN_FILES[account_type]

        # トークンファイルが存在する場合は読み込み
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)

        # 有効な認証情報がない場合は新規取得
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.CREDENTIALS_FILE, self.SCOPES)
                creds = flow.run_local_server(port=0)

            # トークンの保存
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)

        return build('calendar', 'v3', credentials=creds)

    def fetch_calendar_events(self):
        try:
            # 日本時間で今日の日付を取得
            jst_now = datetime.now()
            today_start = jst_now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(hours=9)  # UTCに変換
            today_end = today_start + timedelta(days=1)

            # ISO形式に変換
            time_min = today_start.isoformat() + 'Z'
            time_max = today_end.isoformat() + 'Z'

            all_events = []

            for account_type in ['personal', 'work']:
                try:
                    service = self.get_calendar_service(account_type)
                    events_result = service.events().list(
                        calendarId='primary',
                        timeMin=time_min,
                        timeMax=time_max,
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()
                    events = events_result.get('items', [])

                    for event in events:
                        start = event['start'].get('dateTime', event['start'].get('date'))
                        # タイムゾーン付きの日時文字列を解析
                        if 'T' in start:  # dateTimeの場合
                            # タイムゾーン情報付きの日時文字列を直接解析
                            start_dt = datetime.fromisoformat(start)
                            time_str = start_dt.strftime('%H:%M')
                        else:  # dateの場合（終日イベント）
                            time_str = '終日'

                        all_events.append({
                            'time': time_str,
                            'title': event['summary'],
                            'type': account_type
                        })
                except Exception as e:
                    print(f"{account_type}カレンダーの取得に失敗: {e}")
                    continue

            return sorted(all_events, key=lambda x: x['time'] if x['time'] != '終日' else '00:00')

        except Exception as e:
            print(f"予定の取得に失敗: {e}")
            return []

    def draw_calendar(self, surface):
        # カレンダーセクションの開始位置（右半分の下部）
        start_x = 20
        start_y = surface.get_height() // 2  # 画面の縦方向中央から開始
        line_height = 40

        # カレンダーセクションのヘッダー
        header = self.font.render("今日の予定", True, (255, 255, 255))
        surface.blit(header, (start_x, start_y - 50))

        # キャッシュがないか、イベントが空の場合
        if not self._calendar_cache or len(self._calendar_cache) == 0:
            no_events = self.small_font.render("予定はありません", True, (200, 200, 200))
            surface.blit(no_events, (start_x, start_y))
            return

        # イベントの表示
        for i, event in enumerate(self._calendar_cache):
            # 時間の表示
            time_text = self.small_font.render(event['time'], True, (255, 255, 255))
            surface.blit(time_text, (start_x, start_y + i * line_height))

            # イベントタイプに応じて色を変更
            color = (100, 200, 255) if event['type'] == 'work' else (255, 200, 100)

            # イベントタイトルの表示
            title_text = self.small_font.render(event['title'], True, color)
            surface.blit(title_text, (start_x + 100, start_y + i * line_height))

    def draw_close_button(self):
        # 閉じるボタンを右上に描画
        button_size = 30
        button_margin = 15
        button_pos = (self.screen.get_width() - button_size - button_margin, button_margin)
        button_rect = pygame.Rect(button_pos, (button_size, button_size))
        
        # ボタンの背景
        pygame.draw.rect(self.screen, (150, 30, 30), button_rect, border_radius=5)
        
        # Xマーク
        line_margin = 8
        start_pos1 = (button_pos[0] + line_margin, button_pos[1] + line_margin)
        end_pos1 = (button_pos[0] + button_size - line_margin, button_pos[1] + button_size - line_margin)
        start_pos2 = (button_pos[0] + line_margin, button_pos[1] + button_size - line_margin)
        end_pos2 = (button_pos[0] + button_size - line_margin, button_pos[1] + line_margin)
        
        pygame.draw.line(self.screen, self.WHITE, start_pos1, end_pos1, 2)
        pygame.draw.line(self.screen, self.WHITE, start_pos2, end_pos2, 2)
        
        return button_rect

    def run(self):
        clock = pygame.time.Clock()
        running = True
        close_button_rect = None

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # マウスクリック時にclose_button_rectが定義されていて、その範囲内をクリックした場合
                    if close_button_rect and close_button_rect.collidepoint(event.pos):
                        running = False

            # 時計の描画（毎フレーム）
            self.left_half.fill(self.BLACK)
            self.draw_analog_clock(datetime.now(), self.left_half)
            self.screen.blit(self.left_half, (0, 0))

            # キャッシュされたデータを使用して天気と予定を描画（1秒ごと）
            if int(time.time()) > self.last_weather_update:
                self.right_half.fill(self.BLACK)
                self.draw_weather(self.right_half)
                self.draw_calendar(self.right_half)
                self.screen.blit(self.right_half, (self.screen.get_width() // 2, 0))
                self.last_weather_update = int(time.time())
            
            # 閉じるボタンを描画
            close_button_rect = self.draw_close_button()

            # 画面の更新
            pygame.display.flip()

            clock.tick(60)  # 60FPSに制御

        pygame.quit()

if __name__ == '__main__':
    # コマンドライン引数の設定
    parser = argparse.ArgumentParser(description='Standby Display')
    parser.add_argument('--window', action='store_true', help='ウィンドウモードで起動 (デフォルトはフルスクリーン)')
    parser.add_argument('--cwd', help='作業ディレクトリを指定')
    args = parser.parse_args()
    
    # 作業ディレクトリの変更（指定された場合）
    if args.cwd:
        os.chdir(args.cwd)
        print(f"作業ディレクトリを変更: {args.cwd}")
    
    # フルスクリーンかウィンドウかを引数で切り替え
    display = StandbyDisplay(fullscreen=not args.window)
    try:
        display.run()
    finally:
        pygame.quit()
