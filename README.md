# robotbitnet
robot microbit network
A radio network designed for multinodes and robotic scenario

![](demo.png)

- 功能列表
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

# Document
https://paper.dropbox.com/doc/MbitBot-DG5SSj5zQhBv1CoAgDtAG#:uid=042320171641794286583566&h2=V2.3-%E4%BD%BF%E7%94%A8%E6%96%B9%E5%BC%8F
