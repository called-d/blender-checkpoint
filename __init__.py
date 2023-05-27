import importlib
import sys
import os

bl_info = {
    "name": "Checkpoint - Supercharged",
    "author": "Flowerboy Studio",
    "description": "Backup and version control for Blender",
    "blender": (2, 80, 0),
    "category": "Development",
    "version": (0, 1, 0),
    "location": "Properties > Active Tool and Workspace settings > Checkpoints Panel",
}


# Local imports implemented to support Blender refreshes
"""ORDER MATTERS"""
modulesNames = ("app_helpers", "project_helpers", "object_helpers",
                "project_ops", "object_ops",
                "project_ui", "object_ui",
                "app_preferences", "app_handlers")
for module in modulesNames:
    if module in sys.modules:
        importlib.reload(sys.modules[module])
    else:
        globals()[module] = importlib.import_module(f"{__name__}.{module}")

if app_helpers.HAS_CHECKPOINT_KEY:
    with open(app_helpers.CHECKPOINT_KEY_FILE_PATH, "r") as f:
        # Create a dictionary from the lines in the file
        env_vars = dict(line.strip().split("=") for line in f)
        license_key = env_vars["LICENSE_KEY"]

    error = app_helpers.check_license_key(license_key)

    if error:
        os.remove(app_helpers.CHECKPOINT_KEY_FILE_PATH)
        app_helpers.HAS_CHECKPOINT_KEY = False


def register():
    for moduleName in modulesNames:
        if hasattr(globals()[moduleName], "register"):
            globals()[moduleName].register()


def unregister():
    for module in modulesNames:
        if hasattr(globals()[module], "unregister"):
            globals()[module].unregister()
