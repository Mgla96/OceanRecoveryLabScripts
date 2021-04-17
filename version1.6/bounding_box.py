import os
import Metashape as meta
import time
import sys
from typing import Tuple

"""
Delete points outside bounding box

Metashape 1.6.0 uses Python 3.5
"""


def prompt_path() -> Tuple[str, str]:
    """Initial prompt for path to metashape file

    Returns
    -------
    path_psx : str
        Input path of metashape file
    """
    meta.app.messageBox("Select Metashape File To Create Bounding Box")
    path_psx = meta.app.getOpenFileName("Select Metashape File To Create Bounding Box")
    return path_psx if path_psx[-3::].lower() == "psx" else ""


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
    """Main function for just deleting points outside bounding box

    Returns
    -------
    bool
        False if issue with photo paths and True if completed
    """

    path_psx = prompt_path()

    if path_psx == "":
        return False

    try:
        print("file: " + path_psx)

        doc = meta.app.document
        doc.open(path_psx)
        chunk = doc.chunk

        # optimize cameras
        chunk.optimizeCameras()

        # delete points outside bounding box
        R = chunk.region.rot  # Bounding box rotation matrix
        C = chunk.region.center  # Bounding box center vector
        size = chunk.region.size
        if not (chunk.point_cloud and chunk.enabled):
            return False
        elif not chunk.point_cloud.points:
            return False
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

    except RuntimeError as r_err:
        message = path_psx + ": error during bounding box: " + str(r_err)
        print(message)
        return False

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
            meta.app.messageBox(message)
            print(message)
