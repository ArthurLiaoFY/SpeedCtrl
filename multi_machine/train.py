from collections import defaultdict

import numpy as np
import plotly
import plotly.graph_objects as go
from agent import Agent
from config import kwargs
from env import Env

num_of_eqps = 3
n_episodes = 100
env_step = 1000

env = Env(num_of_eqps=num_of_eqps)
feeding_agent = Agent(**kwargs)
working_agents = [Agent(**kwargs) for _ in range(num_of_eqps)]
ending_agent = Agent(**kwargs)


feeding_rewards = []
working_rewards = []
ending_rewards = []

max_feeding_reward = -np.inf
max_working_rewards = [-np.inf for _ in range(3)]
max_ending_rewards = -np.inf


for episode in range(n_episodes):

    env.reset(num_of_eqps=num_of_eqps)
    feeding_reward = 0
    working_reward_l = [0 for _ in range(3)]
    ending_reward = 0

    for t in range(env_step):

        for eqp_idx in range(num_of_eqps):
            if eqp_idx == 0:
                action_idx = feeding_agent.select_action_idx(
                    state_tuple=tuple(v for v in env.state.values())
                )
                action = feeding_agent.action_idx_to_action(action_idx=action_idx)
                reward, m_depart = env.step(action=action, time=t, eqp_idx=eqp_idx + 1)
                feeding_agent.update_policy(
                    state_tuple=tuple(v for v in env.state.values()),
                    action_idx=action_idx,
                    reward=reward,
                    next_state_tuple=tuple(v for v in env.state.values()),
                )
                feeding_reward += reward / env_step
            elif eqp_idx == (num_of_eqps - 1):
                action_idx = ending_agent.select_action_idx(
                    state_tuple=tuple(v for v in env.state.values())
                )
                action = ending_agent.action_idx_to_action(action_idx=action_idx)
                reward, m_depart = env.step(
                    action=action, time=t, m_arrived=m_depart, eqp_idx=eqp_idx + 1
                )
                ending_agent.update_policy(
                    state_tuple=tuple(v for v in env.state.values()),
                    action_idx=action_idx,
                    reward=reward,
                    next_state_tuple=tuple(v for v in env.state.values()),
                )
                ending_reward += reward / env_step

            else:
                action_idx = working_agents[eqp_idx].select_action_idx(
                    state_tuple=tuple(v for v in env.state.values())
                )
                action = working_agents[eqp_idx].action_idx_to_action(
                    action_idx=action_idx
                )
                reward, m_depart = env.step(
                    action=action, time=t, m_arrived=m_depart, eqp_idx=eqp_idx + 1
                )
                working_agents[eqp_idx].update_policy(
                    state_tuple=tuple(v for v in env.state.values()),
                    action_idx=action_idx,
                    reward=reward,
                    next_state_tuple=tuple(v for v in env.state.values()),
                )

                working_reward_l[eqp_idx] += reward / env_step
    feeding_agent.update_lr_er(episode=episode)
    for eqp_idx in range(num_of_eqps):
        working_agents[eqp_idx].update_lr_er(episode=episode)

    feeding_rewards.append(feeding_reward)
    if feeding_reward > max_feeding_reward:
        # print
        max_feeding_reward = feeding_reward
        print(f"Episode {episode}/{n_episodes}: feeding reward: {feeding_reward}")

    working_rewards.append(working_reward_l)
    for idx in range(num_of_eqps):
        if working_reward_l[idx] > max_working_rewards[idx]:
            # print
            max_working_rewards[idx] = working_reward_l[idx]
            print(
                f"Episode {episode}/{n_episodes}: working reward {idx}: {working_reward_l[idx]}"
            )


# feeding_agent.save_table(prefix="feeding_agent_")

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=np.arange(len(feeding_rewards)),
        y=feeding_rewards,
        mode="lines+markers",
        name="feeding agent",
    )
)
for idx, r in enumerate(np.array(working_rewards).T):
    fig.add_trace(
        go.Scatter(
            x=np.arange(len(r)), y=r, mode="lines+markers", name=f"working agent {idx}"
        )
    )

plotly.offline.plot(figure_or_data=fig, filename="reward_trend.html")
