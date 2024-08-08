from collections import defaultdict

import numpy as np
import plotly
import plotly.graph_objects as go
from agent import Agent
from config import kwargs
from env import Env

env = Env(**kwargs)
agent = [Agent(**kwargs) for _ in range(kwargs.get("num_of_eqps"))]

n_episodes = 300
env_step = 1000

rewards = defaultdict(list)
max_total_reward = {idx: -np.inf for idx in range(kwargs.get("num_of_eqps"))}


for episode in range(n_episodes):
    env.reset()
    total_reward = defaultdict(lambda: 0)
    for t in range(env_step):
        m_arrived = np.sin(t / 30) * 20 + 100 + 0.2 * t + np.random.randn() * 5 // 1
        for eqp_idx in range(kwargs.get("num_of_eqps")):
            state = env.state
            action_idx = agent[eqp_idx].select_action_idx(
                state_tuple=tuple(v for v in state.values())
            )
            action = agent[eqp_idx].action_idx_to_action(action_idx=action_idx)
            reward, m_arrived = env.step(
                action=action, eqp_idx=eqp_idx, m_arrived=m_arrived
            )
            agent[eqp_idx].update_policy(
                state_tuple=tuple(v for v in state.values()),
                action_idx=action_idx,
                reward=reward,
                next_state_tuple=tuple(v for v in env.state.values()),
            )

            total_reward[eqp_idx] += reward / env_step

    for eqp_idx in range(kwargs.get("num_of_eqps")):
        agent[eqp_idx].update_lr_er(episode=episode)
        rewards[eqp_idx].append(total_reward[eqp_idx])
        if total_reward[eqp_idx] > max_total_reward[eqp_idx]:
            # print
            max_total_reward[eqp_idx] = total_reward[eqp_idx]
            print(
                f"Episode {episode}/{n_episodes}: Total reward ({eqp_idx}): {total_reward[eqp_idx]}"
            )


# agent.save_table(prefix="single_machine_v2_")

fig = go.Figure()
for idx, reward_l in rewards.items():
    fig.add_trace(
        go.Scatter(
            x=np.arange(len(reward_l)), y=reward_l, mode="lines+markers", name=idx
        )
    )
plotly.offline.plot(figure_or_data=fig, filename="reward_trend.html")
