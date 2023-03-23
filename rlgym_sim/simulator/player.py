from rlgym_sim.utils.gamestates import PlayerData, PhysicsObject
from rlgym_sim.utils import common_values
from rlgym_sim.utils import math
import pyrocketsim as rsim
import numpy as np


class Player(object):
    JUMP_TIMER_SECONDS = 1.25
    def __init__(self, car):
        self.id = car.id
        self.car_vec_mem = np.zeros((6,3))
        self.rot_mat_mem = np.zeros((3,3))
        self.inverted_quaternion = np.zeros(4)

        player_data = PlayerData()
        car_state = car.get_state()
        if car.team == rsim.BLUE:
            player_data.team_num = common_values.BLUE_TEAM
        else:
            player_data.team_num = common_values.ORANGE_TEAM

        player_data.car_id = car.id
        player_data.car_data._has_computed_euler_angles = True
        player_data.car_data._has_computed_rot_mtx = True

        self.data = player_data
        self.prev_touched_ticks = car_state.last_hit_ball_tick
        self.update(car)

    def update(self, car):
        player_data = self.data
        physics_data = player_data.car_data
        inverted_physics_data = player_data.inverted_car_data

        car_vec_mem = self.car_vec_mem
        inverted_quaternion = self.inverted_quaternion
        car_state = car.get_state()

        player_data.boost_amount = car_state.boost
        player_data.is_demoed = car_state.is_demoed
        player_data.has_jump = car_state.air_time_since_jump < Player.JUMP_TIMER_SECONDS and not (car_state.has_flipped or car_state.has_double_jumped)
        player_data.on_ground = car_state.is_on_ground
        player_data.has_flip = not car_state.has_flipped

        rot_mat = self.rot_mat_mem
        rot_mat[0, :] = car_state.rot_mat[0].as_numpy()
        rot_mat[1, :] = car_state.rot_mat[1].as_numpy()
        rot_mat[2, :] = car_state.rot_mat[2].as_numpy()
        quaternion = math.rotation_to_quaternion(rot_mat)

        car_vec_mem[0, 0] = car_state.pos.x
        car_vec_mem[0, 1] = car_state.pos.y
        car_vec_mem[0, 2] = car_state.pos.z

        car_vec_mem[1, 0] = car_state.vel.x
        car_vec_mem[1, 1] = car_state.vel.y
        car_vec_mem[1, 2] = car_state.vel.z

        car_vec_mem[2, 0] = car_state.ang_vel.x
        car_vec_mem[2, 1] = car_state.ang_vel.y
        car_vec_mem[2, 2] = car_state.ang_vel.z

        car_vec_mem[3, 0] = -car_vec_mem[0, 0]
        car_vec_mem[3, 1] = -car_vec_mem[0, 1]
        car_vec_mem[3, 2] =  car_vec_mem[0, 2]

        car_vec_mem[4, 0] = -car_vec_mem[1, 0]
        car_vec_mem[4, 1] = -car_vec_mem[1, 1]
        car_vec_mem[4, 2] =  car_vec_mem[1, 2]

        car_vec_mem[5, 0] = -car_vec_mem[2, 0]
        car_vec_mem[5, 1] = -car_vec_mem[2, 1]
        car_vec_mem[5, 2] =  car_vec_mem[2, 2]

        physics_data.position = car_vec_mem[0]
        physics_data.linear_velocity = car_vec_mem[1]
        physics_data.angular_velocity = car_vec_mem[2]
        physics_data.quaternion = quaternion
        physics_data._rotation_mtx = rot_mat
        physics_data._euler_angles = car_state.angles.as_numpy()

        # inverted_quaternion = [quaternion[3], quaternion[2], -quaternion[1], -quaternion[0]]
        inverted_quaternion[0] = quaternion[3]
        inverted_quaternion[1] = quaternion[2]
        inverted_quaternion[2] = -quaternion[1]
        inverted_quaternion[3] = -quaternion[0]
        inverted_physics_data.position=car_vec_mem[3]
        inverted_physics_data.linear_velocity=car_vec_mem[4]
        inverted_physics_data.angular_velocity=car_vec_mem[5]
        inverted_physics_data.quaternion=inverted_quaternion
        inverted_physics_data._has_computed_rot_mtx = False
        inverted_physics_data._has_computed_euler_angles = False

        if self.prev_touched_ticks < car_state.last_hit_ball_tick:
            self.prev_touched_ticks = car_state.last_hit_ball_tick
            player_data.ball_touched = True

        elif self.prev_touched_ticks > car_state.last_hit_ball_tick:
            self.prev_touched_ticks = car_state.last_hit_ball_tick
