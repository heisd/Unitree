#!/bin/bash
# ROS 2 Launch Script for Unitree H1 SDK
# This script ensures a clean environment without conda interference

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to print usage
usage() {
    echo -e "${GREEN}Unitree H1 ROS 2 Launch Script${NC}"
    echo ""
    echo "Usage: ./ros2_launch.sh <command> [options]"
    echo ""
    echo "Commands:"
    echo "  gazebo          Launch Gazebo simulation with H1 robot"
    echo "  teleop          Launch keyboard teleoperation"
    echo "  control         Launch high-level control node"
    echo "  full            Launch Gazebo + control + teleop"
    echo "  topic <args>    Run ros2 topic command"
    echo "  node <args>     Run ros2 node command"
    echo "  run <pkg> <exe> Run a ROS 2 executable"
    echo "  build           Build the workspace"
    echo ""
    echo "Options for gazebo:"
    echo "  --no-rviz       Disable RViz"
    echo "  --no-gui        Disable Gazebo GUI"
    echo ""
    echo "Examples:"
    echo "  ./ros2_launch.sh gazebo"
    echo "  ./ros2_launch.sh teleop"
    echo "  ./ros2_launch.sh full"
    echo "  ./ros2_launch.sh topic list"
    echo "  ./ros2_launch.sh build"
}

# Function to run ROS 2 commands in clean environment
ros2_run() {
    env -i \
        HOME="$HOME" \
        PATH="/opt/ros/humble/bin:/usr/local/bin:/usr/bin:/bin" \
        DISPLAY="$DISPLAY" \
        XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}" \
        RMW_IMPLEMENTATION=rmw_fastrtps_cpp \
        XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" \
        bash -c "
            source /opt/ros/humble/setup.bash
            cd '$SCRIPT_DIR'
            if [ -f './install/setup.sh' ]; then
                source ./install/setup.sh
            fi
            $*
        "
}

# Main command handler
case "$1" in
    gazebo)
        shift
        RVIZ_ARG="rviz:=true"
        GUI_ARG="gui:=true"
        for arg in "$@"; do
            case "$arg" in
                --no-rviz) RVIZ_ARG="rviz:=false" ;;
                --no-gui) GUI_ARG="gui:=false" ;;
            esac
        done
        echo -e "${GREEN}Launching H1 Gazebo simulation...${NC}"
        ros2_run "ros2 launch h1_gazebo h1_gazebo.launch.py $RVIZ_ARG $GUI_ARG"
        ;;
    
    teleop)
        echo -e "${GREEN}Launching keyboard teleoperation...${NC}"
        ros2_run "ros2 run h1_control keyboard_teleop.py"
        ;;
    
    control)
        echo -e "${GREEN}Launching high-level control node...${NC}"
        ros2_run "ros2 run h1_control high_level_control.py"
        ;;
    
    full)
        echo -e "${GREEN}Launching full simulation with control...${NC}"
        ros2_run "ros2 launch h1_control simulation_control.launch.py"
        ;;
    
    topic)
        shift
        ros2_run "ros2 topic $*"
        ;;
    
    node)
        shift
        ros2_run "ros2 node $*"
        ;;
    
    run)
        shift
        ros2_run "ros2 run $*"
        ;;
    
    build)
        echo -e "${GREEN}Building workspace...${NC}"
        ros2_run "colcon build --symlink-install"
        ;;
    
    -h|--help|help)
        usage
        ;;
    
    *)
        if [ -z "$1" ]; then
            usage
        else
            # Pass through any other ros2 commands
            ros2_run "ros2 $*"
        fi
        ;;
esac
