# Ocean Recovery Lab Scripts
Metashape Scripts to assist researchers at the Ocean Recoveries Lab at UC Santa Barbara. <br>


<p align="center">
<img src="https://media.giphy.com/media/TH0SVl4SWwyFEcoRhp/giphy.gif" width="50%" alt="gif">
</p>


## alignandelete.py
**STEP 1** <br>
alignanddelete will take a folder directory and loop through it's subfolders of separate coral treatments which consists of overlapping photos. This script will create a new chunk add and align photos, create tie points, estimate camera locations and delete all tie points outside bounding box. Then it will also delete pixels above a 0.5 reprojection error. Then this script will export these updated files to the user's designated location. 

### Instructions 
* Select folder consisting of all the coral treatments
* Select folder where you would like to place all the updated coral treatments

## optandbuild.py
**STEP 2** <br>
optandbuild will be called after the user defines points and set scale bar distance. This script will optimize cameras, delete other points outside bounding box, build dense cloud, then delete more pixels above a 0.5 reprojection error. Then it will repeat this process for all coral treatments.

### Instructions
* Select folder consisting of updated coral treatments that was made from alignanddelete.py

