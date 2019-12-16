import json2frames as jf

video_path = "/home/common/rigidos/"
datasetFolder = "./dataset_rigidos/"

target_path_list = [datasetFolder + "PL0138/",
               datasetFolder + "PL0018"
]

json_file_list = ['./json_files/PL0138/annotations.json',
             './json_files/PL0018/annotations.json'
]

for json_file, target_path in zip(json_file_list, target_path_list):
    jf.get_frames(video_path, json_file, target_path, square=True, automatic_fill_duct=True)