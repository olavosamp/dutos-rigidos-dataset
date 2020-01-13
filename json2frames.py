import os
import cv2
import json
import numpy    as np
import pandas   as pd
from time       import time, strptime
from tqdm       import tqdm
from pathlib    import Path

import commons

def create_folder(path, verbose=False):
    if not(os.path.isdir(path)):
        os.makedirs(path)

def string2seconds(time):
    hours = int(time.split(":")[0])
    minutes = int(time.split(":")[1])
    seconds = int(time.split(":")[2])
    time = hours*3600 + minutes*60 + seconds
    return time


def seconds2string(time):
    hours = time//3600
    minutes = (time - hours*3600)//60
    seconds = (time - hours*3600 - minutes*60)
    time = str(hours).zfill(2)+":"+str(minutes).zfill(2)+":"+str(seconds).zfill(2)
    return time


def mkdir(path):
    if os.path.isdir(path):
        print("Directory '"+path+"' already exists")
    else:
        try:
            os.makedirs(path)
        except OSError:
            print("'"+path+"' is an invalid path")


def istime(time_str):
    try:
        strptime(time_str, '%H:%M:%S')  # testar se esta em formato de tempo
        return True
    except:
        return False


def gen_target(tags, labels):
    vec = [0]*len(tags)  # [0,0,..,0]
    for label in labels:
        for i, tag in enumerate(tags):
            if (label == tag):
                vec[i] = 1
    return vec


def get_times_from_annotations(anns, tags, video_name, verbose=True):
        #instante de inicio de cada tag
    begin_time_string = []
    end_time_string = []
    targets_list = []

    for ann in anns:
        if (gen_target(tags, ann["tags"]) != [0]*len(tags)):
            if istime(ann["startTime"]):
                if "endTime" in ann:
                    if istime(ann["endTime"]):
                        begin_time_string.append(ann["startTime"])
                        targets_list.append(gen_target(tags, ann["tags"]))
                        end_time_string.append(ann["endTime"])
                    else:
                        if verbose is True:
                            print("Bad time annotation on video '"+video_name+"'")
                            print("endTime not in a correct time format")
                            print("{'startTime': '"+ann["startTime"]
                                  + "', 'endTime': '"+ann["endTime"]
                                  + "', 'tags':", ann["tags"], "}")
    #                     print(ann)
                else:  # se nao tiver o endtime, adiciona 1s ao startime
                    begin_time_string.append(ann["startTime"])
                    targets_list.append(gen_target(tags, ann["tags"]))
                    time = ann["startTime"]
                    time = string2seconds(time)+1
                    time = seconds2string(time)
                    end_time_string.append(time)
            else:
                if verbose is True:
                    print("Bad time annotation on video '"+video_name+"'")
                    print("startTime not in a correct time format")
                    print("{'startTime': '"+ann["startTime"]
                          + "', 'tags':", ann["tags"], "}")
#                 print(ann)

    begin_time_seconds = [string2seconds(i) for i in begin_time_string]
    end_time_seconds = [string2seconds(i) for i in end_time_string]

    return begin_time_string, begin_time_seconds, end_time_string, end_time_seconds, targets_list


def get_duct_times_from_json(json_data, video_name, event_tags, video_idx, confusion_time=1):
    video_end = [video["videoEndTime"]
                 for video in json_data["videos"] if video["videoName"] == video_name][0]
    beginings_sec = []
    ends_sec = []

    annotations = json_data["videos"][video_idx]["annotations"]
    __, beginings_sec, __, ends_sec, __ = get_times_from_annotations(
        annotations, event_tags, video_name, False)

    beginings_sec = sorted(beginings_sec)
    ends_sec = sorted(ends_sec)

    beginings_sec = [begining-confusion_time for begining in beginings_sec]
    ends_sec = [end+confusion_time for end in ends_sec]

    duct_beginings_sec = ends_sec
    duct_ends_sec = beginings_sec

    duct_beginings_sec.insert(0, 0)
    duct_ends_sec.append(string2seconds(video_end))
    duct_beginings_str = [seconds2string(sec) for sec in duct_beginings_sec]
    duct_ends_str = [seconds2string(sec) for sec in duct_ends_sec]

    return duct_beginings_str, duct_beginings_sec, duct_ends_str, duct_ends_sec


def fill_tgs(tgs, begin_seconds, end_seconds, targets):
    for i, t in enumerate(begin_seconds):
        instants = range(begin_seconds[i], end_seconds[i])
        for instant in instants:
            if (type(targets[0]) == list):
                assert(len(targets) == len(begin_seconds))
                tgs.loc[instant] = np.bitwise_or(tgs.loc[instant], targets[i])
            else:
                tgs.loc[instant] = np.bitwise_or(tgs.loc[instant], targets)
    return tgs

# def generate_frames(beginings_str, beginings_sec, ends_str, ends_sec, video, target_path, video_name, tag, frame_rate, auto_tag, offset, square):

def convert_petro_tags(tagList):
    if isinstance(tagList, str):
        tagList = [tagList]

    newTagList = []
    for tag in tagList:
        # if tag in commons.class_translation_table.values():
        #     newTagList.append(commons.class_translation_table[tag])
        newTagList.extend(commons.class_translation_table.get(tag, [commons.UNUSED_CLASS]))
    return newTagList


def generate_frames_and_targets(targets, frameid, tgs, frame_rate, video, target_path,
                                video_name, automatic_tagging, offset, square):
    frame_rate_options = [frame_rate, commons.clean_duct_frame_rate]
    target_options = [gen_target(commons.tags, commons.event_tags),
                      gen_target(commons.tags, [commons.clean_duct_tag])]

    times = np.linspace(0, 1, frame_rate_options[automatic_tagging], endpoint=False)
    target_mask = target_options[automatic_tagging]

    indexToDrop = []
    for i in range(len(tgs)):
        for j in range(len(times)):
            if (np.sum(np.bitwise_and(tgs.loc[i].values.tolist(), target_mask)) > 0):
                frame_time = i + times[j]
                video.set(cv2.CAP_PROP_POS_MSEC, (frame_time+offset)*1000)
                errRead, frame = video.read()
                if frame is not None:
                    if square is True:
                        border = int((frame.shape[1] - frame.shape[0])/2)
                        frame = frame[:, border:frame.shape[1]-border, :]

                    targets.loc[frameid] = tgs.loc[i]
                    target_name = str(frameid)+"_"+video_name+"_" + \
                        seconds2string(i).replace(":", "-")+"_"+str(j)+".jpg"

                    folderName = video_name
                    dropFlag = True
                    for targetName in commons.class_priority_table:
                        tags = convert_petro_tags(targetName)
                        labelSum = 0
                        # print("Tags\n", tags)
                        for subTag in tags: # Check if any translated tag equals 1 in target table
                            # print(subTag)
                            if subTag in targets.columns:
                                labelSum += int(targets.loc[frameid, subTag])

                        # if targets.loc[frameid, tag] == 1:
                        if labelSum >= 1:
                            frameDestPath = Path("/".join([target_path, targetName, folderName, target_name]))
                            create_folder(frameDestPath.parent)
                            errWrite = cv2.imwrite(str(frameDestPath), frame)
                            dropFlag = False
                    if dropFlag:
                        indexToDrop.append(frameid)
                    frameid += 1
    return targets, frameid


def get_frames(video_path, json_file, target_path, frame_rate=3, automatic_fill_duct=True, confusion_time=1,
               offset=0, square=False):
    '''
        Function to extract frames from mp4 video using a json file.

        Parameters:
            video_path (str): Directory with mp4 videos

            json_file (str): JSON file path

            target_path (str): Directory for images destination

            frame_rate (int): Extraction frame rate (frames/s)

            automatic_fill_duct (bool): Automatic fill not annotated frames as duct

            confusion_time (int): Time between annotated frames and automatic filling

            offset (int): Offset to start of time count

            square (bool): Square frames

    '''
    begin = time()

    with open(json_file) as f:
        jason = json.load(f)

    video_list = [i for i in os.listdir(video_path) if i.endswith(".mp4")]

    mkdir(target_path)

    if os.path.isfile(os.path.join(target_path, 'targets.csv')):
        targets = pd.read_csv(os.path.join(target_path, 'targets.csv'), index_col=0)
    else:
        targets = pd.DataFrame([], columns=commons.tags)
    frameid = len(targets)

    annotated_video_list = [video["videoName"]+".mp4" for video in jason["videos"]]
    for video_full_name in tqdm(video_list):
        video_name = video_full_name.split(sep=".")[0]
        videoPath = os.path.join(video_path, video_full_name)
        video = cv2.VideoCapture(videoPath)
        print(videoPath)

        video_found = False
        for annotated_video in annotated_video_list:
            if(video_full_name == annotated_video):
                video_found = True
                video_idx = [i for i, e in enumerate(
                    jason["videos"]) if e["videoName"] == video_name][0]
                zeros = [gen_target(commons.tags, ['_'])] * \
                    (string2seconds(jason["videos"][video_idx]["videoEndTime"]))
                tgs = pd.DataFrame(zeros, columns=commons.tags)
                annotations = jason["videos"][video_idx]["annotations"]

                __, begin_seconds, __, end_seconds, targets_list = get_times_from_annotations(annotations,
                                                                  commons.tags, video_name)
                tgs = fill_tgs(tgs, begin_seconds, end_seconds, targets_list)

                __, begin_seconds, __, end_seconds = get_duct_times_from_json(jason,
                                                                  video_name, commons.alteration_tags, video_idx)
                tgs = fill_tgs(tgs, begin_seconds, end_seconds, gen_target(commons.tags, ['duto']))

                if "offset" in jason["videos"][video_idx]:
                    offset = float(jason["videos"][video_idx]["offset"])
                automatic_tagging = False
                targets, frameid = generate_frames_and_targets(targets, frameid, tgs, frame_rate, video,
                                                               target_path, video_name, automatic_tagging,
                                                               offset, square)

                if automatic_fill_duct:
                    automatic_tagging = True
                    targets, frameid = generate_frames_and_targets(targets, frameid, tgs, frame_rate, video,
                                                                   target_path, video_name, automatic_tagging,
                                                                   offset, square)
                break
        if not video_found:
            print("There are no annotations for video "+video_full_name)
    # tgs.to_csv(os.path.join(target_path,'tgs.csv'))

    targets.to_csv(os.path.join(target_path, 'targets.csv'))
    end = time()
    print("\nThe conversion took "+seconds2string(round(end-begin)))


def get_times_per_tag(json_data, tag, video_name, auto_tag):
    video_idx = [i for i, e in enumerate(json_data["videos"]) if e["videoName"] == video_name][0]
    #instante de inicio de cada tag
    begin_time_string = []
    end_time_string = []

    for annotation in json_data["videos"][video_idx]["annotations"]:
        if tag in annotation["tags"]:
            if istime(annotation["startTime"]):
                begin_time_string.append(annotation["startTime"])
            else:
                if not auto_tag:
                    print("Bad time annotation on video '"+video_name+"'")
                    print(annotation)
                    print("startTime not in a correct time format")
            if "endTime" in annotation:
                if istime(annotation["endTime"]):
                    # se nao tiver o endtime, adiciona 1s ao startime
                    end_time_string.append(annotation["endTime"])
                else:
                    if not auto_tag:
                        print("Bad time annotation on video '"+video_name+"'")
                        print(annotation)
                        print("endTime not in a correct time format")
            else:
                time = annotation["startTime"]
                time = string2seconds(time)+1
                time = seconds2string(time)
                end_time_string.append(time)

    begin_time_seconds = [string2seconds(btime) for btime in begin_time_string]
    end_time_seconds = [string2seconds(etime) for etime in end_time_string]

    return begin_time_string, begin_time_seconds, end_time_string, end_time_seconds


def generate_frames(beginings_str, beginings_sec, ends_str, ends_sec, video, target_path, video_name, tag, frame_rate, auto_tag, offset, square):
    for i, t in enumerate(beginings_sec):
        if (ends_sec[i] - beginings_sec[i] > 0):
            for j, frame_time in enumerate(np.linspace(beginings_sec[i],
                                                       ends_sec[i],
                                                       frame_rate*(ends_sec[i] - beginings_sec[i]),
                                                       endpoint=False)):
                video.set(cv2.CAP_PROP_POS_MSEC, (frame_time+offset)*1000)
                #print("frametime: "+str(round(frame_time, 2))+", tag: "+tag)
                errRead, frame = video.read()
                if frame is not None:
                    if square is not False:
                        border = int((frame.shape[1] - frame.shape[0])/2)
                        frame = frame[:, border:frame.shape[1]-border, :]
                    target_name = video_name+'_'+tag+'_' + \
                        beginings_str[i].replace(":", "-")+"_"+str(j)+'.jpg'
                    errWrite = cv2.imwrite(os.path.join(target_path, tag, target_name), frame)
        else:
            if not auto_tag:
                print("Bad time annotation on video '"+video_name)
                print("'{startTime: '"+beginings_str[i]
                      + "', 'endTime': '"+ends_str[i]
                      + "', 'tags': ['"+tag+"']}")
                print("startTime >= endTime")


def get_duct_times_per_tag(json_data, video_name, event_tags, confusion_time=1):
    video_end = [video["videoEndTime"]
                 for video in json_data["videos"] if video["videoName"] == video_name][0]
    beginings_sec = []
    ends_sec = []

    for tag in event_tags:
        beg_str, beg_sec, end_str, end_sec = get_times_per_tag(json_data, tag, video_name, True)
        beginings_sec.extend(beg_sec)
        ends_sec.extend(end_sec)

    beginings_sec = sorted(beginings_sec)
    ends_sec = sorted(ends_sec)

    beginings_sec = [begining-confusion_time for begining in beginings_sec]
    ends_sec = [end+confusion_time for end in ends_sec]

    duct_beginings_sec = ends_sec
    duct_ends_sec = beginings_sec

    duct_beginings_sec.insert(0, 0)
    duct_ends_sec.append(string2seconds(video_end))
    duct_beginings_str = [seconds2string(sec) for sec in duct_beginings_sec]
    duct_ends_str = [seconds2string(sec) for sec in duct_ends_sec]

    return duct_beginings_str, duct_beginings_sec, duct_ends_str, duct_ends_sec


def get_frames_per_tag(video_path, json_file, target_path, frame_rate=3, automatic_fill_duct=True, confusion_time=1, offset=0, square=False):
    #as tags estao no commons
    #o offset eh porque tem video que apesar de passar o tempo certo a funcao pega o frame defasado
    begin = time()

    with open(json_file) as f:
        jason = json.load(f)

    video_list = [i for i in os.listdir(video_path) if i.endswith(".mp4")]

    mkdir(target_path)
    for tag in commons.tags:
        mkdir(os.path.join(target_path, tag))

    annotated_video_list = [video["videoName"]+".mp4" for video in jason["videos"]]
    for video_full_name in tqdm(video_list):
        video_name = video_full_name.split(sep=".")[0]
        video = cv2.VideoCapture(os.path.join(video_path, video_full_name))
        video_found = False
        for annotated_video in annotated_video_list:
            if(video_full_name == annotated_video):
                video_found = True
                video_idx = [i for i, e in enumerate(
                    jason["videos"]) if e["videoName"] == video_name][0]
                if "offset" in jason["videos"][video_idx]:
                    offset = float(jason["videos"][video_idx]["offset"])
                for tag in commons.tags:
                    begin_string, begin_seconds, end_string, end_seconds = get_times_per_tag(
                        jason, tag, video_name, False)
                    automatic_tag = False
                    # print("gerando "+tag)
                    generate_frames(begin_string, begin_seconds, end_string, end_seconds, video,
                                    target_path, video_name, tag, frame_rate, automatic_tag, offset, square)

                if automatic_fill_duct:
                    automatic_tag = True
                    begin_str, begin_sec, end_str, end_sec = get_duct_times_per_tag(
                        jason, video_name, commons.alteration_tags)
                    generate_frames(begin_str, begin_sec, end_str, end_sec, video, target_path, video_name,
                                    commons.clean_duct_tag, commons.clean_duct_frame_rate, automatic_tag, offset, square)

        if not video_found:
            print("There are no annotations for video "+video_full_name)

    end = time()
    print("The conversion took "+seconds2string(round(end-begin)))
