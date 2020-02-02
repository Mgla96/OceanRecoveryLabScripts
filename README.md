# OceanRecoveryLabScripts

<p align="center">
<img src="https://media.giphy.com/media/xT9DPxv8oh2UCSZFYs/giphy.gif" width="50%" alt="gif">
</p>

## Script 1
Script 1 will take a folder and loop through it's subfolders which consists of photos to add to each individual chunk. This script will align photos and delete points outside bounding box as well as delete points that are above a 0.5 reprojection error for each subfolder of photos. Then this script will export these updated files to the user's designated location. 

## Script 2
Script 2 will be called after the user defines points and set scale bar distance. This script will optimize cameras, build dense cloud, then delete more points above a 0.5 reprojection error. Then it will continue 
to build mesh and add texture.


