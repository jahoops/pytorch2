import random

class Entity:
    def __init__(self, id, x, y, direction, team):
        self.id = id
        self.x = x
        self.y = y
        self.direction = direction
        self.team = team
        self.input_data = None
        self.reward = 0

    def set_position(self, x, y):
        self.x = x
        self.y = y

    def set_direction(self, direction):
        self.direction = direction

    def set_reward(self, reward):
        self.reward = reward
