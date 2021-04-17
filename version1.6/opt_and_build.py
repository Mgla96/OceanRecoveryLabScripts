import os
import Metashape as meta
import time
import sys
import logging
from typing import Tuple

"""
optandbuild will be called after the user defines points and set scale bar distance. 
This script will optimize cameras, delete other points outside bounding box, build dense cloud, then delete more pixels above a 0.5 reprojection error. 
Then it will repeat this process for all coral treatments.

Metashape 1.6.0 uses Python 3.5
"""
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# processing parameters - can edit the parameters here
SURFACE = meta.SurfaceType.Arbitrary  # build mesh surface type
DOWNSCALE = 2  # Photo alignment accuracy - 2 is "high quality" (want high quality not ultra high quality)
FILTERING = meta.FilterMode.MildFiltering  # depth filtering
INTERPOLATION = meta.Interpolation.EnabledInterpolation  # build mesh interpolation
FACE_NUM = meta.FaceCount.HighFaceCount  # build mesh polygon count
MAPPING = meta.MappingMode.GenericMapping  # build texture mapping
ATLAS_SIZE = 8192
BLENDING = meta.BlendingMode.MosaicBlending  # blending mode
VOLUMETRIC_MASKS = True
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def prompt_path() -> Tuple[str, str]:
    """Initial prompt for path to photos and export folder

    Returns
    -------
    path_photos : str
        Input path of metashape files`
    path_export : str
        Export path of metashape files
    """
    path_photos, path_export = "", ""
    while True:
        meta.app.messageBox(
            "Select Input folder(folder containing all metashape files:"
        )
        path_photos = meta.app.getExistingDirectory(
            "Select Input folder(folder containing all metashape files:"
        )
        meta.app.messageBox("Select Export folder")
        path_export = meta.app.getExistingDirectory("Select Export folder:")
        if path_photos == "" or path_export == "":
            print("input or export folder wasn't selected. Exiting script")
            meta.app.messageBox(
                "input or export folder wasn't selected. Exiting script"
            )
            return "", ""
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
    """Main function for handling opt and build

    This will optimize cameras, delete other points outside bounding box, build dense cloud,
    then delete more pixels above a 0.5 reprojection error.
    Then it will repeat this process for all coral treatments.

    Returns
    -------
    bool
        False if issue with photo paths and True if opt and build completed
    """
    # get input and output folders
    path_photos, path_export = prompt_path()
    if path_photos == "" or path_export == "":
        return False

    # create logger
    logger = logging.getLogger()
    logger.handlers.clear()
    f_handler = logging.FileHandler(
        filename=path_photos + divider + "opt_and_build.log", mode="a"
    )
    f_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    f_handler.setFormatter(f_formatter)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(f_handler)

    # get all psx files
    psx_list = filter(lambda x: x.lower()[-3::] == "psx", os.listdir(path_photos))

    logger.info("starting opt_and_build")

    for psx in psx_list:
        logger.info(psx)
        doc = meta.app.document
        doc.open(path_photos + divider + psx)
        chunk = doc.chunk

        # optimize cameras
        chunk.optimizeCameras()

        # delete points outside bounding box
        # https://www.agisoft.com/forum/index.php?topic=9030.0
        R = chunk.region.rot  # Bounding box rotation matrix
        C = chunk.region.center  # Bounding box center vector
        size = chunk.region.size
        if not (chunk.point_cloud and chunk.enabled):
            continue
        elif not chunk.point_cloud.points:
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

        # read reprojection Error and delete any 0.5 or greater
        f = meta.PointCloud.Filter()
        f.init(chunk, criterion=meta.PointCloud.Filter.ReprojectionError)
        f.removePoints(0.5)

        try:
            # building dense cloud
            chunk.buildDepthMaps(downscale=DOWNSCALE, filter_mode=FILTERING)
            chunk.buildDenseCloud(point_colors=True)
            # saving
            doc.save(path_export + divider + psx)
            doc.open(path_export + divider + psx)
            chunk = doc.chunk
            message = psx + ": saved after dense cloud"
            logger.info(message)

        except RuntimeError as r_err:
            message = psx + ": error during dense cloud: " + str(r_err)
            print(message)
            logger.error(message)
            # issue with this project so moving to next
            continue

        # building mesh
        try:
            chunk.buildModel(
                surface_type=SURFACE,
                interpolation=INTERPOLATION,
                face_count=FACE_NUM,
                volumetric_masks=VOLUMETRIC_MASKS,
            )
            doc.save(path_export + divider + psx)
            doc.open(path_export + divider + psx)
            chunk = doc.chunk
            message = psx + ": saved after build model"
            logger.info(message)
        except RuntimeError as r_err:
            message = psx + ": error during build model: " + str(r_err)
            print(message)
            logger.error(message)
            continue

        # saving
        try:
            # build texture
            chunk.buildUV(mapping_mode=MAPPING, page_count=1)
            chunk.buildTexture(blending_mode=BLENDING, texture_size=ATLAS_SIZE)
            doc.save(path_export + divider + psx)
            print("saved ", psx, " after build texture")
            message = psx + ": saved after build texture"
            logger.info(message)

        except RuntimeError as r_err:
            message = psx + ": error during build texture: " + str(r_err)
            print(message)
            logger.error(message)

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
            "In arguments box type mac or windows based on which os system you are on"
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
            meta.app.messageBox(message)
            print(message)
