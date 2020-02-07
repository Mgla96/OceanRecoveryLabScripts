import os
import PhotoScan
'''
from PySide2 import QtGui, QtCore, QtWidgets
'''

from PySide2.QtCore import *
from PySide2.QtGui import *
'''
from PyQt5 import QtGui, QtCore, QtWidgets
'''
#Metashape.Application object has no attribute 'cpu_cores_inactive'
'''
This script will take a folder and loop through it's subfolders which consists of photos to add to each individual chunk. 
This script will align photos and delete points outside bounding box as well as delete points that are above a 0.5 reprojection error for each subfolder of photos. 
Then this script will export these updated files to the user's designated location.
'''
def main():

	global doc
	doc = PhotoScan.app.document
	##app = QtGui.Qapplication.instance()
	##parent = app.activeWindow()
	
	#prompting for path to photos
	path_photos = PhotoScan.app.getExistingDirectory("Specify input photo folder:")
	path_export = PhotoScan.app.getExistingDirectory("Specify EXPORT folder:")
	doc.save(path_export+"\\"+"project.psx")
	#processing parameters
	accuracy = PhotoScan.Accuracy.HighAccuracy  #align photos accuracy
	preselection = PhotoScan.Preselection.GenericPreselection
	keypoints = 40000 #align photos key point limit
	tiepoints = 10000 #align photos tie point limit
	#source = PhotoScan.PointsSource.DensePoints #build mesh source
	surface = PhotoScan.SurfaceType.Arbitrary #build mesh surface type
	quality = PhotoScan.Quality.MediumQuality #build dense cloud quality
	filtering = PhotoScan.FilterMode.AggressiveFiltering #depth filtering
	interpolation = PhotoScan.Interpolation.EnabledInterpolation #build mesh interpolation
	face_num = PhotoScan.FaceCount.HighFaceCount #build mesh polygon count
	mapping = PhotoScan.MappingMode.GenericMapping #build texture mapping
	atlas_size = 8192
	blending = PhotoScan.BlendingMode.MosaicBlending #blending mode
	color_corr = False
	threshold=0.5

	print("Script started")
	#creating new chunk
	#doc.addChunk()
	chunk = doc.chunks[-1]
	chunk.label = "New Chunk"

	#loading images
	image_list = os.listdir(path_photos)
	photo_list = list()
	for photo in image_list:
		if ("jpg" or "jpeg" or "JPG" or "JPEG") in photo.lower():
			photo_list.append(path_photos + "\\" + photo)
	chunk.addPhotos(photo_list)

	#align photos
	chunk.matchPhotos(accuracy = accuracy, preselection = preselection, filter_mask = False, keypoint_limit = keypoints, tiepoint_limit = tiepoints)
	chunk.alignCameras()

    #Removing points outside bounding box
	for i in range(len(doc.chunks)):
		chunk = doc.chunks[i]
		R = chunk.region.rot		#Bounding box rotation matrix
		C = chunk.region.center		#Bounding box center vertor
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
	print("Points outside the region were removed.")
	
	#Read reprojection error and delete any 0.5 or greater


	#PhotoScan.app.addMenuItem("Custom menu/Filter point cloud by bounding box", main)	
	#might be 2nd script below here after user defines points and set scale bar distance
	doc.save()

PhotoScan.app.addMenuItem("Custom menu/Process 1", main)	

main()
print("Complete")
