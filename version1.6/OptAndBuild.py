import os
import Metashape as meta
#import photoscan
import math, time
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
	path_photos,path_export="",""
	while True:
		meta.app.messageBox("Specify Input Photo Folder(containing all alignanddelete metashape files):")
		path_photos = meta.app.getExistingDirectory("Specify Input Photo Folder(containing all alignanddelete metashape files):")
		meta.app.messageBox("Specify EXPORT folder")
		path_export = meta.app.getExistingDirectory("Specify EXPORT folder:")
		if path_photos=="" or path_export=="":
			meta.app.messageBox("input or export folder wasn't selected. Exiting script")
			return "",""
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
	surface = meta.SurfaceType.Arbitrary #build mesh surface type
	downscale = 2 # Photo alignment accuracy - 2 is "high quality" (want high quality not ultra high quality)
	filtering = meta.FilterMode.MildFiltering #depth filtering
	interpolation = meta.Interpolation.EnabledInterpolation #build mesh interpolation
	face_num = meta.FaceCount.HighFaceCount #build mesh polygon count
	mapping = meta.MappingMode.GenericMapping #build texture mapping
	atlas_size = 8192
	blending = meta.BlendingMode.MosaicBlending #blending mode
	volumetric_masks = True
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	
	#get input and output folders
	path_photos,path_export=promptPath()
	if path_photos=="" or path_export=="":
		return False
	
	fold_list = os.listdir(path_photos)
	for folder in fold_list:
		#print(folder)	
		if "psx" in folder.lower():
			doc = meta.app.document
			doc.open(path_photos+divider+folder) 
			chunk=doc.chunk
			#optimize cameras
			chunk.optimizeCameras()
			R = chunk.region.rot		#Bounding box rotation matrix
			C = chunk.region.center		#Bounding box center vector
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
			#Read reprojection Error and delete any 0.5 or greater
			f = meta.PointCloud.Filter()
			f.init(chunk, criterion=meta.PointCloud.Filter.ReprojectionError)
			f.removePoints(0.5)
			#building dense cloud
			chunk.buildDepthMaps(downscale = downscale, filter_mode = filtering)
			chunk.buildDenseCloud(point_colors = True)
			#building mesh
			chunk.buildModel(surface_type = surface, interpolation = interpolation, face_count = face_num, volumetric_masks=volumetric_masks)
			#build texture
			chunk.buildUV(mapping_mode = mapping, page_count = 1)
			chunk.buildTexture(blending_mode = blending , texture_size = atlas_size)
			meta.app.update()
			doc.save(path_export+divider+folder+".psx")
		else:
			continue

if __name__=="__main__":
	meta.app.addMenuItem("Custom menu/Process 2", main)
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
			meta.app.messageBox("Completed in "+ str(int(t1-t0))+"seconds.")

			