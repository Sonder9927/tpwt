# TPWT

双平面波

---
## data
1. 按照地震目录切分

data 文件夹下是z 分量 1Hz 的 sac 文件。

切分事件的脚本：

```sh
ls data/*.sac > data_z.lst
mktraceiodb -L done_z.lst -O data_z.db -LIST data_z.lst -V
cutevent -V -ctlg event.cat -tbl data_z.db -b +0 -e +10800 -out SAC
rm done_z.lst data_z.db data_z.lst
```

需要准备 `event.cat`，且相邻时间不应小于3小时：
```cat
2023/01/01,10:10:10
2023/01/02,20:20:20
```

10800 为截取地震时间开始3小时内的数据，输出文件夹在 SAC 下，按照事件进行了分类。

2. 准备台站和事件信息

`event.lst` 包含 事件(12位)、经度、纬度、震级 四列
`station.lst` 包含 台站、经度、纬度 三列

3. 修改格式

- 上述步骤产生的地震事件是14位的，要改成12位，即年月日时分，不要秒。
- sac 的头文件信息可能被改了，确保有 `dist`，这需要台站位置和事件位置。
- sac 的 channel 要修改为 LHZ
- 最终单个 sac 文件路径为：`SAC/202301011010/202301011010.staname.LHZ.sac`

台站名要和头文件的 kcpnm 以及 station.lst 的台站信息对应。

## run

### 01
`01.bash`

Generate reference phase velocities for each pair of event and station, then extract dispersion curves for each sac file.

Prepare files:
    - event.lst: event lo la ma
    - station.lst: station lo la

1. use

    `mk_pathfile` match event and station

    `TPWT/utils/RAYL_320_80_32000_8000.disp` raylei global model

    `TPWT/utils/LOVE_400_100.disp` love global model

    `aftani_c_pgl` extract snr curves.

    `spectral_snr` contral by snr, need use csh, I have modified the .csh to .bash.

2. set
3. generate

`flag_GDM52` 无意义，标志 01 跑完了

`path/ event_station.PH_PRED` and `GDM52_dispersion.out`

`SAC/event/ 1.bash, event.station.sac_1_DISP.0, event.station.sac_1_DISP.1, event.station.sac_2_DISP.0, event.station.sac_2_DISP.1.` Only `event.station.sac_1_DISP.0` will be used

`event.station.sac_snr.yyj.txt filelist, flag_SNR, flag_aftan, param.dat, step.txt, temp.dat bash 01.bash`

### 02
`02.bash`

1. use

    `find_phvel_amp_earthquake` format the pinsan according to event and zhouqi. generate .ph.txt
    `correct_tt_select_data` input mid points coordinate to remove bad points. Keep points which can satisfied less than the tmisfit.

2. set

    ```sh
    cutoff_per=0.7  # 有效台站记录在70%以上，则事件有效
    snr=10
    dist=3500  # the longest distance between two stations.
    tmisfit=10  # 走时误差超过 10s 则舍弃 
    ```

    correct_tt_select_data 设定参考台站坐标
    plot_phase_time 设定反演范围

3. generate

    sta_dist.lst

    all_events_20_150/{t}sec_{snr}snr_3500dis/ {event}_am.txt, {event}_am.txt.HD{event}_am.txt_v1, {event}_am.txt_v1.HD, {event}.ph.txt, {event}.ph.txt.HD, {event}.ph.txt_v1, {event}.ph.txt_v1.HD, tomo.grd

    `{event}.ph.txt` will be used in 02.bash self.

### 03

1. use
    - `wc`
    - `sdiff`

2. set

    - nsta_cutoff = 15
    - Region: la and lo of region, the range should < 10 degree

3. generate
    - `SAC/` `tempeq` and `eqlistper`: total number of stations to one event and the order number of the event.

### 04
1. use
- `creatgridnode_TPWT` : create fan yan wang ge in `invrsnodes`.
- `avgvel` : average v
- `echo 5 {smooth_len} 0.25 0.25 >>{new_eqlistper}` :0.25 can be changed to 0.2 or not.
- `rd` : select event, should notice that the event number in sacfile name must be 12.

2. set
    - snrcutoff = 10
    - tcutoff = 10
    - dist_cutoff = 3500 need > 3500
    - nsta_cutoff = 15
    - smooth_len = 80
    - damping = 0.2

3. generate

    - `sens_dir/`
    - `TPW_{snrcutoff}snr_{tcutoff}t_{dist_cutoff}_dist`
    - `invrsnodes` fan yan wang ge jie dian.
    - `eqlistper` (new): old `eqlistper` + some new information.
        detail; summar; invrnodes; pham - resort of `.ph.txt` generated before.

### 05
repeat 04, chose pham.V3

Results are in `new_2d` directory.

### 06
check board.

---

## final result
The final result is 2 `grd.*` files in `new_2d`, `.ave` is perturbation.

And there are two `std*` files representing standard deviation in the `new_2d`.