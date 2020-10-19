import os
import Metashape as meta
#import photoscan
import math, time
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
    path_photos,path_export="",""
    while True:
        meta.app.messageBox("Specify Input Photo folder(folder containing all metashape files)")
        path_photos = meta.app.getExistingDirectory("Specify INPUT photo folder(folder containing all metashape files):")
        meta.app.messageBox("Specify Export Folder")
        path_export = meta.app.getExistingDirectory("Specify EXPORT folder:")
        if path_photos=="" or path_export=="":
            meta.app.messageBox("input or export folder wasn't selected. Exiting script")
            return "",""
        elif path_photos==path_export:
            meta.app.messageBox("For safety, a separate folder should be selected for the input and export folder. Please try again")
        elif len(os.listdir(path_photos))<1:
            meta.app.messageBox("A folder wasn't selected for the input folder or the input folder had no photos. Exiting script")
            return "",""
        else:
            tmp=os.listdir(path_photos)
            if len(tmp)==1 and (("jpg" or "jpeg") in tmp[0].lower()):
                meta.app.messageBox("Only one photo was found. If there were more photos please restart and click the folder rather than a photo. Otherwise ignore this message.")
            break
    return path_photos,path_export


def main():
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #processing parameters - can edit the parameters here
    downscale = 1 # Photo alignment accuracy - 1 is "high" not "highest"
    generic_preselection = True  
    keypoints = 40000 #align photos key point limit
    tiepoints = 10000 #align photos tie point limit
    threshold=0.5
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    #get input and output folders
    path_photos,path_export=promptPath()
    if path_photos=="" or path_export=="":
        return False

    fold_list = os.listdir(path_photos)
    for folder in fold_list:
        if not os.path.isfile(folder):
            #loading images
            folderPath = path_photos + divider + folder
            image_list = os.listdir(folderPath)
            photo_list = list()
            for photo in image_list:
                if ("jpg" or "jpeg") in photo.lower():
                    photo_list.append(os.path.join(folderPath,photo))
            doc = meta.Document()
            doc.save(path_export+divider+folder+".psx")
            chunk=doc.addChunk() 
            chunk.addPhotos(photo_list)
            #align photos
            chunk.matchPhotos(downscale = downscale, generic_preselection = generic_preselection, filter_mask = False, keypoint_limit = keypoints, tiepoint_limit = tiepoints)
            chunk.alignCameras()
            #Removing points outside bounding box
            chunk = doc.chunks[-1]
            R = chunk.region.rot#Bounding box rotation matrix
            C = chunk.region.center#Bounding box center vertor
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
            #Points outside the region were removed. Read reprojection error and delete any 0.5 or greater
            f = meta.PointCloud.Filter()
            f.init(chunk, criterion=meta.PointCloud.Filter.ReprojectionError)
            f.removePoints(threshold)
            doc.save()
    return True

if __name__=="__main__":
    meta.app.addMenuItem("Custom menu/Process 1", main)
    global divider
    divider=""
    for i in range (1, len(sys.argv)):
        arg = sys.argv[i]
        if type(arg)==str:
            arg=arg.lower()
        if arg=="mac":
            divider="/"
        if arg=="windows":
            divider="\\"
    if divider=="":
        meta.app.messageBox("In the arguments box type mac or windows based on which file system you are on")
    else:
        t0 = time.time()
        flag=main()
        t1 = time.time()
        if flag:
            meta.app.messageBox("Completed in "+str(int(t1-t0))+"seconds. Now define points & set scale bar distance before running optandbuild.py")
