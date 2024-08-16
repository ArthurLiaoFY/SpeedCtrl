from collections import defaultdict

import numpy as np
import plotly
import plotly.graph_objects as go
from agent import Agent
from config import eqp_kwargs, q_learning_kwargs
from eqp_env import EqpEnv
from plotly.subplots import make_subplots

env = EqpEnv(eqp_idx=0, **eqp_kwargs)
agent = Agent(**eqp_kwargs, **q_learning_kwargs)

n_episodes = 10000

rewards = []
nan_process_amount = defaultdict(list)
departs = defaultdict(list)
ability = defaultdict(list)
h_queued = defaultdict(list)
t_queued = defaultdict(list)
r = defaultdict(list)
state_list = defaultdict(list)

max_total_reward = -np.inf

max_step = 500

for episode in range(n_episodes):
    step_cnt = 0
    env.reset()
    total_reward = 0
    departs[episode].append(0)
    ability[episode].append(0)
    h_queued[episode].append(env.current_head_queued)
    t_queued[episode].append(env.current_tail_queued)
    nan_process_amount[episode].append(env.current_unprocessed_amount)
    r[episode].append(None)
    while (
        env.current_unprocessed_amount + env.current_head_queued > 0
        and step_cnt <= max_step
    ):

        state = env.eqp_state.copy()
        state_list[episode].append(state.copy())
        action_idx = agent.select_action_idx(
            state_tuple=tuple(v for v in state.values())
        )
        action = agent.action_idx_to_action(action_idx=action_idx)
        reward, depart_actual, depart_ability = env.step(action=action)
        departs[episode].append(depart_actual)
        ability[episode].append(depart_ability)
        h_queued[episode].append(env.current_head_queued)
        t_queued[episode].append(env.current_tail_queued)
        nan_process_amount[episode].append(env.current_unprocessed_amount)
        r[episode].append(reward)

        agent.update_policy(
            state_tuple=tuple(v for v in state.values()),
            action_idx=action_idx,
            reward=reward,
            next_state_tuple=tuple(v for v in env.eqp_state.values()),
        )

        total_reward += reward
        step_cnt += 1
    agent.update_lr_er(episode=episode)
    rewards.append(total_reward / step_cnt)
    if total_reward > max_total_reward:
        # print
        max_total_reward = total_reward
        print(
            f"Episode {episode}/{n_episodes}: Total reward : {total_reward}, Step: {step_cnt}"
        )


agent.save_table(
    prefix="single_machine_v2"
    + f"_feeding_speed_{eqp_kwargs.get('feeding_speed')}"
    + f"_shipping_speed_{eqp_kwargs.get('shipping_speed')}"
    + "_"
)
import json

with open("tmp.pkl", 'w') as f:
    json.dump(state_list[n_episodes-1], f)

fig = go.Figure()

fig.add_trace(go.Scatter(x=np.arange(len(rewards)), y=rewards, mode="lines+markers"))
plotly.offline.plot(figure_or_data=fig, filename="reward_trend.html")

case = [999, 4999]
fig = make_subplots(rows=len(case), cols=1)
for idx, flag in enumerate([999, 4999]):
    fig.add_trace(
        go.Scatter(
            x=np.arange(len(departs[flag])),
            y=departs[flag],
            mode="lines+markers",
            name=flag,
            legendgroup="departs",
            legendgrouptitle={"text": "departs"},
        ),
        row=idx+1,
        col=1
    )
    fig.add_trace(
        go.Scatter(
            x=np.arange(len(ability[flag])),
            y=ability[flag],
            mode="lines+markers",
            name=flag,
            legendgroup="expects",
            legendgrouptitle={"text": "expects"},
        ),
        row=idx + 1,
        col=1,
    )
    # fig.add_trace(
    #     go.Scatter(
    #         x=np.arange(len(departs[flag])),
    #         y=np.cumsum(departs[flag]),
    #         mode="lines+markers",
    #         name=flag,
    #         legendgroup="cumulate departs",
    #         legendgrouptitle={"text": "cumulate departs"},
    #     )
    # )
    fig.add_trace(
        go.Scatter(
            x=np.arange(len(h_queued[flag])),
            y=h_queued[flag],
            mode="lines+markers",
            name=flag,
            legendgroup="head queued",
            legendgrouptitle={"text": "head queued"},
        ),
        row=idx + 1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=np.arange(len(t_queued[flag])),
            y=t_queued[flag],
            mode="lines+markers",
            name=flag,
            legendgroup="tail queued",
            legendgrouptitle={"text": "tail queued"},
        ),
        row=idx + 1,
        col=1,
    )
    # fig.add_trace(
    #     go.Scatter(
    #         x=np.arange(len(nan_process_amount[flag])),
    #         y=nan_process_amount[flag],
    #         mode="lines+markers",
    #         name=flag,
    #         legendgroup="prod left",
    #         legendgrouptitle={"text": "prod left"},
    #     )
    # )
    fig.add_trace(
        go.Scatter(
            x=np.arange(len(r[flag])),
            y=r[flag],
            mode="lines+markers",
            name=flag,
            legendgroup="reward",
            legendgrouptitle={"text": "reward"},
        ),
        row=idx + 1,
        col=1,
    )
plotly.offline.plot(figure_or_data=fig, filename="depart_trend.html")
