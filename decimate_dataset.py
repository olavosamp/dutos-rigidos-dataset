import os
import shutil
import numpy    as np
import pandas   as pd
from glob       import glob
from tqdm       import tqdm
from pathlib    import Path

import commons

def _make_path(x): return Path(x)
def _get_class(x): return str(x.parts[-3])

def create_folder(path, verbose=False):
    if not(os.path.isdir(path)):
        os.makedirs(path)

def _copy_to_folder(path, folder):
    newPath = Path("/".join(Path(path).parts[1:]))
    newPath = folder / newPath
    create_folder(newPath.parent)
    shutil.copy2(path, newPath)


datasetPath = "dataset_rigidos"
newDatasetFolder = datasetPath + "_decimated"

decimation_table = {
                    'algas':    2,
                    'anodo':    0,
                    'dano':     0,
                    'duto':     10,
                    'peixe':    2,
                    'sucata':   0,
                    'variacao': 2,
                    }

# Get filepaths of all dataset images
globString = datasetPath+"/**/*jpg"
imgList = glob(globString, recursive=True)

# Sort images by class
imgList = list(map(_make_path, imgList))
classList = list(map(_get_class, imgList))
imgDf = pd.DataFrame({'class': classList, 'path': imgList})


# Operate on each class separately
groupDataset = imgDf.groupby('class')
newDatasetDf = pd.DataFrame()
for className, groupDf in groupDataset:
    # Decimate classes according to decimation_table
    decimationRate = decimation_table[className]
    
    pathList = groupDf['path'].values
    pathList.sort()
    classSize = len(pathList)

    indexToKeep = []
    if decimationRate == 0:
        # Decimation rate of zero means to not decimate that class
        indexToKeep = list(range(classSize))
    else:
        for i in range(classSize):
            if (i != 0):
                if ((i % decimationRate) == 0):
                    indexToKeep.append(i)
    decimatedDf = pd.DataFrame(pathList)
    decimatedDf = decimatedDf.loc[indexToKeep, :]
    # decimatedDf.drop(indexToKeep, axis=0, inplace=True)

    print("\nClass: {}\nDecimation Rate: {}\nOld len: {}\nNew len: {}\n".format(className, decimationRate, classSize, len(decimatedDf)))

    newDatasetDf = newDatasetDf.append(decimatedDf, sort=False, ignore_index=True)

newLen = len(newDatasetDf)
print(newLen)

# Copy new dataset to new folder
for i in tqdm(range(newLen)):
    path = newDatasetDf.loc[i, 0]
    _copy_to_folder(path, newDatasetFolder)
print("New dataset at {}.\nIt has {} images.".format(newDatasetFolder, newLen))