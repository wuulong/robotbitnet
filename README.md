# robotbitnet
robot microbit network
A radio network designed for multinodes and robotic scenario

![](https://paper-attachments.dropbox.com/s_F2C6764D28F36F901AACE34728A06E860EDF2FC20EFA3E1A6EF80DBE7D681916_1608330208764_image.png)


## 功能列表
    - 多點網路
    - 多點遙控車
        - 用遙控器遙控單台車/全部車
        - 可強制停車與恢復遙控
        - 可選擇要遙控的車子
    - PC 端有網域管理程式
        - 檢測整個網路
        - 各點感測現狀與歷史，可繪圖表
        - 各點 RSSI 值與歷史，可繪圖表
        - 支援控制命令
            - 移動車子
            - RGB LED
        - 支援檔案腳本

## 使用方式
- 韌體下載
    - Github: robotbitnet
- 硬體與所需版本：
    - MicroBit V2: rbn_car_v2.py (V2.3)
    - MicroBit V1: rbn_broker_v1.py (V1.0)
- 安裝與設定
    - 登月小車 *N : 
        - 安裝硬體與韌體： MicroBit V2: rbn_car_v2.py (V2.3)
    - 遙控器：
        - 安裝硬體與韌體：MicroBit V2: rbn_car_v2.py (V2.3)
        - 遙控器可對全部，也可對任一台遙控。所以依照情境看需要幾台
            - 如果是一控全，那只要一台
            - 如果是一對一，那需要 N 台
    - PC 端（Broker）
        - 非必要，有需要使用 dm_monitor (V0.6.2) 時才要
        - 情境一：只要監控狀態
            - 安裝硬體與韌體： MicroBit V2: rbn_car_v2.py (V2.3)
        - 情境二：會下控制指令
            - 安裝硬體與韌體：MicroBit V1: rbn_broker_v1.py (V1.0)
- 開電與啟動
    - 登月小車：按 ButtonA
    - 遙控器：按 ButtonB
    - PC 端（Broker）: 按 ButtonA
        - 需使用 DM 時，執行 dm_monitor.py
        - 使用命令列來互動
- 執行中使用
    - 遙控器：
        - ButtonA: 單台與全部切換
        - ButtonB: 停止與控制切換
        - Logo 選台:
            - 按著時，代號會輪流顯示，那台車也會同時顯示。確認時，放掉 Logo
- 展示影片
    - [多點遙控車展示_V2.2.mov](https://drive.google.com/file/d/1KfWiZ7oTpz3-8hihB69_mxEHb1s7nGpy/view)
    - 之前影片
        - [多點遙控車展示_V2.1.mov](https://drive.google.com/file/d/1Rhx0gkFED4dsrfZGdgIjSfRNAvTA0CbM/view)
- 參考
    - [MoonCar 登月小車- CircusPi](http://www.circuspi.com/index.php/teachingplan/microbit-mooncar/)         



## 設計
### 檔案
| 檔名                           | 說明                                 |
| ---------------------------- | ---------------------------------- |
| dm_monitor.py                | DM Monitor 主程式                     |
| rbn_broker_v1.py             | 單獨 Broker 韌體                       |
| rbn_car_v2.py                | MicroBit V1 跑的RBN遙控車韌體(支援登月小車)     |
| others/mooncar_lib.py        | 登月小車的函式庫                           |
| history/rbn_car.py           | MicroBit V1 跑的RBN遙控車韌體（支援 MbitBot） |
| others/rc_car.py             | MicroBit V1 跑的遙控車（支援 MbitBot）      |
| history/robotbitnet_v1_t7.py | MicroBit V1 DM 版 搭配 DM V0.4        |
| history/robotbitnet_v2_t2.py | MicroBit V2 感測+rssi 搭配  DM V0.6    |

### 命令說明與列表
- 命令實作於否，看每個韌體自己個規劃，需文件宣告支援的命令
- 命令長短
    - 預設封包設定為 64 byte, 超過會自動被丟棄
- 命令格式
    - [主格式] SID:DID:APPINFO
        - 用 : 分隔的三欄
    - [主格式-ACK] ~
    - 相容性
            - VERSION = 1 
            - 記憶體不足問題，不在命令格式的考量範圍。每份韌體，不保證支持所有命令，一般都是只支持特定命令
    - [APPINFO] VER,TYPE, PERTYPE_INFO
        - 用 , 分隔的多欄，欄數每個 TYPE 定義會不同
        - VER: 1, (初始版視為 VER:0)
        - 實作狀態:
            - 設計中：發想設計階段，可隨時更改
            - 部分使用：之前版本有實作
            - 內建：目前版本內建
        - PERTYPE_INFO: 以 , 做為分隔符號
        - TYPE<10 , 為系統定義, 使用在 broadcast，10<=TYPE<20, 使用在 Unicast,  20含以上，為使用者自定義，但須符合格式。有需要回覆時建議雙數為命令，單數為回覆
            - EX- 10: 執行這個步態，11: 步態已執行完畢
        - 本格式在 broadcast/unicast 皆需滿足
        - PERTYPE 總表 (如下表)


- 協議
    - Broadcast:  did=0
        - 每個點每秒用廣播輪詢發出有在使用的 PERTYPE_INFO
        - 線上 ID 應看每個廣播，得知網域上有哪些點
    - Unicast: 利用 PERTYPE>=10, 自定義格式
- 實作邏輯
    - 分散式，資訊由各點自行收集與紀錄
    - 記憶體考量，用不上的 TYPE 與 Code, 不用實作
    - 發控制命令之前，須先切換成主控狀態，沒有命令要發了，需離開主控狀態
        - 進出主控狀態時，需要 broadcast type 1, 更新主控狀態資訊
        - 固定主控情境，主控一開始就設定成主控狀態，之後就沒有離開
- PERTYPE 定義
    - 1,2,3: 自身感測/狀態資訊
        - 細部定義
            - 主控狀態
                - 0: 目前不是主控 , 1: 目前是主控
                - 在沒有固定主控/臨時主控情境下，設為 0
            - 命令狀態
                - 0: 初始狀態 or 命令執行完
                - 1: 命令執行中
        - 說明
            - 記憶體考量，只有主控狀態與命令狀態需實作，沒實作留空白
            - EX: 0,0,,,,,,,
    - 20: 報數
        - 要報的數
### 燈號
    - debug 燈號
        - [4:4] 發送 toggle
        - [0-2:4] 接收顯示
        - [3:4] 主控 ID 資訊，9-自己是主控, 0-沒主控, 5-有主控，我是被控
        - [0-3:0-3] 週期回報（每秒更換）
            - ID
            - 命令可視化 或其他資訊
            
| App Version | TYPE  | 實作狀態 | Broadcast/<br>Unicast | Description                             | 特性與內容說明               | TYPE_INFO                                                                              | 使用範例或備註                                                                                                                                       |
| ----------- | ----- | ---- | --------------------- | --------------------------------------- | --------------------- | -------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| 1           | 1     | 設計中  | 系統 B                  | 狀態資訊                                    | 兩欄數字                  | 主控狀態<br>命令狀態                                                                           |                                                                                                                                               |
| 1           | 2     | 部分使用 | 系統 B                  | 狀態資訊+可見點數                               | 三欄數字                  | 主控狀態<br>命令狀態<br>可見點數                                                                   | visible nodes count                                                                                                                           |
| 1           | 3     | 內建   | 系統 B                  | 狀態資訊+可見點數+各種感測值                         | 9 欄數字                 | 主控狀態，命令狀態<br>可見點數<br>Logo有沒有被按<br>光感應<br>麥克風值<br>加速度 x,y,z<br><br>磁力計方位因為每次都要校正，所以沒放進去 | (產製需 硬體V2)<br>visible nodes count + int(pin_logo.is_touched())<br>display.read_light_level()<br>microphone.sound_level()<br>a_x,a_y,a_z       |
| 1           | 5     | 設計中  | 系統 B                  | 網域資訊                                    | 欄數固定<br>每個 SID 可能都有資訊 | 與各點的距離                                                                                 |                                                                                                                                               |
| 1           | 10-19 |      | 系統 U                  |                                         |                       |                                                                                        |                                                                                                                                               |
| 1           | 10    | 內建   | 系統 U                  | 問某一點的 RSSI                              | 一欄數字                  | id                                                                                     |                                                                                                                                               |
| 1           | 11    | 內建   | 系統 U                  | 回報某一點的 RSSI                             | 兩欄數字                  | id<br>rssi                                                                             |                                                                                                                                               |
| 1           | 20    | 內建   | 使用者 U                 |                                         | 一欄數字                  |                                                                                        | 報數，發給每一台他的 ID                                                                                                                                 |
| 1           | 22    | 部分使用 | 使用者 U                 | 控制車輛馬達命令<br>MbitBot driver 方式<br>（沒在用了） | 兩欄數字                  | px_cmd<br>py_cmd                                                                       | 0-99 map to -50 to 49<br><br>go_value = -(py_cmd-50)*2<br>percent = (px_cmd-50)<br><br>motor1 = go_value-percent<br>motor2 = go_value+percent |
| 1           | 23    | 內建   | 使用者 U                 | 控制車輛馬達命令(I2C value)                     | 一欄數字                  | left*100+right                                                                         | 0(後退)-50（停止）-100（前進）?                                                                                                                         |
| 1           | 24    | 設計中  | 使用者 U                 | 依方位，前進速度，前進時間                           | 三欄數字                  | compass.heading<br>0-100<br>秒數                                                         |                                                                                                                                               |
| 1           | 25    | 內建   | 使用者 U                 | 控制 RGB 燈號                               | 四欄數字                  | 第幾個燈<br>r,g,b                                                                          |                                                                                                                                               |



## PC Domain Master

為 PC 上的程式，監控整個網路

### DM CLI 命令
    python dm_monitor.py
    Dm>version
    DmMonitor V0.6.2
    Dm>help
    
    Documented commands (type help <topic>):
    ========================================
    act       demo_rccar  maxnodes_test  quit      rssi_plot    sensing_plot
    car_move  dminfo      mon_ids        reset     script       tx_cmd      
    demo      help        network        rssi_his  sensing_his  version     
    
    Dm>dminfo
    Domain nodes count=3
    DM/broker ID=1
    
    node ID= 1, last_rx=-0.528 s,ms=1,cs=0
    type[3]=['1', '0', '2', '0', '0', '3', '-12', '100', '-1024']
    type[10]=['1']
    type[11]=['3', '-44']
    type[20]=['3']
    Sensing:VISCNT=2,LOGO=0,LIGHT=0,SOUND=3,A_X=-12,A_Y=100,A_Z=-1024
    rssi[2]=-33 -> 0 cm
    rssi[3]=-44 -> 0 cm
    node ID= 2, last_rx=-0.114 s,ms=0,cs=0
    type[3]=['0', '0', '2', '0', '1', '1', '-152', '188', '-1028']
    type[10]=['2']
    type[11]=['3', '-23']
    type[20]=['1']
    Sensing:VISCNT=2,LOGO=0,LIGHT=1,SOUND=1,A_X=-152,A_Y=188,A_Z=-1028
    rssi[1]=-33 -> 0 cm
    rssi[3]=-23 -> 0 cm
    node ID= 3, last_rx=-0.492 s,ms=0,cs=0
    type[3]=['0', '0', '2', '0', '0', '1', '-28', '144', '-1008']
    type[10]=['3']
    type[11]=['2', '-24']
    type[20]=['2']
    Sensing:VISCNT=2,LOGO=0,LIGHT=0,SOUND=1,A_X=-28,A_Y=144,A_Z=-1008
    rssi[1]=-43 -> 0 cm
    rssi[2]=-24 -> 0 cm
    1->0 : 3,4462,60
    1->2 : 1,3343,60
    1->3 : 1,3346,60
    2->0 : 4,4459,60
    2->1 : 1,3342,60
    2->3 : 4,3341,48
    3->0 : 3,4453,60
    3->1 : 1,3345,60
    3->2 : 4,3345,48
    Dm>mon_ids
    SS-123
     0-dee
     1-dee
     2-dee
     3-dee
     4-dee
     5-dee
     6-dee
     7-dee
     8-dee
     9-dee
    Dm>network
    Dm>help sensing_his
    show per node sensing history 
                sensing_his [node_id] #0: all, c: clear history
            
    Dm>sensing_his 1
    
    TIME=2020-12-11 20:56:01.827966|NODE=1,VISCNT=2,LOGO=0,LIGHT=0,SOUND=1,A_X=40,A_Y=64,A_Z=-1008
    TIME=2020-12-11 20:56:02.132594|NODE=1,VISCNT=2,LOGO=0,LIGHT=0,SOUND=0,A_X=36,A_Y=56,A_Z=-1012
    TIME=2020-12-11 20:56:02.171024|NODE=1,VISCNT=2,LOGO=0,LIGHT=0,SOUND=1,A_X=28,A_Y=64,A_Z=-1012
    TIME=2020-12-11 20:56:02.332261|NODE=1,VISCNT=2,LOGO=0,LIGHT=0,SOUND=0,A_X=44,A_Y=60,A_Z=-1016
    TIME=2020-12-11 20:56:02.371508|NODE=1,VISCNT=2,LOGO=0,LIGHT=0,SOUND=4,A_X=48,A_Y=68,A_Z=-1004
    TIME=2020-12-11 20:56:02.503942|NODE=1,VISCNT=2,LOGO=0,LIGHT=0,SOUND=2,A_X=48,A_Y=64,A_Z=-996
    TIME=2020-12-11 20:56:02.542088|NODE=1,VISCNT=2,LOGO=0,LIGHT=0,SOUND=2,A_X=32,A_Y=60,A_Z=-1008
    TIME=2020-12-11 20:56:02.675349|NODE=1,VISCNT=2,LOGO=0,LIGHT=0,SOUND=0,A_X=24,A_Y=56,A_Z=-1016
    TIME=2020-12-11 20:56:02.715219|NODE=1,VISCNT=2,LOGO=0,LIGHT=0,SOUND=4,A_X=32,A_Y=72,A_Z=-1016
    TIME=2020-12-11 20:56:02.871521|NODE=1,VISCNT=2,LOGO=0,LIGHT=0,SOUND=2,A_X=44,A_Y=64,A_Z=-1000
     
    
    Dm>help sensing_plot
    plot sensing history
                
                1. plot one node with all sensor 
                    sensing_plot [id] 
                2. plot all node with one sensor
                    sensing_plot 0 [col_id]
                3. plot all nodes
                    sensing_plot 0
                4. plot one node with one sensor
                    sensing_plot [id] [col_id]
                col_id : IDX_VISCNT=0,IDX_LOGO=1,IDX_LIGHT=2,IDX_SOUND=3,IDX_A_X=4,IDX_A_Y=5,IDX_A_Z=6
            


![](https://paper-attachments.dropbox.com/s_A90EB1209324CE3E8E7B205A7FAE2745D4A2CCABFC031EE46221230FF933675D_1607695431113_image.png)

![](https://paper-attachments.dropbox.com/s_A90EB1209324CE3E8E7B205A7FAE2745D4A2CCABFC031EE46221230FF933675D_1607695851372_image.png)



### DM Script 設計

命令雷同 dm_monitor 的命令列，只支援部分命令

- 在 CLI 中用 script 命令來執行
- 註解：第一個字為 #
- 支援命令
    - sleep [ms]
    - 命令格式同 CLI
        - tx_cmd,car_move
- 可參考 script 目錄中的範例


### Domain 架構
![](https://paper-attachments.dropbox.com/s_A90EB1209324CE3E8E7B205A7FAE2745D4A2CCABFC031EE46221230FF933675D_1551402659078_image.png)
![](https://paper-attachments.dropbox.com/s_A90EB1209324CE3E8E7B205A7FAE2745D4A2CCABFC031EE46221230FF933675D_1551403149042_image.png)

- 情境有需要時才會有 Leader, 目前的實作是沒有 Leader
- PC DM 存在時，才需要有 Broker, Broker 是 EP 的角色，也可以是 Leader
- 基本情境
    - A - 第一個開機自動為 Leader，發號司令
    - B - DM 透過 Broker 管理整個網路，Broker 也是 Leader
![](https://paper-attachments.dropbox.com/s_A90EB1209324CE3E8E7B205A7FAE2745D4A2CCABFC031EE46221230FF933675D_1551417139116_image.png)


### 安裝
- 使用 python 3
- 需先安裝以下 modules, 建議使用 Anaconda 環境
    - serial
    - matplotlib
    - networkx



# Document
https://paper.dropbox.com/doc/RobotBitNet--BBj0BC1fHBQfhJAqEZkuyBIgAg-CVvstPQ1sEKXuTFA4Rw5K


