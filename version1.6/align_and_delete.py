import os
import Metashape as meta
import math
import time
import sys
import typing
import logging
from typing import Tuple

"""
alignanddelete will take a folder directory and loop through it's subfolders of separate coral treatments which consists of overlapping photos. 
This script will create a new chunk add and align photos, create tie points, estimate camera locations and delete all tie points outside bounding box. 
Then it will also delete pixels above a 0.5 reprojection error. Then this script will export these updated files to the user's designated location. 

Metashape 1.6.0 uses Python 3.5
"""
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# processing parameters - can edit the parameters here
DOWNSCALE = 1  # Photo alignment accuracy - 1 is "high" not "highest"
GENERIC_PRESELECTION = True
KEYPOINTS = 40000  # align photos key point limit
TIEPOINTS = 10000  # align photos tie point limit
THRESHOLD = 0.5
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
DOWNSCALE = 64


def prompt_path() -> Tuple[str, str]:
    """Initial prompt for path to photos and export folder

    Returns
    -------
    path_photos : str
        Input path of photos
    path_export : str
        Export path of metashape files
    """
    path_photos, path_export = "", ""
    while True:
        meta.app.messageBox("Select Input Photo Folder containing image files:")
        path_photos = meta.app.getExistingDirectory(
            "Select Input Photo Folder containing image files:"
        )
        meta.app.messageBox("Select Export Folder")
        path_export = meta.app.getExistingDirectory("Select Export folder:")
        if path_photos == "" or path_export == "":
            print("input or export folder wasn't selected. Exiting script")
            meta.app.messageBox(
                "input or export folder wasn't selected. Exiting script"
            )
            return "", ""
        elif path_photos == path_export:
            print("Separate folder should be selected for input and export folder")
            meta.app.messageBox(
                "Separate folder should be selected for input and export folder"
            )
        elif len(os.listdir(path_photos)) < 1:
            print(
                "Folder not selected for input folder or input folder had no photos. Exiting script"
            )
            meta.app.messageBox(
                "Folder not selected for input folder or input folder had no photos. Exiting script"
            )
            return "", ""
        else:
            tmp = os.listdir(path_photos)
            if len(tmp) == 1 and (("jpg" or "jpeg") in tmp[0].lower()):
                print(
                    "Only 1 photo found. If true ignore message otherwise restart and select the folder rather than a photo"
                )
                meta.app.messageBox(
                    "Only 1 photo found. If true ignore message otherwise restart and select the folder rather than a photo"
                )
            break
    return path_photos, path_export


def guess_os() -> Tuple[str, str]:
    """Attempts to guess the os and set the path divider to correct format

    Returns
    -------
    str
        / or \\ depending on OS
    str
        guessed OS
    """
    if sys.platform.startswith("linux"):
        return "/", "linux"
    elif sys.platform.startswith("darwin"):
        return "/", "macOS"
    elif sys.platform.startswith("win32"):
        return "\\", "windows"
    elif sys.platform.startswith("cygwin"):
        return "\\", "windows/cygwin"
    return "", ""


def main() -> bool:
    """Main function for handling align and delete

    This will create a new chunk, add and align photos, create tie points, estimate camera locations and delete all tie points outside bounding box.
    Then it will delete pixels above a 0.5 reprojection error.

    Returns
    -------
    bool
        False if issue with photo paths and True if align and delete completed
    """
    path_photos, path_export = prompt_path()

    if path_photos == "" or path_export == "":
        return False

    # logging
    logger = logging.getLogger()
    logger.handlers.clear()
    f_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    f_handler = logging.FileHandler(
        filename=path_photos + "/align_and_delete.log", mode="a"
    )
    f_handler.setFormatter(f_formatter)
    logger.addHandler(f_handler)
    logger.setLevel(logging.DEBUG)

    # get rid of pesky files like .DS_Store
    fold_list = filter(
        lambda x: x[0] != "." and x[-3:] != "log", os.listdir(path_photos)
    )

    logger.info("starting align_and_delete")

    for folder in fold_list:
        if not os.path.isfile(folder):
            # loading images
            folderPath = path_photos + divider + folder
            if os.path.isfile(folderPath):  # skip because it should be folder not file
                continue
            photo_list = []
            # getting rid of pesky files like .DS_Store
            image_list = filter(lambda x: x[0] != ".", os.listdir(folderPath))
            for photo in image_list:
                if ("jpg" or "jpeg") in photo.lower():
                    photo_list.append(os.path.join(folderPath, photo))
            # only runs program on folder with photos in it (photo_list in chunk.addPhotos(photo_list) can't be empty)
            if not photo_list:
                print("found non photo folder")
                logger.info("found non photo folder")
                continue
            doc = meta.Document()
            doc.save(path_export + divider + folder + ".psx")

            try:
                chunk = doc.addChunk()
                chunk.addPhotos(photo_list)
                # align photos
                chunk.matchPhotos(
                    downscale=DOWNSCALE,
                    generic_preselection=GENERIC_PRESELECTION,
                    filter_mask=False,
                    keypoint_limit=KEYPOINTS,
                    tiepoint_limit=TIEPOINTS,
                )
                chunk.alignCameras()
                chunk = doc.chunks[-1]

                # delete points outside bounding box
                R = chunk.region.rot  # Bounding box rotation matrix
                C = chunk.region.center  # Bounding box center vertor
                size = chunk.region.size
                if not (chunk.point_cloud and chunk.enabled):
                    continue
                elif not len(chunk.point_cloud.points):
                    continue
                for point in chunk.point_cloud.points:
                    if point.valid:
                        v = point.coord
                        v.size = 3
                        v_c = v - C
                        v_r = R.t() * v_c
                        if abs(v_r.x) > abs(size.x / 2.0):
                            point.valid = False
                        elif abs(v_r.y) > abs(size.y / 2.0):
                            point.valid = False
                        elif abs(v_r.z) > abs(size.z / 2.0):
                            point.valid = False
                        else:
                            continue

                # Points outside the region were removed. Read reprojection error and delete any 0.5 or greater
                f = meta.PointCloud.Filter()
                f.init(chunk, criterion=meta.PointCloud.Filter.ReprojectionError)
                f.removePoints(THRESHOLD)
                doc.save()
                print("completed align_and_delete for:", folder)
                logger.info(folder + ": completed align_and_delete")
            except RuntimeError as r_err:
                logger.error(folder + ": " + str(r_err))
    return True


if __name__ == "__main__":
    global divider
    divider = ""

    # get OS if specified
    for i in range(1, len(sys.argv)):
        arg = sys.argv[i]
        if type(arg) == str:
            arg = arg.lower()
        if arg == "mac":
            divider = "/"
        if arg == "windows":
            divider = "\\"

    # no OS specified, attempts to guess os
    if divider == "":
        divider, message = guess_os()
        if message != "":
            meta.app.messageBox("Guessing OS: " + message)
            print(
                "If guessed OS wrong, in the arguments box type mac or windows based on which os you are on"
            )

    if divider == "":
        meta.app.messageBox(
            "In the arguments box type mac or windows based on which os system you are on"
        )
        print(
            "In arguments box type mac or windows based on which os system you are on"
        )
    else:
        t0 = time.time()
        flag = main()
        t1 = time.time()
        total_time = int(t1 - t0)
        if flag:
            message = "Completed in " + str(total_time) + " seconds."
            meta.app.messageBox(
                "Completed in "
                + str(total_time)
                + " seconds.\n Now define points & set scale bar distance before running optandbuild.py"
            )
            print(
                "Completed in",
                total_time,
                "seconds.\nNow define points & set scale bar distance before running optandbuild.py",
            )
