# Ocean Recovery Lab Scripts
Metashape Scripts to assist researchers at the Ocean Recoveries Lab at UC Santa Barbara. <br>
**Note this is still a work in progress**
## alignandelete.py
**STEP 1** <br>
alignanddelete will take a folder and loop through it's subfolders which consists of photos to add to each individual chunk. This script will align photos and delete points outside bounding box as well as delete points that are above a 0.5 reprojection error for each subfolder of photos. Then this script will export these updated files to the user's designated location. 

## optandbuild.py
**STEP 2** <br>
optandbuild will be called after the user defines points and set scale bar distance. This script will optimize cameras, build dense cloud, then delete more points above a 0.5 reprojection error. Then it will continue 
to build mesh and add texture.

