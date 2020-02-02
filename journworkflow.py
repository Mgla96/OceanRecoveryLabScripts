import os
import PhotoScan


def main():

	global doc
	doc = PhotoScan.app.document

	app = QtGui.QApplication.instance()
	parent = app.activeWindow()
	
	#prompting for path to photos
	path_photos = PhotoScan.app.getExistingDirectory("Specify input photo folder:")
	path_export = PhotoScan.app.getExistingDirectory("Specify EXPORT folder:")
	
	#processing parameters
	accuracy = PhotoScan.Accuracy.HighAccuracy  #align photos accuracy
	preselection = PhotoScan.Preselection.GenericPreselection
	keypoints = 40000 #align photos key point limit
	tiepoints = 10000 #align photos tie point limit
	source = PhotoScan.PointsSource.DensePoints #build mesh source
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
	doc.addChunk()
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
	
	chunk.optimizeCameras()

	#building dense cloud
	PhotoScan.app.gpu_mask = 1  #GPU devices binary mask
	PhotoScan.app.cpu_cores_inactive = 2  #CPU cores inactive
	chunk.buildDenseCloud(quality = quality, filter = filtering)


    #Read reprojection Error and delete any 0.5 or greater
    

	#building mesh
	chunk.buildModel(surface = surface, source = source, interpolation = interpolation, face_count = face_num)

  


	#build texture
	chunk.buildUV(mapping = mapping, count = 1)
	chunk.buildTexture(blending = blending , color_correction = color_corr, size = atlas_size)

	PhotoScan.app.update()

	#export
	
	chunk.exportModel(path_export + "\\model.obj", format = "obj", texture_format='jpg')

	print("Script finished")


PhotoScan.app.addMenuItem("Custom menu/Process 1", main)	

main()
print(":)")