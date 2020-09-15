import os
import PhotoScan
import math, time
'''
alignanddelete will take a folder directory and loop through it's subfolders of separate coral treatments which consists of overlapping photos. 
This script will create a new chunk add and align photos, create tie points, estimate camera locations and delete all tie points outside bounding box. 
Then it will also delete pixels above a 0.5 reprojection error. Then this script will export these updated files to the user's designated location. 
'''
def main():
    #prompting for path to photos
    path_photos,path_export="",""
    while True:
        PhotoScan.app.messageBox("Specify Input Photo folder(folder containing all metashape files)")
        path_photos = PhotoScan.app.getExistingDirectory("Specify INPUT photo folder(folder containing all metashape files):")
        PhotoScan.app.messageBox("Specify Export Folder")
        path_export = PhotoScan.app.getExistingDirectory("Specify EXPORT folder:")
        if path_photos=="" or path_export=="":
            PhotoScan.app.messageBox("input or export folder wasn't selected. Exiting script")
            return False
        elif path_photos==path_export:
            PhotoScan.app.messageBox("For safety, a separate folder should be selected for the input and export folder. Please try again")
        elif len(os.listdir(path_photos))<1:
            PhotoScan.app.messageBox("A folder wasn't selected for the input folder or the input folder had no photos. Exiting script")
            return False
        else:
            tmp=os.listdir(path_photos)
            if len(tmp)==1 and (("jpg" or "jpeg") in tmp[0].lower()):
                PhotoScan.app.messageBox("Only one photo was found. If there were more photos please restart and click the folder rather than a photo. Otherwise ignore this message.")
            break
    
    #processing parameters
    downscale, = 1 # Photo alignment accuracy - 1 is "high" not "highest"
    generic_preselection = True  
    keypoints = 40000 #align photos key point limit
    tiepoints = 10000 #align photos tie point limit
    threshold=0.5

    fold_list = os.listdir(path_photos)
    for folder in fold_list:
        #loading images
        folderPath = path_photos + "/" + folder
        image_list = os.listdir(folderPath)
        photo_list = list()
        for photo in image_list:
            if ("jpg" or "jpeg") in photo.lower():
                photo_list.append(os.path.join(folderPath,photo))
        doc = PhotoScan.Document()
        doc.save(path_export+"/"+folder+".psx")
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
        f = PhotoScan.PointCloud.Filter()
        f.init(chunk, criterion=PhotoScan.PointCloud.Filter.ReprojectionError)
        f.removePoints(threshold)
        doc.save()
    return True

if __name__=="__main__":
    PhotoScan.app.addMenuItem("Custom menu/Process 1", main)
    t0 = time.time()
    flag=main()
    t1 = time.time()
    if flag:
        PhotoScan.app.messageBox("Completed in "+str(int(t1-t0))+"seconds. Now define points & set scale bar distance before running optandbuild.py")
