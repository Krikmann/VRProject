Terrace level setup script
==========================

SetupTerraceLevel.py adds default lighting, fog, a scaled SM_Cube floor, and
PlayerStart to Content/VRTemplate/Maps/Terrace. It also removes duplicate
DirectionalLight / SkyLight actors and fixes exposure (white viewport fix).
Meshes such as rocks from LightingAndMainRocks are left untouched.

Requirements
------------
- Python Editor Script Plugin (enabled in DrownedCityVR.uproject)
- Editor Scripting Utilities
- Restart the editor after enabling plugins

Run once
--------
1. Open the DrownedCityVR project.
2. File -> Execute Python Script
3. Select Content/Python/SetupTerraceLevel.py

To run against whichever map is already open, set USE_OPEN_LEVEL = True at
the top of the script.

Re-runs
-------
With SKIP_DUPLICATES = True, actors that are already present are left alone.

Troubleshooting
---------------
- "No module named unreal" -> enable the Python plugin and restart.
- "Mesh not found" -> confirm SM_Cube exists under LevelPrototyping/Meshes.
- Black viewport -> switch the view mode to Lit.

Command line (optional)
-----------------------
UnrealEditor DrownedCityVR.uproject -ExecutePythonScript=".../SetupTerraceLevel.py" -unattended -nullrhi
