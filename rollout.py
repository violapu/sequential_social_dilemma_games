"""Defines a multi-agent controller to rollout environment episodes w/
   agent policies."""

import utility_funcs
import numpy as np
import os
import sys
import shutil
import tensorflow as tf
import torch
import matplotlib.pyplot as plt

from social_dilemmas.envs.norm import NormEnv
from social_dilemmas.observer import Observer

FLAGS = tf.app.flags.FLAGS

tf.app.flags.DEFINE_string(
    'vid_path', os.path.abspath(os.path.join(os.path.dirname(__file__), './videos')),
    'Path to directory where videos are saved.')
tf.app.flags.DEFINE_string(
    'env', 'norm',
    'Name of the environment to rollout. Can be cleanup, harvest or norm.')
tf.app.flags.DEFINE_string(
    'render_type', 'pretty',
    'Can be pretty or fast. Implications obvious.')
tf.app.flags.DEFINE_integer(
    'fps', 8,
    'Number of frames per second.')


class Controller(object):

    def __init__(self, env_name='norm'):
        self.env_name = env_name
        if env_name == 'norm':
            print('Initializing norm environment')
            self.env = NormEnv(num_agents=2, render=True,
                               norm={'G':True, 'R':False,'B':False}, reward={'G':0.5,'R':0.5,'B':0.5})
        else:
            print('Error! Not a valid environment type')
            return

        self.env.reset()

        # TODO: initialize agents here

    def rollout(self, horizon=500, save_path=None):
        """ Rollout several timesteps of an episode of the environment.

        Args:
            horizon: The number of timesteps to roll out.
            save_path: If provided, will save each frame to disk at this
                location.
        """
        rewards = []
        observations = []
        shape = self.env.world_map.shape
        full_obs = [np.zeros(
            (shape[0], shape[1], 3), dtype=np.uint8) for i in range(horizon)]

        observer = Observer(list(self.env.agents.values())[0].grid.copy())
        loss_norm=[]
        for i in range(horizon):
            agents = list(self.env.agents.values())
            observer.update_grid(agents[0].grid)
            action_dim = agents[0].action_space.n
            depth = 2
            # 3- go right; 2 - go left; 1 - go down; 0 - go up;
            action_list = []
            for j in range(self.env.num_agents):
                act = agents[j].policy(depth)
                action_list.append(act)
            obs, rew, dones, info, = self.env.step({'agent-%d'%k: action_list[k] for k in range(self.env.num_agents)})
            loss_norm.append(float(observer.observation(action_list)))
            #for agent in range(self.env.num_agents):
            #    print(agents[agent].reward)

            sys.stdout.flush()

            if save_path is not None:
                self.env.render(filename=save_path + 'frame' + str(i).zfill(6) + '.png')

            rgb_arr = self.env.map_to_colors()
            full_obs[i] = rgb_arr.astype(np.uint8)
            observations.append(obs['agent-0'])
            rewards.append(rew['agent-0'])
        #print("Loss norm: ", loss_norm)

        return rewards, observations, full_obs

    def render_rollout(self, horizon=500, path=None,
                       render_type='pretty', fps=8):
        """ Render a rollout into a video.

        Args:
            horizon: The number of timesteps to roll out.
            path: Directory where the video will be saved.
            render_type: Can be 'pretty' or 'fast'. Impliciations obvious.
            fps: Integer frames per second.
        """
        if path is None:
            path = os.path.abspath(os.path.dirname(__file__)) + '/videos'
            print(path)
            if not os.path.exists(path):
                os.makedirs(path)
        video_name = self.env_name + '_trajectory'

        if render_type == 'pretty':
            image_path = os.path.join(path, 'frames/')
            if not os.path.exists(image_path):
                os.makedirs(image_path)

            rewards, observations, full_obs = self.rollout(
                horizon=horizon, save_path=image_path)
            utility_funcs.make_video_from_image_dir(path, image_path, fps=fps,
                                                    video_name=video_name)

            # Clean up images
            shutil.rmtree(image_path)
        else:
            rewards, observations, full_obs = self.rollout(horizon=horizon)
            utility_funcs.make_video_from_rgb_imgs(full_obs, path, fps=fps,
                                                   video_name=video_name)


def main(unused_argv):
    c = Controller(env_name=FLAGS.env)
    c.render_rollout(path=FLAGS.vid_path, render_type=FLAGS.render_type,
                     fps=FLAGS.fps)


if __name__ == '__main__':
    tf.app.run(main)
