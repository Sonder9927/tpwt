# TPWT

---

## info

Two plane wave tomography inversion of phase velocity an area.

Here is my backup.

This only records the form of the data,
the processing flow, some automated scripts that
process the data in the flow,
and some flashes of light.

Not ready to public yet.

## DATA to SAC

Using `get_cut_event.py` to create event.lst and event.cat from two event catalog downloaded from website and to cut event from data.

Using `get_SAC.py` to get SAC for tpwt from cut event directory.

More information see bellow.

### Raw Data

Seismic data from stations in the area.

My first-hand data is in `.miniseed` format.

### Preprocessing

Use `'sac'` to process and finally get only Z component, filtered 20-150s
(optional because it has been filtered in the step of removing instrument response,
just make sure the frequencies is wide enough for the periods), 1Hz `.sac` data.

### Cut by event

I need to cut data by events from 30&deg; to 120&deg; and only need data within 3 hours after the earthquakes.

1. I download event catalog from
   [Search Earthquake Catalog](https://earthquake.usgs.gov/earthquakes/search/).

- Basic Options:

  - Magnitude Minimum: 5.5

- Advanced Options:

  - Circle:
    - la:
    - lo:
    - km:
  - Event Type:
    - earthquakes: Earthquake
  - Output Options: CSV

  So I get 120&deg; and 30&deg; event files in format `.csv` .

2. I use Python to treat the two event files. Code in `evt.ipynb`.

Then I will get 3 files:

- event.cat: This will be used to cut event. Format is:

  `2021/12/30,13:13:17`

- event.lst: Note that event must be description with 12 number. This will be used in `01.bash`. Format is:

  `202112301313 125.2498  -0.0798 5.5`

- event_depth.cat: This will be used in `batch_sacfile_ch.py`. Format is:

  `202112301313 125.2498  -0.0798 42.0`

Now I have `.sac` data files and `event.cat` file. I can cut data by events.

I will get some folders named `202112301313` in which there are some `.sac` files.

And those folders are in the `Out` set by me.

### Sac File Rename and Modify Head

Now I'm in `Out`.I will use:

- event_depth.cat: event lo la dp
- station_el.cat: station lo la el

I will add `evla evlo evdp stlo stla stel` to the head files which will automatically calculate `dist`
and change naming format of the sac files to be `eventtime.station.LHZ.sac`.

`bash sac_ch_rename.sh`

Now sac files will change from `XX.station.00.XXZ.X.eventtime.sac`
to `eventtime.station.LHZ.sac`. And `dist` will appear in head file.

At this point, my data preparation is basically complete.

## binuse

1. `TPWT/bin`

- aftani_c_pgl_TPWT
- average
- calc_distance_earthquake
- check_board
- convert_checkerboard_vel
- correct_tt_select_data
- createsac_TPWT
- creatgridnode_TPWT
- find_bad_kern100
- find_phvel_amp_earthquake
- GDM52_dispersion_TPWT
- gen_cor_pred_TPWT
- getdatafromsac_GZ
- gridgenvar.yang_v2
- guassia_avg
- july2month
- kern
- syndata_GUOZ
- lf_correct_2pi_v1
- map_list
- mk_pathfile_TPWT
- pvelper
- rdsetupsimul_phamp_from_earthquake
- sensitivity_rayleigh
- simannerr100.kern
- simannerr160.kern
- spectral_snr_TPWT

2. sensitivity.bash
   `TPWT/utils/sens_prog/sensitivity.bash`

## python scripts

I have python scripts as interface to run tpwt.

It can do work flow from getting SAC from data (after pz and delta is 5Hz) to run tpwt and image.

`param.json` is the file including parameters.

### tpwt_1.py

Works like `01.bash`.

### tpwt_6_check.py

Not complete yet.

### tpwt all

I'm going to push `tpwt_all.py` which can do all test parameters.

## bash scripts

### 01.bash

Generate reference phase velocities for each pair of event and station,
then extract dispersion curves for each sac file.

Prepare files:

- event.lst: event lo la ma
- station.lst: station lo la

1. use

- `event.lst` don't use 2 events in the same period about 3 hours. Have 4 columns - "event lo la ma".

- `station.lst` Have 3 columns - "station lo la".
- `mk_pathfile` match event and station
- `TPWT/utils/RAYL_320_80_32000_8000.disp` raylei global model
- `TPWT/utils/LOVE_400_100.disp` love global model
- `aftani_c_pgl` extract snr curves.
- `spectral_snr` contral by snr, need use csh, I have modified the `.csh` to `.bash`.

2. set

3. generate

- `flag_GDM52`
- `path/`
  `event_station.PH_PRED` and `GDM52_dispersion.out`
- `SAC/event/`
  `1.bash`, `event.station.sac_1_DISP.0`, `event.station.sac_1_DISP.1`, `event.station.sac_2_DISP.0`, `event.station.sac_2_DISP.1`.
  Only `event.station.sac_1_DISP.0` will be used

      `event.station.sac_snr.yyj.txt`
      `filelist`, `flag_SNR`, `flag_aftan`, `param.dat`, `step.txt`, `temp.dat`

  `bash 01.bash`

### 02.bash

When I run `02.bash`, I unfortunately find that
the Z component name in sac file must be `.LHZ.`.

Then I modify the sac name. Thus I can get correct file `sta_dist.lst`.

And I should adjust parameters otherwise `snr_err` will appear.

1. use

- `find_phvel_amp_earthquake` format the pinsan according to event and zhouqi.
  generate `.ph.txt`
- `correct_tt_select_data` input mid points coordinate to remove bad points. Keep points which can satisfied less than the tmisfit.

2. set

- cutoff_per = 0.7
- snr = 10
- dist = 3500 the longest distance between two stations.
- tmisfit = 10

3. generate

- `sta_dist.lst`
- `all_events_20_150/{t}sec_{snr}snr_3500dis/`
  `{event}_am.txt`, `{event}_am.txt.HD{event}_am.txt_v1`, `{event}_am.txt_v1.HD`, `{event}.ph.txt`, `{event}.ph.txt.HD`, `{event}.ph.txt_v1`, `{event}.ph.txt_v1.HD`, `gmt.history`, `tomo.grd`

  `{event}.ph.txt` will be used in 02.bash self.

### 03.bash

1. use

- `wc`
- `sdiff`

2. set

- nsta_cutoff = 15
- Region: la and lo between maximum and minimium in a region should <10degree

3. generate

- `SAC/`
  `tempeq` and `eqlistper`: total number of stations to one event and the order number of the event.

### 04.bash

1. use

- `creatgridnode_TPWT` : create fan yan wang ge in `invrsnodes`.
- `avgvel` : average v
- `echo 5 {smooth_len} 0.25 0.25 >>{new_eqlistper}` :0.25 can be changed to 0.2 or not.
- `rd` : select event, should notice that the event number in sacfile name must be 12.

2. set

- snrcutoff = 10
- tcutoff = 12
- dist_cutoff = 3500 need > 3500
- nsta_cutoff = 15
- smooth_len = 80

3. generate

- `sens_dir/`
- `TPW_{snrcutoff}snr_{tcutoff}t_{dist_cutoff}_dist`
- `invrsnodes` fan yan wang ge jie dian.
- `eqlistper` (new): old `eqlistper` + some new information.
  detail can cha; summar ping jia; invrnodes fan yang wang ge jie dian; pham zhi qian de `.ph.txt` de chong xin zheng li.
- ``

- ``

### 05.bash

repeat 04, chose pham.V3

Result is in `new_2d` directory.

### 06.bash

It's check board.

---

## final result

The final result is 2 `grd.*` files in `new_2d`, `.ave` is perturbation.

And there are two `std*` files representing standard deviation in the `new_2d`.

## plot

There are some python scripts using `pygmt` to plot `grid.*.ave`.

Learning more about [pygmt](https://www.pygmt.org/latest/).

Files used in the script:

- grid.\*
- station.lst
- some data
