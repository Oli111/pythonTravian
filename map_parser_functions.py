import pandas as pd
from os import listdir
from datetime import datetime
from datetime import timedelta
from math import sqrt
def process_map_file(_dir_raw_data, _file_to_process):
    _date = datetime(year=int(_file_to_process[0:4]), month=int(_file_to_process[4:6]), day=int(_file_to_process[6:8]))
    print("Processing " + _file_to_process)
    df_raw = pd.read_csv(_dir_raw_data + "/" + _file_to_process, encoding='UTF-8', sep="/t", header=None)
    for index, row in df_raw.iterrows():
        _list_temp = row[0].split(",")
        if (len(row[0].split(",")) == 11):
            _df_temp = pd.DataFrame({'a':_list_temp}).transpose()
            try:
                _df_map = _df_map.append(_df_temp)
            except:
                _df_map = _df_temp
    _df_map.columns = ["todrop",
                      "coord_x",
                      "coord_y",
                      "todrop2",
                        "todrop3",
                      "village_name",
                      "someId",
                      "player_name",
                      "some_number",
                      "aliance_name",
                      "village_pop"]

    _df_map['village_pop'] = _df_map.apply(lambda x: x["village_pop"].strip(");"), 1)
    _df_map = _df_map[["coord_x", "coord_y", "village_name", "player_name", "aliance_name", "village_pop"]]
    _df_map['date'] = pd.to_datetime(_date)
    return _df_map

def preprocess_data(_dir_raw_data, _dir_preprocessed):
    _files_to_process = listdir(_dir_raw_data)
    for _file_to_process in _files_to_process:
        _df_map = process_map_file(_dir_raw_data, _file_to_process)
        _df_map.to_csv(_dir_preprocessed + "/" + _file_to_process.strip(".txt") + ".csv", index=False, encoding='UTF-8' )


def append_history_data(_dir_preprocessed):
    _data_paths_preproc = listdir(_dir_preprocessed)
    for path_preproc in _data_paths_preproc:
        print(path_preproc)
        _df_temp = pd.read_csv(_dir_preprocessed + "/" + path_preproc, encoding='UTF-8')
        try:
            _df_history = _df_history.append(_df_temp)
        except:
            _df_history = _df_temp
    return _df_history


_dir_raw_data = 'rawMapData'
_dir_preprocessed = "preprocessedMapData"