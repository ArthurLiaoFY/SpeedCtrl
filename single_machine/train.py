from collections import defaultdict

import numpy as np
import plotly
import plotly.graph_objects as go

from agent import Agent
from config import kwargs
from no_fault_max_uph_env import Env

env = Env()
agent = Agent(**kwargs)

n_episodes = 1000
env_step = 500

rewards = []
max_total_reward = -np.inf


for episode in range(n_episodes):
    env.reset()
    total_reward = 0
    for t in range(env_step):
        state = env.state
        action_idx = agent.select_action_idx(
            state_tuple=tuple(v for v in state.values())
        )
        action = agent.action_idx_to_action(action_idx=action_idx)
        reward = env.step(action, t)
        agent.update_policy(
            state_tuple=tuple(v for v in state.values()),
            action_idx=action_idx,
            reward=reward,
            next_state_tuple=tuple(v for v in env.state.values()),
        )

        total_reward += reward/env_step

    agent.update_lr_er(episode=episode)
    rewards.append(total_reward)
    if total_reward > max_total_reward:
        # print
        max_total_reward = total_reward
        print(f"Episode {episode}/{n_episodes}: Total reward: {total_reward}")


agent.save_table(prefix='single_machine_')

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=np.arange(len(rewards)),
        y=rewards,
        mode="lines+markers",
    )
)
plotly.offline.plot(figure_or_data=fig, filename="reward_trend.html")
# fig = go.Figure()
# fig.add_trace(
#     go.Scatter(
#         x=np.arange(len(rewards)),
#         y=rewards,
#         mode="lines+markers",
#     )
# )
# plotly.offline.plot(figure_or_data=fig, filename="reward_trend.html")
