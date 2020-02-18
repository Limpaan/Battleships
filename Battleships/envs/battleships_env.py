import numpy as np
import gym
from gym import error, spaces, utils
from gym.utils import seeding

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

        self.player_ai_grid = None
        self.player_opp_grid = None
        self.ship_size = ship_sizes
        self.grid_size = grid_size

    def step(self, action):
        assert self.action_space.contains(action), "{} ({}) invalid action".format(action, type(action))
        x, y = action
        if self.player_opp_grid[x][y][0] <= 0:
            reward = -1
            self.player_opp_grid[x][y][1] = -1
        else:
            reward = 0
            self.player_opp_grid[x][y][1] = 1
        self.mark_sunk_ships(self.player_opp_grid)
        hits = np.count_nonzero(self.player_opp_grid[:, :, 1] == 2)

        done = hits == sum(self.ship_size)
        self.state = self.player_opp_grid[:, :, 1]

        return self.state, reward, done, {}

    def reset(self):
        # Index 0 is ships, Index 1 is hits
        self.player_ai_grid = np.zeros((self.grid_size[0], self.grid_size[1], 2))
        self.player_opp_grid = np.zeros((self.grid_size[0], self.grid_size[1], 2))
        self.place_ships_random(self.player_ai_grid)
        self.place_ships_random(self.player_opp_grid)
        self.state = self.player_opp_grid[:, :, 1]
        return self.state

    def render(self, mode='human'):
        screen_width = 800
        screen_height = 400

        min_dimension = min(screen_width/2, screen_height)*
        grid_size = min_dimension*0.9/max(self.grid_size)
        right_side_origin = screen_width / 2
        margins = min_dimension*0.05

        while True:
            if self.viewer is None:
                from gym.envs.classic_control import rendering
                self.viewer = rendering.Viewer(screen_width, screen_height)

                for 

                grid = rendering.make_polyline([[0, 0], [100, 100]])
                grid.set_linewidth(10)
                self.viewer.add_geom(grid)
                self.viewer.render(return_rgb_array=mode == 'rgb_array')

        return self.viewer.render(return_rgb_array=mode == 'rgb_array')

    def close(self):
        ...

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
                x_pos = self.rng.randint(0, len(grid) - x_cutoff)
                y_pos = self.rng.randint(0, len(grid) - y_cutoff)
                if self.place_ship_at(grid, ship_id, (x_pos, y_pos), (x_pos + x_cutoff, y_pos + y_cutoff)):
                    break

    def place_ship_at(self, grid, ship_id, top_left_pos, bottom_right_pos):
        # Check horizontal / vertical placement
        assert top_left_pos[0] == bottom_right_pos[0] or top_left_pos[1] == bottom_right_pos[1]
        for x in range(max(bottom_right_pos[0] - top_left_pos[0], 1)):
            for y in range(max(bottom_right_pos[1] - top_left_pos[1], 1)):
                if grid[top_left_pos[0] + x][top_left_pos[1] + y][0] != 0:
                    return False
        for x in range(max(bottom_right_pos[0] - top_left_pos[0], 1)):
            for y in range(max(bottom_right_pos[1] - top_left_pos[1], 1)):
                grid[top_left_pos[0] + x][top_left_pos[1] + y][0] = ship_id
        return True


bs = BattleshipsEnv()
bs.reset()
bs.place_ships_random(bs.player_ai_grid)
bs.render()
print(bs.player_ai_grid)
