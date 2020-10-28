import os
import Metashape as meta
import math
import time
import sys
'''
optandbuild will be called after the user defines points and set scale bar distance. 
This script will optimize cameras, delete other points outside bounding box, build dense cloud, then delete more pixels above a 0.5 reprojection error. 
Then it will repeat this process for all coral treatments.
'''


def promptPath():
    '''
    Initial prompt for path to photos and export folder
    '''
    path_photos, path_export = "", ""
    while True:
        meta.app.messageBox(
            "Select Input folder(folder containing all metashape files:")
        path_photos = meta.app.getExistingDirectory(
            "Select Input folder(folder containing all metashape files:")
        meta.app.messageBox("Select Export folder")
        path_export = meta.app.getExistingDirectory("Select Export folder:")
        if path_photos == "" or path_export == "":
            print("input or export folder wasn't selected. Exiting script")
            meta.app.messageBox(
                "input or export folder wasn't selected. Exiting script")
            return "", ""
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
    SURFACE = meta.SurfaceType.Arbitrary  # build mesh surface type
    # Photo alignment accuracy - 2 is "high quality" (want high quality not ultra high quality)
    DOWNSCALE = 2
    FILTERING = meta.FilterMode.MildFiltering  # depth filtering
    INTERPOLATION = meta.Interpolation.EnabledInterpolation  # build mesh interpolation
    FACE_NUM = meta.FaceCount.HighFaceCount  # build mesh polygon count
    MAPPING = meta.MappingMode.GenericMapping  # build texture mapping
    ATLAS_SIZE = 8192
    BLENDING = meta.BlendingMode.MosaicBlending  # blending mode
    VOLUMETRIC_MASKS = True
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # get input and output folders
    path_photos, path_export = promptPath()
    if path_photos == "" or path_export == "":
        return False

    # get all psx files
    psx_list = filter(lambda x: x.lower()
                      [-3::] == 'psx', os.listdir(path_photos))

    for psx in psx_list:
        doc = meta.app.document
        doc.open(path_photos+divider+psx)
        chunk = doc.chunk
        # optimize cameras
        chunk.optimizeCameras()
        R = chunk.region.rot  # Bounding box rotation matrix
        C = chunk.region.center  # Bounding box center vector
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
        # Read reprojection Error and delete any 0.5 or greater
        f = meta.PointCloud.Filter()
        f.init(chunk, criterion=meta.PointCloud.Filter.ReprojectionError)
        f.removePoints(0.5)
        # building dense cloud
        chunk.buildDepthMaps(downscale=DOWNSCALE, filter_mode=FILTERING)
        chunk.buildDenseCloud(point_colors=True)
        # building mesh
        chunk.buildModel(surface_type=SURFACE, interpolation=INTERPOLATION,
                         face_count=FACE_NUM, volumetric_masks=VOLUMETRIC_MASKS)
        # build texture
        chunk.buildUV(mapping_mode=MAPPING, page_count=1)
        chunk.buildTexture(blending_mode=BLENDING, texture_size=ATLAS_SIZE)
        meta.app.update()
        doc.save(path_export+divider+psx+".psx")

    return True


if __name__ == "__main__":
    meta.app.addMenuItem("Custom menu/Process 2", main)
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
            meta.app.messageBox("Completed in " + str(int(t1-t0))+"seconds.")
