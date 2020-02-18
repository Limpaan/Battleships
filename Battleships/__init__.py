from gym.envs.registration import register

register(
    id='battleships-v0',
    entry_point='Battleships.envs:BattleshipsEnv',
)