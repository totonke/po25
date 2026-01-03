IoTデータロガーシステム概要
（Arduino × LoRa × Python × Flask × MariaDB x (java androidアプリ増設中)）

本システムは、職業訓練校における「IoT × Web × DB データ蓄積総合演習」の課題として作成した IoT データロガーです。

Arduino で取得したセンサデータを無線通信で Raspberry Pi に送信し、サーバ側でデータベースへ保存し、Web 画面で表示する一連の処理を構築しています。
現在Javaを学習中で、26年2月には最終的にandroidアプリでセンサーの値を表示します。

全ソースは以下ですが、細かい構成ごとのコードのURLも随時張ります。
https://github.com/totonke/po25

---

システム構成

Arduino（センサ）
LoRa 無線通信
Raspberry Pi（ゲートウェイ）
HTTP POST
Raspberry Pi（サーバ：Gunicorn + Flask）
MariaDB
Web ブラウザ表示

---

Arduino（センサ側）

Arduino では以下の処理を行っています。

温度センサ（ADT7410）から温度を取得します。
Grove Light Sensor（フォトレジスタ型）アナログ入力から照度を取得します。
RTC（DS1307）を用いて時刻を取得します。
Grove RGB LCD画面に現在の温度、照度、時刻の値を表示します。


それぞれから取得したテキスト形式のデータを生成し
LoRa モジュール（E220）を使用してラズベリーパイへ無線送信します。

SDカードモジュールを使用して（AE-microSD-LLCNV）SDカードへバックアップも保存します。


送信データは CSV 形式の文字列として構成されています。

コードは以下
https://github.com/totonke/po25/blob/main/ardDaLog.ino



---

LoRa 無線通信

Arduino と Raspberry Pi（ゲートウェイ）間の通信には LoRa を使用しています。
LoRa ではテキストデータのみを送信しています。

---

Raspberry Pi（ゲートウェイ）

ゲートウェイ側では Python プログラムを動作させています。

主な処理内容は以下の通りです。

シリアル通信により LoRa からデータを受信します。
受信したバイトデータを文字列にデコードします。
CSV 形式の文字列を分割し、デバイス名・温度・照度を取得します。
受信時刻は複数端末から受信する想定の為 Python 側で取得します。
HTTP POST によりサーバへデータを送信します。

ここでもSDカードにバックアップをとっています。
コードは以下
https://github.com/totonke/po25/blob/main/raspRec.py

---

Raspberry Pi（サーバ）

サーバ側では Flask アプリケーションを Gunicorn 上で動作させています。

以下処理が分かれますので、先にmyappのファイルURLをおいておきます。
https://github.com/totonke/po25/tree/main/myapp

Flask アプリケーションでは以下の処理を行っています。

HTTP POST によるセンサデータの受信を行います。
POST パラメータから各データを取得します。
文字列として受信した数値を数値型に変換します。
MariaDB に対してデータを登録します。

---

MariaDB（データベース）

センサデータは MariaDB に保存しています。

保存している項目は以下の通りです。

デバイス名
温度
照度
デバイス時刻

テーブルもPythonで作成し、Flask アプリケーションから INSERT 文を実行してデータを保存しています。

---

Web 表示

Flask と Jinja2 を使用して、MariaDB に保存されたデータを Web ブラウザ上に表示しています。
Web 画面では、保存されたデータを一覧形式で確認できます。


---

まとめ

本課題では、以下の一連の IoT データ処理を実装しました。

センサデータの取得
無線通信
ゲートウェイでの受信処理
HTTP 通信
データベースへの保存
Web 画面での表示


