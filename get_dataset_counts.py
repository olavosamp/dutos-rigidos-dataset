import numpy    as np
import pandas   as pd

from pathlib    import Path
from glob       import glob
import commons

datasetFolder = Path("./dataset_rigidos/")
#datasetFolder = Path("/home/olavosamp/projetos/projeto_final/henrique-pf/dataset_rigidos/")

classCounts = {}
for tag in commons.petro_class_table:
    globString = datasetFolder / "**" / tag /"**"/"*.jpg"

    imgList = glob(str(globString), recursive=True)
    classCounts[tag] = len(imgList)

print(classCounts)

targetPath = datasetFolder / "PL0018" / "targets.csv"
targets = pd.read_csv(targetPath)

print(targets["planta"].sum())