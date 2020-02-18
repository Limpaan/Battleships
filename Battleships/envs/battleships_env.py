import numpy as np
import gym
from gym import error, spaces, utils
from gym.utils import seeding
from gym.envs.classic_control import rendering

# Untried squares are 0
# Misses are -1
# Hits are 1
# Sunk ships are 2

class BattleshipsEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self, grid_size=(10, 10), ship_sizes=(0, 5, 4, 3, 3, 2), seed=None):
        self.rng, self.seed = seeding.np_random(seed)
        self.action_space = spaces.MultiDiscrete([grid_size[0], grid_size[1]])
        self.observation_space = spaces.Box(-1, 2, [grid_size[0], grid_size[1]])
        self.state = None
        self.viewer = None

        self.ai_ship_grid = None
        self.opp_ship_grid = None
        self.ai_hit_grid = None
        self.opp_hit_grid = None
        self.ship_size = ship_sizes
        self.grid_size = grid_size

        # Rendering
        self.screen_dimensions = 800, 400
        min_dimension = min(self.screen_dimensions[0]/2, self.screen_dimensions[1])
        self.right_side_offset = self.screen_dimensions[0] / 2
        self.margin = min_dimension*0.05
        self.grid_length = (min_dimension - 2*self.margin)/(max(self.grid_size))
        self.grid_margin = self.grid_length * 0.15
        self.grid_line_width = 2
        self.horizontal_adjustment = self.grid_length * max(0, self.grid_size[0] - self.grid_size[1])
        self.vertical_adjustment = self.grid_length * max(0, self.grid_size[1] - self.grid_size[0])
        self.rendering_ai_hit = None
        self.rendering_opp_hit = None
        self.ship_color = (0.5, 0.5, 0.5)
        self.hit_colors = {-1: (0.2, 0.2, 1.0), 1: (0.7, 0.1, 0.1), 2: (0, 0, 0)}

    def step(self, action):
        assert self.action_space.contains(action), "{} ({}) invalid action".format(action, type(action))
        x, y = action
        if self.opp_ship_grid[x][y] <= 0:           # A miss
            reward = -1
            self.opp_hit_grid[x][y] = -1
        elif self.opp_hit_grid[x][y] >= 1:          # Hitting an already hit target
            reward = -1
        else:                                       # Otherwise a hit!
            reward = 0
            self.opp_hit_grid[x][y] = 1
            ship_hit = self.opp_ship_grid[x][y]
            ship_pos = np.argwhere(self.opp_ship_grid == ship_hit)
            sunk = True
            for pos in ship_pos:
                if self.opp_hit_grid[pos[0]][pos[1]] == 0:
                    sunk = False
                    break
            if sunk:
                for pos in ship_pos:
                    self.opp_hit_grid[pos[0]][pos[1]] = 2
        hits = np.count_nonzero(self.opp_hit_grid == 2)

        done = hits == sum(self.ship_size)
        self.state = self.opp_hit_grid

        return self.state, reward, done, {}

    def reset(self):
        self.ai_ship_grid = np.zeros((self.grid_size[0], self.grid_size[1]))
        self.opp_ship_grid = np.zeros((self.grid_size[0], self.grid_size[1]))

        self.ai_hit_grid = np.zeros((self.grid_size[0], self.grid_size[1]))
        self.opp_hit_grid = np.zeros((self.grid_size[0], self.grid_size[1]))

        self.place_ships_random(self.ai_ship_grid)
        self.place_ships_random(self.opp_ship_grid)

        self.state = self.opp_hit_grid

        self.rendering_ai_hit = np.zeros((self.grid_size[0], self.grid_size[1]))
        self.rendering_opp_hit = np.zeros((self.grid_size[0], self.grid_size[1]))

        return self.state

    def render(self, mode='human'):
        if self.viewer is None:
            self.viewer = rendering.Viewer(self.screen_dimensions[0], self.screen_dimensions[1])

            self.draw_grid(left=True)
            for i in range(1, len(self.ship_size)):
                self.draw_ship(i, left_side=True)
            self.draw_grid(left=False)
            for i in range(1, len(self.ship_size)):
                self.draw_ship(i, left_side=False)

        diff = self.opp_hit_grid - self.rendering_opp_hit
        diff_pos = np.argwhere(diff)
        for pos in diff_pos:
            val = self.opp_hit_grid[pos[0]][pos[1]]
            circle = rendering.make_circle(radius=(self.grid_length - self.grid_margin)/2, filled=True)
            circle.set_color(self.hit_colors[val][0], self.hit_colors[val][1], self.hit_colors[val][2])
            left, bottom = self.get_left_bottom_grid_cell_position(pos[0], pos[1], left_side=True)
            circle.add_attr(rendering.Transform(translation=(left + self.grid_length/2, bottom + self.grid_length/2)))
            self.viewer.add_geom(circle)
            self.rendering_opp_hit[pos[0]][pos[1]] = val

        return self.viewer.render(return_rgb_array=mode == 'rgb_array')

    def draw_ship(self, ship_index, left_side):
        if left_side:
            grid = self.opp_ship_grid
        else:
            grid = self.ai_ship_grid
        ship_coords = np.argwhere(grid == ship_index)
        x_min = min(ship_coords[:, 0])
        x_max = max(ship_coords[:, 0])
        y_min = min(ship_coords[:, 1])
        y_max = max(ship_coords[:, 1])
        left, bottom = self.get_left_bottom_grid_cell_position(x_min, y_min, left_side)
        right, top = self.get_left_bottom_grid_cell_position(x_max, y_max, left_side)
        bottom = bottom + self.grid_margin
        left = left + self.grid_margin
        top = top + self.grid_length - self.grid_margin
        right = right + self.grid_length - self.grid_margin
        ship = rendering.make_polygon([[left, bottom], [right, bottom], [right, top], [left, top]], filled=True)
        ship.set_color(self.ship_color[0], self.ship_color[1], self.ship_color[2])
        self.viewer.add_geom(ship)

    def draw_grid(self, left):
        x_min = self.get_left_bottom_grid_cell_position(0, 0, left_side=left)[0]
        x_max = self.get_left_bottom_grid_cell_position(self.grid_size[0], 0, left_side=left)[0]
        y_min = self.get_left_bottom_grid_cell_position(0, 0, left_side=left)[1]
        y_max = self.get_left_bottom_grid_cell_position(0, self.grid_size[1], left_side=left)[1]

        for i in range(self.grid_size[1] + 1):
            y_val = self.get_left_bottom_grid_cell_position(0, i, left)[1]
            horizontal_line = rendering.make_polyline(
                [[x_min, y_val], [x_max, y_val]]
            )
            horizontal_line.set_linewidth(self.grid_line_width)
            self.viewer.add_geom(horizontal_line)
        for i in range(self.grid_size[0] + 1):
            x_val = self.get_left_bottom_grid_cell_position(i, 0, left)[0]
            vertical_line = rendering.make_polyline(
                [[x_val, y_min], [x_val, y_max]]
            )
            vertical_line.set_linewidth(self.grid_line_width)
            self.viewer.add_geom(vertical_line)

    def get_left_bottom_grid_cell_position(self, x, y, left_side):
        if left_side:
            x_coord = self.margin + self.grid_length * x
            y_coord = self.margin + self.grid_length * y
            return x_coord, y_coord
        else:
            x_coord = self.screen_dimensions[0] - self.margin - (self.grid_size[0] + 1 - x) * self.grid_length
            y_coord = self.margin + self.grid_length * y
            return x_coord, y_coord

    def close(self):
        if self.viewer:
            self.viewer.close()
            self.viewer = None

    def place_ships_random(self, grid):
        # Skipping 0 so that 0 can be "empty water"
        for ship_id in range(1, len(self.ship_size)):
            if self.rng.random() < 0.5:
                x_cutoff = self.ship_size[ship_id]
                y_cutoff = 0
            else:
                x_cutoff = 0
                y_cutoff = self.ship_size[ship_id]
            # No way to block all possible placements, so it will find a solution eventually
            while True:
                x_pos = self.rng.randint(0, len(grid[:, 0]) - x_cutoff)
                y_pos = self.rng.randint(0, len(grid[0]) - y_cutoff)
                if self.place_ship_at(grid, ship_id, (x_pos, y_pos), (x_pos + x_cutoff, y_pos + y_cutoff)):
                    break

    def place_ship_at(self, grid, ship_id, bottom_left_pos, top_right_pos):
        # Check horizontal / vertical placement
        assert bottom_left_pos[0] == top_right_pos[0] or bottom_left_pos[1] == top_right_pos[1]
        for x in range(max(top_right_pos[0] - bottom_left_pos[0], 1)):
            for y in range(max(top_right_pos[1] - bottom_left_pos[1], 1)):
                if grid[bottom_left_pos[0] + x][bottom_left_pos[1] + y] != 0:
                    return False
        for x in range(max(top_right_pos[0] - bottom_left_pos[0], 1)):
            for y in range(max(top_right_pos[1] - bottom_left_pos[1], 1)):
                grid[bottom_left_pos[0] + x][bottom_left_pos[1] + y] = ship_id
        return True