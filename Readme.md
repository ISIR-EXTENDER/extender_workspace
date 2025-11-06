# Extender Workspace 

This is the main workspace for the extender project. 

## How to install ? 

First clone this repo in the `src` directory of your ros2 workspace
```
git clone https://gitlab.isir.upmc.fr/extender/extender_workspace.git
```
For now all sub repos are private, so you need to setup git credential helper to clone everything. This wya you only need to enter your credentials on the first repo cloning.
```
git config --local credential.helper
git config --local credential.helper 'cache --timeout=3600'
```

Then use vcs to clone all the subdirectories of the extender project. 
```
cd extender_workspace
vcs import --input extender.repos --workers 1
```

Afterwards, it is important to compile first the robot_interfaces package, which allows all controllers to be used on any robots of the project.
```
colcon build --symlink-install --packages-up-to robot_interfaces
source install/setup.zsh # or bash if you are using bash
```

Then controllers and control interfaces can be compiled
```
colcon build
```
