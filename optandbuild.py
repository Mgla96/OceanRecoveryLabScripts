import os
import PhotoScan
import math, time

'''
This script will be called after the user defines points and set scale bar distance. 
This script will optimize cameras, build dense cloud, then delete more points above a 0.5 reprojection error. 
Then it will continue to build mesh and add texture.
'''

def main():

    global doc
	doc = PhotoScan.app.document

	#chunk = doc.chunk
	path_photos = PhotoScan.app.getExistingDirectory("Specify INPUT photo folder(containing all alignanddelete metashape files):")
	#don't need path export will put back in same place
	#path_export = PhotoScan.app.getExistingDirectory("Specify EXPORT folder:")	
	surface = PhotoScan.SurfaceType.Arbitrary #build mesh surface type
	quality = PhotoScan.Quality.MediumQuality #build dense cloud quality
	filtering = PhotoScan.FilterMode.AggressiveFiltering #depth filtering
	interpolation = PhotoScan.Interpolation.EnabledInterpolation #build mesh interpolation
	face_num = PhotoScan.FaceCount.HighFaceCount #build mesh polygon count
	mapping = PhotoScan.MappingMode.GenericMapping #build texture mapping
	atlas_size = 8192
	blending = PhotoScan.BlendingMode.MosaicBlending #blending mode
	color_corr = False
	fold_list = os.listdir(path_photos)
	for folder in fold_list:	
		if ("psx" or "Psx") in folder.lower():
			print(folder)
			doc = PhotoScan.app.document
			doc.open("folder")
			chunk=doc.chunk
			#optimize cameras
			chunk.optimizeCameras()

			#building dense cloud
			chunk.buildDenseCloud()

			#Read reprojection Error and delete any 0.5 or greater
			f = PhotoScan.PointCloud.Filter()
			f.init(chunk, criterion=PhotoScan.PointCloud.Filter.ReprojectionError)
			f.removePoints(0.5)

			#building dense cloud
			chunk.buildDenseCloud(quality = quality, filter = filtering)
    	
			#building mesh
			chunk.buildModel(surface = surface, interpolation = interpolation, face_count = face_num)
		
			#build texture
			chunk.buildUV(mapping = mapping, count = 1)
			chunk.buildTexture(blending = blending , color_correction = color_corr, size = atlas_size)
			PhotoScan.app.update()
			#export
			chunk.exportModel(path_export + "\\model.obj", format = "obj", texture_format='jpg')
    		print("Now saving.")
			#saving docs
			doc.save()
		else:
			continue
PhotoScan.app.addMenuItem("Custom menu/Process 2", main)	
t0 = time.time()
main()
t1 = time.time()
PhotoScan.app.messageBox("Completed in "+ str(int(t1-t0))+"seconds.")

			