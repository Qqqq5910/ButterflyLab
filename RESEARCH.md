# Research protocol and social rules

Phase 2C scanning, exploratory detection, independent validation and finite-size limitations are specified in [the Phase 2C protocol](docs/PHASE2C.md). Descriptive bootstrap intervals are not automatic significance claims, and screened regions are not proof of a phase transition.

These are synthetic mechanisms, not validated models of human behavior.
`0.2.0` remains the legacy engine. `social-1.0.0` is an opt-in new model.
Parameter values are research choices, not empirical estimates.

## Deterministic order

At each round freeze opening agents and active edges, then:

1. Decide all actions from the same opening state.
2. Execute simultaneous capped donations and treasury-funded incentives.
3. Update experience from this round's neighbor cooperation.
4. Propagate information from previously informed senders only; synchronously
   update opinions from opening neighbor opinions.
5. Update trust from cooperation mismatch/mutual cooperation and actual
   successful transmission.
6. Remove ties below threshold and append bounded agent memories.
7. Record actual snapshots, metrics and events.

Topology generation uses the paired seed; positions use a fixed seeded layout.
Behavior noise is addressed by seed/round/agent, propagation by
seed/round/source/target, not by branch-dependent random call counts.

## Explicit formulas

For agent i, with opening resource r, propensity p, mean active tie trust T,
experience h, incentive parameter I, and U in [0,1]:

`scarcity = max(0, 1-r/40)`

`score = .35p + .25T + .2h + .2I - .4scarcity + .1(U-.5)`

Cooperate iff score >= configured threshold. No neighbors means T=0. With
cooperation disabled, previous actions remain and transfers/experience freeze.

An acting donor gives `min(opening_balance, exchange * recipient_count)`,
equally split over recipients. Rule actions target all neighbors; structured
actions may select one neighbor. Requested reward is `I * outgoing`; all
rewards share `min(1, treasury / sum(requested))`. Debit that exact total from
the finite treasury. Transfers conserve sum(agent resources)+treasury up to
floating-point error. Resource intervention is explicit external injection or
removal, clamped at zero. There is no arbitrary upper clipping of holdings.

`h_next = .8h + .2 mean(current neighbor cooperation)`; isolates retain h.

`P(j -> i) = transmission * trust_ij * strength_ij * susceptibility_i`.
Each eligible directed edge uses its independent addressed draw; the first
successful prior-informed neighbor in stable ID order records source, target,
round and probability. New recipients cannot transmit within the same round.
Coverage includes configured information origins.

`opinion_next = clip(opinion + opinion_speed * (weighted_peer_mean-opinion))`,
weights = trust * strength; zero total weight keeps opinion unchanged. Opinion
disagreement is not claimed to be polarization. Disabling diffusion freezes
both information and opinion updates.

`trust_next = clip(trust + trust_speed * (reward + communication))` in [0,1],
reward = +1 mutual cooperation, -1 action mismatch, 0 mutual competition;
communication = .25 for an actual successful transmission along the tie,
otherwise zero. When enabled, pruning removes trust below break_threshold.
No new ties are created in this engine version.

## Metrics

| Metric | Formula / denominator | Range and boundary |
| --- | --- | --- |
| Cooperation | cooperating actions / N valid per-agent decision opportunities | [0,1]; includes isolates; round zero is intended action; empty=0 |
| Resource Gini | sum(i,j) abs(r_i-r_j)/(2N sum r) | [0,(N-1)/N]; all zero or empty=0 |
| Opinion disagreement | mean abs difference over N(N-1)/2 unordered pairs | [0,1]; N<2=0; not a multimodality measure |
| Largest component | largest actual positive-trust connected component / N | [0,1]; isolates included; empty=0 |
| Information coverage | informed agents / N | [0,1]; includes origins |
| Mean trust | sum(active tie trust) / active tie count | [0,1]; no ties=0; pruning changes denominator |
| Mean resources | sum(agent resources) / N | nonnegative units per agent; treasury transfers can raise it |

Time curves use [0,1] ratio axes; resource curves start at zero in resource
units. Effect bars use a symmetric zero-centered extent containing all effects.
Heatmaps retain all requested cells and disclose their symmetric color extent.

## Experimental design and limitations

Thirty paired seeds are the default after creating a social world, configurable
1-100. Pair initial worlds before intervention. Report each final B-A effect,
mean, sample SD and deterministic percentile bootstrap interval (2000
resamples, bootstrap seed 20261008). Thirty seeds are a starting point, not a
guarantee of precision or statistical significance. Multiple metric selection,
grid exploration and winner selection add multiplicity; no automatic causal
or significance claim is produced.

Ablation explicitly sets one mechanism on for A and off for B, retaining
identical opening agents/edges. Sensitivity compares every Cartesian parameter
cell to the requested reference world. Resource scale necessarily regenerates
resource holdings with the same seed. Studies reject an additional intervention
so parameter and intervention contrasts are not conflated.

Search reports candidate cost and discovery uncertainty, then independently
validates the selected candidate with disjoint seeds. The current search family
is resource interventions only; it is not a global optimizer.

## Three reproducibility claims

1. Rule mode: same config/seeds/engine/dependencies produces exact complete
   simulation results. Metadata timestamps are excluded from equality.
2. Fresh external model calls: no exact equality claim, even at temperature 0.
3. Recorded validated decisions: exact trajectory replay under the same engine
   and configuration. This is not proof of fresh model reproducibility.

Mock and external providers have hard call limits and conservative pre-attempt
token reservations (UTF-8 context bytes + 800, output max 200). This is a budget
proxy rather than provider-billed usage, and model context/tokenization can
differ. Exhaustion is labeled rule fallback. The default demo does not claim
all agents received model decisions. Credentials stay in the server environment.
