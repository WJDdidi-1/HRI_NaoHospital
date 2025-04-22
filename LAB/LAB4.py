from naoqi import ALProxy
import time
import math


def initialize_robot(robotIP, PORT):
    # Create ALMotion and ALRobotPosture proxies.
    # Wake up the robot and set it to the StandInit posture with a slower speed.

    try:
        motion = ALProxy("ALMotion", robotIP, PORT)
        posture = ALProxy("ALRobotPosture", robotIP, PORT)
    except Exception as e:
        print("Error creating proxies:", e)
        exit(1)

    # Wake up the robot
    motion.wakeUp()
    # Set the robot to the initial StandInit posture with a slower speed (0.2)
    posture.goToPosture("StandInit", 0.2)
    return motion, posture


def compute_relative_transform(home, current):
    # Compute the relative displacement (dx, dy, dtheta) to move the robot

    # Global differences
    dx_global = home[0] - current[0]
    dy_global = home[1] - current[1]
    theta_current = current[2]

    # Transform the global differences into the robot's local coordinate frame
    dx_relative = math.cos(theta_current) * dx_global + math.sin(theta_current) * dy_global
    dy_relative = -math.sin(theta_current) * dx_global + math.cos(theta_current) * dy_global
    dtheta = home[2] - theta_current

    return dx_relative, dy_relative, dtheta


def main():
    # Change this to your robot's IP address and port
    robotIP = "192.168.1.35"
    PORT = 9559

    # Initialize the robot: create proxies, wake it up, and set it to the initial posture (with slower speed)
    motion, posture = initialize_robot(robotIP, PORT)

    # Use ALMotion.getRobotPosition to get the current robot pose as the home location
    home_location = motion.getRobotPosition(True)
    print("Home location set to:", home_location)

    # Command the robot to move forward a specified distance (e.g., 1 meter)
    forward_distance = 0.2  # in meters
    print("Moving forward {:.2f} meter(s) from home...".format(forward_distance))
    motion.moveTo(forward_distance, 0.0, 0.0)
    time.sleep(3)  # Wait for the movement to complete

    # Get the current pose after moving forward
    current_location = motion.getRobotPosition(True)
    print("Current location after moving forward:", current_location)

    # Compute the relative transform needed to return to the home position
    dx_rel, dy_rel, dtheta = compute_relative_transform(home_location, current_location)
    print("Relative transform to return home: dx: {:.2f}, dy: {:.2f}, dtheta: {:.2f}"
          .format(dx_rel, dy_rel, dtheta))

    # If the return movement involves moving backward (negative x direction), lower the robot's center of gravity
    if dx_rel < 0:
        print("Detected backward movement, lowering center of gravity by entering 'Crouch' posture for safety...")
        posture.goToPosture("Crouch", 0.5)
        time.sleep(1)

    # Command the robot to return to the home position
    print("Returning to home position...")
    motion.moveTo(dx_rel, dy_rel, dtheta)
    time.sleep(3)

    # If previously in a lowered posture, restore the StandInit posture with a slower speed after the movement
    if dx_rel < 0:
        print("Return movement complete, restoring 'StandInit' posture with slower speed...")
        posture.goToPosture("StandInit", 0.2)
        time.sleep(1)

    # Optionally, get the final pose for verification
    final_location = motion.getRobotPosition(True)
    print("Final location:", final_location)

    # Put the robot to rest
    motion.rest()


if __name__ == "__main__":
    main()