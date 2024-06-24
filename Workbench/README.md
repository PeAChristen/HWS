### HWS: A FreeCAD Workbench

This is a FreeCAD workbench to create and simulate toolpaths('wirepaths') for the grbl-mega-5x machine.
At the moment the workbench is in heavy development and its functionality may be broken from time to time.

**Current Features:\***
  - Parametric machine
  - Shape to wirepath algorithm
  - Links between wirepaths
  - Save G-Code file *.nc
  - Generate block cutting G-Code file *.nc
  - Wirepath animation

  *functionalities are not complete and need more testing.

### Command line installation in Ubuntu/Mint/similar:
  Open one terminal window (usually **ctrl+alt+t** ) and copy-paste line by line:
  
  Install git:
  **sudo apt-get install git**
  
  Clone repository:
  **git clone https://github.com/PeAChristen/HWS**
  
  Move content of workbench folder to /.FreeCAD/Mod/HWS:
  
  **mkdir ~/.FreeCAD/Mod/HWS**

  **mv ~/HWS/Workbench/\* ~/.FreeCAD/Mod/HWS/**


### Windows/Manual install (available to all users)
  Download the repository (https://github.com/PeAChristen/HWS) as ZIP file and extract the folder 'Workbench' 
  inside **C:\Program Files\FreeCAD\Mod** for Windows or **/usr/lib/FreeCAD/Mod** for Debian-like systems.


