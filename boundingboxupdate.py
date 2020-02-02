import PhotoScan
def main():
	doc = PhotoScan.app.document
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

	print("Script finished. Points outside the region were removed.")
	
PhotoScan.app.addMenuItem("Custom menu/Filter point cloud by bounding box", main)	

main()