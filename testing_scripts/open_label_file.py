import numpy as np
import cv2
import pandas as pd
import matplotlib.pyplot as plt 
from pathlib import Path
import os
# import skimage as ski 

def mask_to_polygons(mask):
    # cv2.RETR_CCOMP flag retrieves all the contours and arranges them to a 2-level
    # hierarchy. External contours (boundary) of the object are placed in hierarchy-1.
    # Internal contours (holes) are placed in hierarchy-2.
    # cv2.CHAIN_APPROX_NONE flag gets vertices of polygons from contours.
    mask = np.ascontiguousarray(mask)  # some versions of cv2 does not support incontiguous arr
    contours, hierarchy = cv2.findContours(mask.astype("uint8"), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    # print(len(res))
    # hierarchy = res[-1]
    if hierarchy is None:  # empty mask
        return [], [], False
    has_holes = (hierarchy.reshape(-1, 4)[:, 3] >= 0).sum() > 0

    contours = [x.flatten() for x in contours]

    # # These coordinates from OpenCV are integers in range [0, W-1 or H-1].
    # # We add 0.5 to turn them into real-value coordinate space. A better solution
    # # would be to first +0.5 and then dilate the returned polygon by 0.5.
    # res = [x + 0.5 for x in res if len(x) >= 6]

    return contours, hierarchy, has_holes

print("OpenCV", cv2.__version__)

dataset_path = Path("/media/maxwell/Lucky_chicken/output_files_20221209_1")
output_path = Path("testing_scripts/output")

## define paths
rgb_path = dataset_path / "rgb"
pred_path = dataset_path / "panoptic_fpn_R_101_3x"

# filename = os.listdir(rgb_path)[].split(".")[0]
filename = "frame_3245"

mask_path = pred_path / "masks" / (filename + ".csv")
lbl_path  = pred_path / "labels" / (filename + ".csv")
img_path  = str(rgb_path / (filename + ".bmp"))

img = cv2.imread(img_path)
mask = np.genfromtxt(mask_path, delimiter=",")

# fig, axs = plt.subplots(1,2)
# axs[0].imshow(img)
# axs[1].imshow(mask)
# plt.show()

lbls = pd.read_csv(lbl_path)
# lbls.head()
wanted_catagories = [0,1,2,3,5,7,9,11]
for idx, row in lbls.iterrows():
    class_name = row["category_id"]
    if class_name not in wanted_catagories:
        continue
    
    mask_i = mask == row["id"]

    contours, hierarchy, has_holes = mask_to_polygons(mask_i)

    mask_i = (np.stack((mask_i,)*3, axis = -1) * 255).astype(np.uint8)
    
    ## grab only top polygon - maybe fix later 
    poly = contours[0]
    poly = poly.reshape(-1, 2).astype(int)
    mask_i = cv2.polylines(mask_i, [poly], True, (0,0,255), 1)

    cv2.imwrite(str(output_path / ("mask_{}.png".format(idx))), mask_i)
    