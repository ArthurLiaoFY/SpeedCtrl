from collections import defaultdict

import numpy as np
import plotly
import plotly.graph_objects as go
from agent import Agent
from config import kwargs
from machine_level_agent.eqp_env import EqpEnv

env = EqpEnv(**kwargs)
agent = Agent(**kwargs)

n_episodes = 500  # 5000

rewards = {idx: [] for idx in range(kwargs.get("num_of_eqps"))}
max_total_reward = {idx: -np.inf for idx in range(kwargs.get("num_of_eqps"))}

max_step = 500

for episode in range(n_episodes):
    step_cnt = 0
    env.reset()
    total_reward = {idx: 0 for idx in range(kwargs.get("num_of_eqps"))}
    while sum(env.current_head_queued_list) > 0 and step_cnt <= max_step:
        for eqp_idx in range(kwargs.get("num_of_eqps")):
            state = env.state_dict[eqp_idx]
            action_idx = agent.select_action_idx(
                state_tuple=tuple(v for v in state.values())
            )
            action = agent.action_idx_to_action(action_idx=action_idx)
            reward = env.step(action=action, eqp_idx=eqp_idx)
            agent.update_policy(
                state_tuple=tuple(v for v in state.values()),
                action_idx=action_idx,
                reward=reward,
                next_state_tuple=tuple(v for v in env.state_dict[eqp_idx].values()),
            )

            total_reward[eqp_idx] += reward
        step_cnt += 1

    for eqp_idx in range(kwargs.get("num_of_eqps")):
        agent.update_lr_er(episode=episode)
        rewards[eqp_idx].append(total_reward[eqp_idx] / step_cnt)
        if total_reward[eqp_idx] > max_total_reward[eqp_idx]:
            # print
            max_total_reward[eqp_idx] = total_reward[eqp_idx]
            print(
                f"Episode {episode}/{n_episodes}: Total reward ({eqp_idx}): {total_reward[eqp_idx] / step_cnt}"
            )


agent.save_table(prefix="single_machine_v2_")

fig = go.Figure()
for idx, reward_l in rewards.items():
    fig.add_trace(
        go.Scatter(
            x=np.arange(len(reward_l)), y=reward_l, mode="lines+markers", name=idx
        )
    )
plotly.offline.plot(figure_or_data=fig, filename="reward_trend.html")
