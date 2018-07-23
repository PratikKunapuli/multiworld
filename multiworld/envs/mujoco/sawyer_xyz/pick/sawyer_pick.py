from collections import OrderedDict
import numpy as np
from gym.spaces import Box, Dict

from multiworld.envs.env_util import get_stat_in_paths, \
    create_stats_ordered_dict, get_asset_full_path
from multiworld.core.multitask_env import MultitaskEnv
from multiworld.envs.mujoco.sawyer_xyz.base import SawyerXYZEnv

class SawyerPickEnv(SawyerXYZEnv):
    def __init__(
            self,
            obj_low=None,
            obj_high=None,


            obj_init_pos=(0, 0.6),

            
            goal_low=None,
            goal_high=None,

            

            **kwargs
    ):
        self.quick_init(locals())
       # MultitaskEnv.__init__(self)
        SawyerXYZEnv.__init__(
            self,
            model_name=self.model_name,
            **kwargs
        )
        if obj_low is None:
            obj_low = self.hand_low
        if obj_high is None:
            obj_high = self.hand_high

        if goal_low is None:
            goal_low = np.hstack((self.hand_low, obj_low))
        if goal_high is None:
            goal_high = np.hstack((self.hand_high, obj_high))


        self.max_path_length = 100

        
      
        self.obj_init_pos = np.array([obj_init_pos[0], obj_init_pos[1], 0.02])

       
        self.heightTarget = 0.1


        

        self.action_space = Box(
            np.array([-1, -1, -1, -1]),
            np.array([1, 1, 1, 1]),
        )
        self.hand_and_obj_space = Box(
            np.hstack((self.hand_low, obj_low)),
            np.hstack((self.hand_high, obj_high)),
        )
        self.observation_space = Dict([
          
            ('state_observation', self.hand_and_obj_space),
            
        ])
        #goal is not part of observation space, specified in the dict only to define 
        #self.goal_space. Goal not passed into the network

        self.reset()

    @property
    def model_name(self):
        return get_asset_full_path('sawyer_xyz/sawyer_pick_and_place.xml')

    def viewer_setup(self):
        pass
        # self.viewer.cam.trackbodyid = 0
        # self.viewer.cam.lookat[0] = 0
        # self.viewer.cam.lookat[1] = 1.0
        # self.viewer.cam.lookat[2] = 0.5
        # self.viewer.cam.distance = 0.3
        # self.viewer.cam.elevation = -45
        # self.viewer.cam.azimuth = 270
        # self.viewer.cam.trackbodyid = -1

    def step(self, action):

     
        self.set_xyz_action(action[:3])


       
        
        self.do_simulation([action[-1], -action[-1]])
        # The marker seems to get reset every time you do a simulation
        #self._set_goal_marker(self._state_goal)
        ob = self._get_obs()
       

        reward , pickRew = self.compute_rewards(action)
        self.curr_path_length +=1

       
        #info = self._get_info()

        if self.curr_path_length == self.max_path_length:
            done = True
        else:
            done = False
        return ob, reward, done, {'pickRew':pickRew}

    def _get_obs(self):
        e = self.get_endeff_pos()
        b = self.get_obj_pos()
        flat_obs = np.concatenate((e, b))

        return dict(
           
            state_observation=flat_obs,
            
        )

   
    def get_obj_pos(self):
        return self.data.get_body_xpos('obj').copy()

    
           

    def _set_obj_xyz(self, pos):
        qpos = self.data.qpos.flat.copy()
        qvel = self.data.qvel.flat.copy()

        qpos[9:12] = pos.copy()
        qvel[9:15] = 0
        self.set_state(qpos, qvel)

    def reset_model(self):

        

        self._reset_hand()
       
       

        self._set_obj_xyz(self.obj_init_pos)

        self.curr_path_length = 0
      

        return self._get_obs()

    def _reset_hand(self):
        for _ in range(10):
            self.data.set_mocap_pos('mocap', np.array([0, 0.5, 0.05]))
            self.data.set_mocap_quat('mocap', np.array([1, 0, 1, 0]))
            self.do_simulation(None, self.frame_skip)

    

    def get_site_pos(self, siteName):
        _id = self.model.site_names.index(siteName)
        return self.data.site_xpos[_id].copy()





    def compute_rewards(self, actions):
           
        rightFinger, leftFinger = self.get_site_pos('rightEndEffector'), self.get_site_pos('leftEndEffector')
       
        heightTarget = self.heightTarget
       
        objPos = self.get_body_com("obj")
      

        
        fingerCOM = (rightFinger + leftFinger)/2


        graspDist = np.linalg.norm(objPos - fingerCOM)
        graspRew = -graspDist


        def graspAttained():
            if graspDist <0.1:
                return True

            else:
                return False

      
        def pickReward():

           
       
            if (objPos[2]> 0.025) and graspAttained():
                
                return 10* min(heightTarget, objPos[2])
         
            else:
                return 0

       

        pickRew = pickReward()
       
        reward = graspRew + pickRew 


       
        return [reward, pickRew] 
        #returned in a list because that's how compute_reward in multiTask.env expects it

   

    def get_diagnostics(self, paths, prefix=''):
        statistics = OrderedDict()
        # for stat_name in [
        #     'hand_distance',
        #     'obj_distance',
        #     'hand_and_obj_distance',
        #     'touch_distance',
        #     'hand_success',
        #     'obj_success',
        #     'hand_and_obj_success',
        #     'touch_success',
        # ]:
        #     stat_name = stat_name
        #     stat = get_stat_in_paths(paths, 'env_infos', stat_name)
        #     statistics.update(create_stats_ordered_dict(
        #         '%s%s' % (prefix, stat_name),
        #         stat,
        #         always_show_all_stats=True,
        #     ))
        #     statistics.update(create_stats_ordered_dict(
        #         'Final %s%s' % (prefix, stat_name),
        #         [s[-1] for s in stat],
        #         always_show_all_stats=True,
        #     ))
        return statistics

   