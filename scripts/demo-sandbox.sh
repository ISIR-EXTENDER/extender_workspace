# Default values
USE_SIM="false"
ROBOT="explorer"

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -s|--sim) USE_SIM="true"; shift ;;
        -r|--robot) ROBOT="$2"; shift 2 ;;
        -h|--help) 
            echo "Usage: $0 [options]"
            echo "  -s, --sim       Enable simulation (default: false)"
            echo "  -r, --robot     Select robot: 'explorer' or 'kinova' (default: explorer)"
            exit 0 ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
done

# clean up ros 
ros2 daemon stop
pkill -f ros2
pkill -f fastdds
rm -f /dev/shm/fastrtps_port*
rm -f /dev/shm/fastrtps_*
ros2 daemon start

# Tablet Backend
echo "Starting Tablet Backend in background..."
(
    source .venv/bin/activate
    cd src/input_interfaces/tablet_interface
    uv run python -m tablet_interface.main --ros-args --params-file config/tablet_interface_parameters_explorer.yaml
) > /tmp/tablet_backend.log 2>&1 &

echo "Starting Tablet Frontend in background..."
(
    cd src/extender_ui
    # Note: Using && ensures install finishes before dev starts
    npm install && npm run dev
) > /tmp/tablet_frontend.log 2>&1 &

# echo "Waiting for background processes to initialize..."
# sleep 1

echo "Launching Robot (Foreground)..."
# source install/setup.zsh
if [ "$ROBOT" = "explorer" ]; then
    ros2 launch sandbox_controller explorer.launch.py use_simulation:="$USE_SIM"
elif [ "$ROBOT" = "kinova" ]; then
    # Added example of robot-specific launch parameters
    ros2 launch sandbox_controller kinova.launch.py \
        use_simulation:="$USE_SIM" \
        robot_ip:=192.168.1.10
else
    echo "Error: Unknown robot type '$ROBOT'"
    exit 1
fi
