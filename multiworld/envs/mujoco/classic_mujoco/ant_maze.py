import os.path as osp
import numpy as np

from multiworld.envs.env_util import get_asset_full_path
from multiworld.envs.mujoco.classic_mujoco.ant import AntEnv

PRESET1 = np.array([
    [-3, 0],
    [0, -3],
])


class AntMazeEnv(AntEnv):
    def __init__(
            self,
            *args,
            model_path='classic_mujoco/ant_maze.xml',
            goal_sampling_strategy='uniform',
            presampled_goal_paths='',
            presampled_goal_key='state_observation',
            **kwargs
    ):
        self.quick_init(locals())
        self.model_path = model_path
        super().__init__(
            *args,
            model_path=model_path,
            **kwargs
        )
        assert goal_sampling_strategy in {'uniform', 'preset1', 'presampled'}
        self.goal_sampling_strategy = goal_sampling_strategy
        self.presampled_goal_key = presampled_goal_key
        if self.goal_sampling_strategy == 'presampled':
            assert presampled_goal_paths is not None
            if not osp.exists(presampled_goal_paths):
                presampled_goal_paths = get_asset_full_path(
                    presampled_goal_paths
                )
            self.presampled_goals = np.load(presampled_goal_paths)
            if presampled_goal_key == 'qpos_observation':
                self.presampled_goals = self.presampled_goals[:15]
        else:
            self.presampled_goals = None

    def _sample_random_goal_vectors(self, batch_size):
        if self.goal_sampling_strategy == 'uniform':
            assert self.goal_is_xy
            goals = self._sample_uniform_xy(batch_size)
        elif self.goal_sampling_strategy == 'preset1':
            assert self.goal_is_xy
            goals = PRESET1[
                np.random.randint(PRESET1.shape[0], size=batch_size), :
            ]
        elif self.goal_sampling_strategy == 'presampled':
            idxs = np.random.randint(
                self.presampled_goals.shape[0], size=batch_size,
            )
            goals = self.presampled_goals[idxs, :]
        else:
            raise NotImplementedError(self.goal_sampling_strategy)

        return goals

    def _sample_uniform_xy(self, batch_size):
        goals = np.random.uniform(
            self.goal_space.low[:2],
            self.goal_space.high[:2],
            size=(batch_size, 2),
        )
        if 'small' in self.model_path:
            goals[(0 <= goals) * (goals < 0.5)] += 1
            goals[(0 <= goals) * (goals < 1.25)] += 1
            goals[(0 >= goals) * (goals > -0.5)] -= 1
            goals[(0 >= goals) * (goals > -1.25)] -= 1
        else:
            goals[(0 <= goals) * (goals < 0.5)] += 2
            goals[(0 <= goals) * (goals < 1.5)] += 1.5
            goals[(0 >= goals) * (goals > -0.5)] -= 2
            goals[(0 >= goals) * (goals > -1.5)] -= 1.5
        return goals


if __name__ == '__main__':
    env = AntMazeEnv(
        goal_low=[-4, -4],
        goal_high=[4, 4],
        goal_is_xy=True,
        reward_type='xy_dense',
    )
    import gym
    from multiworld.envs.mujoco import register_custom_envs
    register_custom_envs()
    env = gym.make('AntMaze150RandomInitEnv-v0')
    # env = gym.make('AntCrossMaze150Env-v0')
    # env = gym.make('DebugAntMaze30BottomLeftRandomInitGoalsPreset1Env-v0')
    env = gym.make(
        # 'AntMaze30RandomInitFS20Env-v0',
        # 'AntMaze30RandomInitEnv-v0',
        # 'AntMazeSmall30RandomInitFS10Env-v0',
        # 'AntMazeSmall30RandomInitFs5Dt3Env-v0',
        # 'AntMaze30RandomInitNoVelEnv-v0',
        # 'AntMaze30StateEnv-v0',
        'AntMaze30QposRandomInitFS20Env-v0',
    )
    env.reset()
    i = 0
    while True:
        i += 1
        env.render()
        action = env.action_space.sample()
        # action = np.zeros_like(action)
        _, reward, *_ = env.step(action)
        # print(reward, np.linalg.norm(env.sim.data.get_body_xpos('torso')[:2]
        #                              - env._xy_goal) )
        # print(env.sim.data.qpos)
        if i % 5 == 0:
            env.reset()