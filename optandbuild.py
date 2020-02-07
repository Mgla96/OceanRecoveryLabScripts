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
	path_export = PhotoScan.app.getExistingDirectory("Specify EXPORT folder:")	
	
	fold_list = os.listdir(path_photos)
	for folder in fold_list:	
		doc.save(path_export+"\\"+folder+".psx")
		chunk.optimizeCameras()
		#building dense cloud
		PhotoScan.app.gpu_mask = 1  #GPU devices binary mask
		PhotoScan.app.cpu_cores_inactive = 2  #CPU cores inactive
		chunk.buildDenseCloud(quality = quality, filter = filtering)
    	#Read reprojection Error and delete any 0.5 or greater
		f = PhotoScan.PointCloud.Filter()
		f.init(chunk, criterion=PhotoScan.PointCloud.Filter.ReprojectionError)
		f.removePoints(0.5)
			
		#building mesh
		chunk.buildModel(surface = surface, interpolation = interpolation, face_count = face_num)
		#source = source,
		#build texture
		chunk.buildUV(mapping = mapping, count = 1)
		chunk.buildTexture(blending = blending , color_correction = color_corr, size = atlas_size)
		PhotoScan.app.update()
		#export
		chunk.exportModel(path_export + "\\model.obj", format = "obj", texture_format='jpg')
    	print("Script finished. Now saving.")
    	try: 
			doc.save()
		except RuntimeError:
			 PhotoScan.app.messageBox("Can't save project :()")

PhotoScan.app.addMenuItem("Custom menu/Process 2", main)	
main()
t1 = time.time()
PhotoScan.app.messageBox("Completed in "+ str(int(t1-t0))+"seconds.")