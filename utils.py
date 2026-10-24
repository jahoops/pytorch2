# utils.py

import random
from constants import directions  # Import directions from constants.py

# Function to encode color as one-hot vector
def encode_color(color):
    color_map = {
        (255, 0, 0): [1, 0, 0, 0],    # Red
        (0, 255, 0): [0, 1, 0, 0],    # Green
        (0, 0, 255): [0, 0, 1, 0],    # Blue
        (255, 255, 0): [0, 0, 0, 1]   # Yellow
    }
    return color_map[color]

# Function to determine new direction based on action and collision entity
def determine_new_direction(action, collision_direction):
    if action == 8:  # Do not move
        return (0, 0)
    elif action == 0:  # Move toward the collision entity
        return collision_direction
    elif action == 1:  # Move to the left of the collision entity
        return (-collision_direction[1], collision_direction[0])
    elif action == 2:  # Move to the right of the collision entity
        return (collision_direction[1], -collision_direction[0])
    elif action == 3:  # Move directly away from the collision entity
        return (-collision_direction[0], -collision_direction[1])
    elif action == 4:  # Move diagonally toward the collision entity (up-left)
        return (-1, -1)
    elif action == 5:  # Move diagonally toward the collision entity (up-right)
        return (1, -1)
    elif action == 6:  # Move diagonally away from the collision entity (down-left)
        return (-1, 1)
    elif action == 7:  # Move diagonally away from the collision entity (down-right)
        return (1, 1)
    return random.choice(directions)  # Default to random direction if no valid action