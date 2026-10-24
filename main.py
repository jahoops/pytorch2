import debugpy
import pygame
import random
import numpy as np
import torch
import torch.nn as nn
from entity import Entity
from model import EntityModel
from utils import encode_color, determine_new_direction
from constants import directions  # Import directions from constants.py

# Allow other computers to attach to debugpy at this IP address and port.
debugpy.listen(("0.0.0.0", 5678))

# Pause the program until a remote debugger is attached
print("Waiting for debugger attach...")
debugpy.wait_for_client()
print("Debugger attached")

# Constants
SCREEN_WIDTH = 350
SCREEN_HEIGHT = 200
BOARD_WIDTH = 70
BOARD_HEIGHT = 40
center_x, center_y = BOARD_WIDTH // 2, BOARD_HEIGHT // 2

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((500, 200))  # Add 400 to the width for reward data
clock = pygame.time.Clock()
pygame.font.init()  # Initialize the font module
font = pygame.font.SysFont(None, 24)  # Use Pygame's font module

# Define team colors
team_colors = [
    (255, 0, 0),    # Red
    (0, 255, 0),    # Green
    (128, 128, 255),    # Blue
    (255, 255, 0)   # Yellow
]
class Team:
    def __init__(self, color):
        self.id = None
        self.color = color
        self.model = None
        self.optimizer = None

# Create teams
teams = [Team(color) for color in team_colors]
for idx, team in enumerate(teams):
    team.id = idx
learning_rate = 0.001
input_size = 52
hidden_size = 64
output_size = 9
for team in teams:
    team.model = EntityModel(input_size, hidden_size, output_size)
    team.optimizer = torch.optim.Adam(team.model.parameters(), lr=learning_rate)

entities = []
# Create entities and assign teams
num_entities_per_team = 25
# Create a list of models, one per team
for team in teams:
    entity_id = 0
    for _ in range(num_entities_per_team):
        x, y = random.randint(0, BOARD_WIDTH - 1), random.randint(0, BOARD_HEIGHT - 1)
        while (x, y) == (center_x, center_y):
            x, y = random.randint(0, BOARD_WIDTH - 1), random.randint(0, BOARD_HEIGHT - 1)
        entity = Entity(entity_id, x, y, random.randint(0, 8), team.id)
        entity.input_data = np.zeros(input_size)
        entities.append(entity)
        entity_id += 1

# Initialize the board
board = np.zeros((BOARD_WIDTH, BOARD_HEIGHT), dtype=object)

def draw_walls():
    for x, y in wall_positions:
        pygame.draw.rect(screen, (255, 255, 255), (x * 5, y * 5, 10, 10))

for entity in entities:
    board[entity.x, entity.y] = entity

    # Define the positions for the walls
    wall_positions = [
        (center_x, center_y),  # Center
        (center_x // 2, center_y // 2),  # Top-left quadrant
        (center_x + center_x // 2, center_y // 2),  # Top-right quadrant
        (center_x // 2, center_y + center_y // 2),  # Bottom-left quadrant
        (center_x + center_x // 2, center_y + center_y // 2)  # Bottom-right quadrant
    ]

    # Place walls on the board
    for x, y in wall_positions:
        board[x, y] = 'wall'

# Training loop
print("Starting training loop...")
epoch = 0
epsilon = 0.20  # initial epsilon value

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

    # Initialize reward tracking
    reward_tracking = {index: {'total_reward': 0, 'count': 0} for index in range(len(team_colors))}

    screen.fill((0, 0, 0))

    # Shuffle entities to pick a random starting point
    random.shuffle(entities)
    #spy_entity = 52
    wall_penalties = 0

    for entity in entities:
        teamid = entity.team;
        # Move entity in the stored direction if possible
        new_x = entity.x + directions[entity.direction][0]
        new_y = entity.y + directions[entity.direction][1]

        # Check if the new position is out of bounds
        def inbounds(x, y, width, height):
            return 0 <= x < width and 0 <= y < height
        if inbounds(new_x, new_y, BOARD_WIDTH, BOARD_HEIGHT):
            if board[new_x, new_y] == 0:
                board[new_x, new_y] = entity
                board[entity.x, entity.y] = 0  # Empty the current square
                entity.set_position(new_x, new_y)
            else:
                if isinstance(board[new_x, new_y], Entity):
                    # Check if the entity occupying the square can be pushed
                    push_x = new_x + directions[entity.direction][0]
                    push_y = new_y + directions[entity.direction][1]
                    if inbounds(push_x, push_y, BOARD_WIDTH, BOARD_HEIGHT) and board[push_x, push_y] == 0:
                        # Recursively push the occupying entity
                        def recursive_push(entity, direction):
                            new_x = entity.x + directions[direction][0]
                            new_y = entity.y + directions[direction][1]
                            if inbounds(new_x, new_y, BOARD_WIDTH, BOARD_HEIGHT):
                                if board[new_x, new_y] == 0:
                                    board[new_x, new_y] = entity
                                    board[entity.x, entity.y] = 0
                                    entity.set_position(new_x, new_y)
                                    return True
                                elif board[new_x, new_y] != 'wall':
                                    occupying_entity = board[new_x, new_y]
                                    if recursive_push(occupying_entity, direction):
                                        board[new_x, new_y] = entity
                                        board[entity.x, entity.y] = 0
                                        entity.set_position(new_x, new_y)
                                        return True
                            return False

                        occupying_entity = board[new_x, new_y]
                        if recursive_push(occupying_entity, entity.direction):
                            board[new_x, new_y] = entity
                            board[entity.x, entity.y] = 0
                            entity.set_position(new_x, new_y)

        positive_reward = 0
        negative_reward = 0
        input_index = 0
        entity.input_data = np.zeros(52)

        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue  # Skip the center square
                for look3 in range(3):
                    neighbor_x = entity.x + dx * look3
                    neighbor_y = entity.y + dy * look3
                    # Ensure the neighbor is within the bounds of the grid
                    if inbounds(neighbor_x, neighbor_y, BOARD_WIDTH, BOARD_HEIGHT):
                        neighbor = board[neighbor_x, neighbor_y]
                        
                        if isinstance(neighbor, Entity):
                            if neighbor.team == teamid:
                                entity.input_data[input_index * 4 + 0] += .3  # Set the neighbor color to 1
                                positive_reward += 0.3  # Same color
                            else:
                                entity.input_data[input_index * 4 + 1] += .3
                                negative_reward += 0.2  # Different color
                        else:
                            if neighbor == 'wall':  # wall
                                entity.input_data[input_index * 4 + 2] += .3
                                positive_reward += 100.0
                            else:
                                entity.input_data[input_index * 4 + 3] += .3
                                positive_reward += 0.1
                    else:
                        negative_reward += 100.0  # Out of bounds treated as different color
                        entity.input_data[input_index * 4 + 4] += .3
                input_index += 1

        # Normalize reward
        reward = (positive_reward - negative_reward)
        entity.input_data[40] = entity.x / BOARD_WIDTH
        entity.input_data[41] = entity.y / BOARD_HEIGHT
        # Set the last 10 input data entries to indicate the entity ID
        entity_id_index = entity.id % 10
        entity.input_data[42 + entity_id_index] = 1
        # Track rewards
        reward_tracking[teamid]['total_reward'] += reward
        reward_tracking[teamid]['count'] += 1
        entity.set_reward(reward)

    for entity in entities:
        # Use the reward to update the model
        # reward = reward_tracking[entity.team]['total_reward'] /  reward_tracking[entity.team]['count']
        # Prepare the input data for the model
        teamid = entity.team;
        data = torch.tensor(entity.input_data, dtype=torch.float32)
        output = teams[teamid].model(data)
        target = torch.tensor(entity.reward, dtype=torch.float32)
        loss = nn.MSELoss()(output[entity.direction], target)
        teams[teamid].optimizer.zero_grad()
        loss.backward()
        teams[teamid].optimizer.step()
                
        # Epsilon-greedy action selection
        if random.random() < epsilon:
            action_index = random.randint(0, 8)  # Explore: choose a random action
        else:
            action_index = torch.argmax(output).item()  # Exploit: choose the best action

        # Ensure action_index is within the valid range
        action_index = min(max(action_index, 0), 8)

        # Determine the new direction based on the action
        new_direction = action_index  # Move in the chosen direction

        # Set the new direction for the next epoch
        entity.set_direction(new_direction)
        #if entity.id == spy_entity:
        #    print(f"{entity.x},{entity.y} Reward: {reward}, Input Data: {input_data}, Output: {output},  direction: {new_direction}")



    # Draw entities with team colors after each epoch
    screen.fill((0, 0, 0))
    # Decay epsilon over time
    epsilon = max(0.01, epsilon * 0.999)
    for entity in entities:
        pygame.draw.circle(screen, team_colors[entity.team], (entity.x * 5, entity.y * 5), 5)  # Scale position to 800x600 and draw 5x5 pixel circle
            # Draw walls
    draw_walls()
    # Display the current epoch and average rewards in the top right corner
    epoch_text = font.render(f"Epoch: {epoch}", True, (255, 255, 255))
    epsilon_text = font.render(f"Epsilon: {epsilon:.2f}", True, (255, 255, 255))
    screen.blit(epoch_text, (screen.get_width() - epoch_text.get_width() - 10, 10))
    screen.blit(epsilon_text, (screen.get_width() - epsilon_text.get_width() - 10, 30))
    y_offset = 50
    
    for team, data in reward_tracking.items():
        if data['count'] > 0:
            avg_reward = data['total_reward'] / data['count']
        else:
            avg_reward = 0
        reward_text = font.render(f"Reward: {avg_reward:.2f}", True, team_colors[team])
        screen.blit(reward_text, (screen.get_width() - reward_text.get_width() - 10, y_offset))
        y_offset += 20

    pygame.display.flip()
    clock.tick(60)
    epoch += 1

print("Training loop finished.")