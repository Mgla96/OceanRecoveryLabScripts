import os
import Metashape as meta
import math
import time
import sys
'''
alignanddelete will take a folder directory and loop through it's subfolders of separate coral treatments which consists of overlapping photos. 
This script will create a new chunk add and align photos, create tie points, estimate camera locations and delete all tie points outside bounding box. 
Then it will also delete pixels above a 0.5 reprojection error. Then this script will export these updated files to the user's designated location. 
'''


def promptPath():
    '''
    Initial prompt for path to photos and export folder
    '''
    path_photos, path_export = "", ""
    while True:
        meta.app.messageBox(
            "Select Input Photo Folder containing image files:")
        path_photos = meta.app.getExistingDirectory(
            "Select Input Photo Folder containing image files:")
        meta.app.messageBox("Select Export Folder")
        path_export = meta.app.getExistingDirectory("Select Export folder:")
        if path_photos == "" or path_export == "":
            print("input or export folder wasn't selected. Exiting script")
            meta.app.messageBox(
                "input or export folder wasn't selected. Exiting script")
            return "", ""
        elif path_photos == path_export:
            print("Separate folder should be selected for input and export folder")
            meta.app.messageBox(
                "Separate folder should be selected for input and export folder")
        elif len(os.listdir(path_photos)) < 1:
            print(
                "Folder not selected for input folder or input folder had no photos. Exiting script")
            meta.app.messageBox(
                "Folder not selected for input folder or input folder had no photos. Exiting script")
            return "", ""
        else:
            tmp = os.listdir(path_photos)
            if len(tmp) == 1 and (("jpg" or "jpeg") in tmp[0].lower()):
                print(
                    "Only 1 photo found. If true ignore message otherwise restart and select the folder rather than a photo")
                meta.app.messageBox(
                    "Only 1 photo found. If true ignore message otherwise restart and select the folder rather than a photo")
            break
    return path_photos, path_export


def main():
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # processing parameters - can edit the parameters here
    DOWNSCALE = 1  # Photo alignment accuracy - 1 is "high" not "highest"
    GENERIC_PRESELECTION = True
    KEYPOINTS = 40000  # align photos key point limit
    TIEPOINTS = 10000  # align photos tie point limit
    THRESHOLD = 0.5
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # get input and output folders
    path_photos, path_export = promptPath()
    if path_photos == "" or path_export == "":
        return False

    fold_list = os.listdir(path_photos)
    fold_list = filter(lambda x:x[0]!='.',fold_list) #getting rid of pesky files like .DS_Store
    for folder in fold_list:
        if not os.path.isfile(folder):
            # loading images
            folderPath = path_photos + divider + folder
            if os.path.isfile(folderPath):  # skip because it should be folder not file
                continue
            image_list,photo_list = os.listdir(folderPath),[] 
            image_list = filter(lambda x:x[0]!='.',image_list) #getting rid of pesky files like .DS_Store
            #print(image_list)
            for photo in image_list:
                # print(photo)
                if ("jpg" or "jpeg") in photo.lower():
                    photo_list.append(os.path.join(folderPath, photo))
            # only runs program on folder with photos in it (photo_list in chunk.addPhotos(photo_list) can't be empty)
            if not photo_list:
                print("found non photo folder")
                continue
            doc = meta.Document()
            doc.save(path_export+divider+folder+".psx")
            chunk = doc.addChunk()
            chunk.addPhotos(photo_list)
            # align photos
            chunk.matchPhotos(downscale=DOWNSCALE, generic_preselection=GENERIC_PRESELECTION,
                              filter_mask=False, keypoint_limit=KEYPOINTS, tiepoint_limit=TIEPOINTS)
            chunk.alignCameras()
            # Removing points outside bounding box
            chunk = doc.chunks[-1]
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
                    if abs(v_r.x) > abs(size.x / 2.):
                        point.valid = False
                    elif abs(v_r.y) > abs(size.y / 2.):
                        point.valid = False
                    elif abs(v_r.z) > abs(size.z / 2.):
                        point.valid = False
                    else:
                        continue
            # Points outside the region were removed. Read reprojection error and delete any 0.5 or greater
            f = meta.PointCloud.Filter()
            f.init(chunk, criterion=meta.PointCloud.Filter.ReprojectionError)
            f.removePoints(THRESHOLD)
            doc.save()
    return True


if __name__ == "__main__":
    meta.app.addMenuItem("Custom menu/Process 1", main)
    global divider
    divider = ""
    for i in range(1, len(sys.argv)):
        arg = sys.argv[i]
        if type(arg) == str:
            arg = arg.lower()
        if arg == "mac":
            divider = "/"
        if arg == "windows":
            divider = "\\"
    if divider == "":
        meta.app.messageBox(
            "In the arguments box type mac or windows based on which file system you are on")
    else:
        t0 = time.time()
        flag = main()
        t1 = time.time()
        if flag:
            meta.app.messageBox("Completed in "+str(int(t1-t0)) +
                                "seconds. Now define points & set scale bar distance before running optandbuild.py")
