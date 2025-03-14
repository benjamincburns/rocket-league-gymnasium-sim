"""
    The Rocket League gymnasium environment.
"""
from typing import List, Union, Tuple, Dict, Any
from gymnasium import Env
from rlgymnasium_sim.simulator import RocketSimGame
import RocketSim as rsim
from rlgymnasium_sim.utils import common_values


class Gym(Env):
    def __init__(self, match, copy_gamestate_every_step, dodge_deadzone,
                 tick_skip, gravity, boost_consumption):
        super().__init__()

        self._match = match
        self.observation_space = match.observation_space
        self.action_space = match.action_space
        self._prev_state = None

        self._game = RocketSimGame(match,
                                   copy_gamestate=copy_gamestate_every_step,
                                   dodge_deadzone=dodge_deadzone,
                                   tick_skip=tick_skip)

        self.update_settings(gravity=gravity, boost_consumption=boost_consumption, tick_skip=tick_skip)

    def reset(self, *, seed: int | None = None, options: Dict[str, Any] | None = None) -> Tuple[List, Dict[str, Any]]:
        """
        The environment reset function. When called, this will reset the state
        of the environment and objects in the game. This should be called once
        when the environment is initialized, then every time the `done` flag
        from the `step()` function is `True`.
        
        :param seed: The seed to use for the environment. If `None`, the
         environment will use whatever seed it was last given. This must be
         called with a seed before the environment can be used.
        
        :param options: A dictionary of options to be passed to the game,
         currently unused
        
        :return: A tuple containing (obs, info)
        """
        
        super().reset(seed=seed, options=options)

        state_str = self._match.get_reset_state()
        state = self._game.reset(state_str)

        self._match.episode_reset(state)
        self._prev_state = state

        obs = self._match.build_observations(state)
        info = {
            'state': state,
            'result': self._match.get_result(state)
        }
        return obs, info

    def step(self, actions: Any) -> Tuple[List, List, bool, bool, Dict[str, Any]]:
        """
        The step function will send the list of provided actions to the game,
        then advance the game forward by `tick_skip` physics ticks using that
        action. The game is then paused, and the current state is sent back to
        rlgymnasium_sim This is decoded into a `GameState` object, which gets
        passed to the configuration objects to determine the rewards, next
        observation, and done signal.

        :param actions: An object containing actions, in the format specified
         by the `ActionParser`.

        :return: A tuple containing (obs, rewards, terminated, truncated, info)
        """

        actions = self._match.format_actions(self._match.parse_actions(actions, self._prev_state))

        state = self._game.step(actions)

        obs = self._match.build_observations(state)
        done = self._match.is_done(state)
        reward = self._match.get_rewards(state, done)
        self._prev_state = state

        info = {
            'state': state,
            'result': self._match.get_result(state)
        }

        return obs, reward, done, False, info

    def close(self):
        pass

    def update_settings(self, gravity=None, boost_consumption=None, tick_skip=None):
        """
        Updates the specified RocketSim instance settings

        :param gravity: Scalar to be multiplied by in-game gravity. Default 1.

        :param boost_consumption: Scalar to be multiplied by default boost
        consumption rate. Default 1.

        :param tick_skip: Number of physics ticks the simulator will be
         advanced with the current controls before a `GameState` is returned at
         each call to `step()`.
        """

        mutator_cfg = self._game.arena.get_mutator_config()
        if gravity is not None:
            mutator_cfg.gravity = rsim.Vec(0, 0, common_values.GRAVITY_Z*gravity)

        if boost_consumption is not None:
            mutator_cfg.boost_used_per_second = common_values.BOOST_CONSUMED_PER_SECOND*boost_consumption

        if tick_skip is not None:
            self._game.tick_skip = tick_skip
            self._match.tick_skip = tick_skip

        self._game.arena.set_mutator_config(mutator_cfg)
