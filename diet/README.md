# DietZen — 每日飲食助理

一個裝得進手機桌面的飲食紀錄 App。單頁 HTML + PWA，沒有後端、沒有帳號、不連外網，
所有資料只存在使用者自己的瀏覽器裡（`localStorage`）。

## 功能

| 分頁 | 內容 |
| --- | --- |
| 今日 | 熱量環（目標 − 攝取 + 運動消耗）、三大營養素進度、喝水杯數、體重、當日筆記 |
| 飲食 | 早／午／晚／點心四餐分開記；內建 60+ 項台灣常見食物；自訂食物與常用清單；一鍵複製昨天 |
| 運動 | 記錄今天在哪練（可自訂地點清單）；5 份內建健身菜單（徒手／推／拉／腿／有氧）＋自建菜單；逐組打勾、記錄訓練總量與消耗 |
| 趨勢 | 7／14／30／90 天的體重折線圖與每日熱量長條圖、訓練天數與地點分布、期間平均 |
| 設定 | 每日目標、TDEE 換算（Mifflin-St Jeor）、常用食物管理、JSON 匯出／匯入／清除 |

## 安裝到手機

部署後用手機瀏覽器開啟 `…/diet/`：

- **Android / Chrome**：會跳出安裝提示，或在選單選「安裝應用程式」。
- **iPhone / Safari**：點下方「分享」→「加入主畫面」。App 內的設定頁也會顯示這段提示。

安裝後由 service worker 提供離線快取，沒有網路也能記錄。

## 本機開發

沒有建置流程，直接開 static server 即可（service worker 需要 http，不能用 `file://`）：

```bash
python3 -m http.server 8000
# 然後開 http://127.0.0.1:8000/diet/
```

## 檔案

```
diet/
├── index.html              App 本體（HTML + CSS + JS 全部在裡面）
├── manifest.webmanifest    PWA 設定：名稱、圖示、桌面捷徑
├── sw.js                   service worker：導覽 network-first，其餘 cache-first
├── icon-192.png            一般圖示
├── icon-512.png
├── icon-maskable-512.png   Android 自適應圖示
└── apple-touch-icon.png    iOS 主畫面圖示
```

改版時記得把 `sw.js` 裡的 `VERSION` 加一號，舊快取才會被清掉。

## 注意

食物的熱量與營養素是常見份量的**估算值**，僅供日常參考，不能取代營養師或醫療建議。
資料沒有雲端備份，換手機或清瀏覽器資料前請先用設定頁的「匯出 JSON」留一份。
