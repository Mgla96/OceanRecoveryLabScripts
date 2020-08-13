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
    path_photos = PhotoScan.app.getExistingDirectory("Specify INPUT photo folder(containing all metashape files):")
    path_export = PhotoScan.app.getExistingDirectory("Specify EXPORT folder:")
    #processing parameters
    accuracy = PhotoScan.Accuracy.HighAccuracy  #align photos accuracy
    preselection = PhotoScan.Preselection.GenericPreselection
    keypoints = 40000 #align photos key point limit
    tiepoints = 10000 #align photos tie point limit
    threshold=0.5
    fold_list = os.listdir(path_photos)
    for folder in fold_list:
        #print("folder name is : "+folder)
#loading images
        folderPath = path_photos + "/" + folder
        image_list = os.listdir(folderPath)
        photo_list = list()
        for photo in image_list:
            if ("jpg" or "jpeg" or "JPG" or "JPEG") in photo.lower():
                photo_list.append(os.path.join(folderPath,photo))
        doc = PhotoScan.Document()
        doc.save(path_export+"/"+folder+".psx")
        chunk=doc.addChunk() 
        chunk.addPhotos(photo_list)
        #align photos
        chunk.matchPhotos(accuracy = accuracy, preselection = preselection, filter_mask = False, keypoint_limit = keypoints, tiepoint_limit = tiepoints)
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
    #Points outside the region were removed.
    #Read reprojection error and delete any 0.5 or greater
        f = PhotoScan.PointCloud.Filter()
        f.init(chunk, criterion=PhotoScan.PointCloud.Filter.ReprojectionError)
        f.removePoints(threshold)
        doc.save()
PhotoScan.app.addMenuItem("Custom menu/Process 1", main)
t0 = time.time()
main()
t1 = time.time()
PhotoScan.app.messageBox("Completed in "+str(int(t1-t0))+"seconds. Now define points & set scale bar distance before running optandbuild.py")
