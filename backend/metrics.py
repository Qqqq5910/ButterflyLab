"""Metric definitions and independent mathematical implementations."""
import networkx as nx
import numpy as np
DEFINITIONS = {
 'coverage': {'name':'Information Coverage','formula':'informed agent count / N','range':'[0,1]','note':'Includes configured origins; actual recorded adoption paths, not a causal estimate.'},
 'mean_trust': {'name':'Mean Trust','formula':'sum active edge trust / active edge count','range':'[0,1]','note':'Undirected active ties; no ties returns 0. Removing weak edges changes the denominator.'},
 'resource_mean': {'name':'Mean Resources','formula':'sum agent resources / N','range':'[0,total opening resources + treasury]','note':'Resource units per agent; transfers conserve resources, incentives debit finite treasury. Interventions are explicit external injections/removals.'},
 'cooperation': {'name':'Cooperation Rate','formula':'count(action = cooperate) / N','range':'[0,1]','note':'Each agent has one valid decision opportunity per round, including isolated agents. N is the population, not the edge count. Round zero is intended action. Empty population returns 0.'},
 'disagreement': {'name':'Opinion Disagreement','formula':'sum(i<j) |opinion_i-opinion_j| / (N*(N-1)/2)','range':'[0,1]','note':'Mean absolute difference over unordered agent pairs on [0,1]. N<2 returns 0. This measures disagreement, not polarization.'},
 'largest_component': {'name':'Largest Component Ratio','formula':'max(component node count) / N','range':'[0,1]','note':'Undirected actual relationships with weight>0, including isolated nodes. Empty population returns 0. The current engine retains positive edges, so a connected initial graph stays connected.'},
 'polarization': {'name':'Opinion polarization','formula':'4 * mean((opinion - mean(opinion))^2)','range':'[0,1]','note':'Variance proxy, not a full description of multimodality.'},
 'inequality': {'name':'Resource Gini','formula':'sum_i sum_j |r_i-r_j| / (2 N sum_i r_i)','range':'[0,(N-1)/N]','note':'Nonnegative resources. Empty population and all-zero resources return 0.'},
 'modularity': {'name':'Network modularity','formula':'sum_c [L_c/m - (k_c/(2m))^2]','range':'[-0.5,1]','note':'Weighted undirected Q for a fixed initial greedy-modularity partition, shared across branches and time.'},
 'diversity': {'name':'Opinion diversity','formula':'-sum_b p_b log(p_b) / log(5)','range':'[0,1]','note':'Shannon entropy in five fixed equal-width bins over [0,1].'},
 'cascade': {'name':'Cascade size','formula':'number of informed agents linked by recorded transmissions from A01','range':'[1,N]','note':'Cumulative unique adoption, including origin; not a causal effect estimate.'},
}
def gini(values):
    a=np.sort(np.array(values,dtype=float)); n=len(a)
    if not n or a.sum()==0: return 0.0
    return float(2*np.sum(np.arange(1,n+1)*a)/(n*a.sum())-(n+1)/n)
def polarization(values): return float(4*np.var(values)) if len(values) else 0.0
def disagreement(values):
    n=len(values)
    if n<2: return 0.0
    a=np.asarray(values,dtype=float)
    return float(np.abs(a[:,None]-a[None,:]).sum()/(n*(n-1)))
def largest_component(agents,edges):
    if not agents: return 0.0
    graph=nx.Graph(); graph.add_nodes_from(a['id'] for a in agents)
    graph.add_edges_from((e['source'],e['target']) for e in edges if e['weight']>0 and e['source'] in graph and e['target'] in graph)
    return max(map(len,nx.connected_components(graph)))/len(agents)
def diversity(values):
    if not len(values): return 0.0
    counts=np.histogram(values,bins=np.linspace(0,1,6))[0]; p=counts[counts>0]/len(values)
    return float(-np.sum(p*np.log(p))/np.log(5))
def modularity(edges,groups):
    graph=nx.Graph()
    for group in groups: graph.add_nodes_from(group)
    graph.add_weighted_edges_from([(e['source'],e['target'],e['weight']) for e in edges])
    if graph.size(weight='weight')==0: return 0.0
    return float(nx.community.modularity(graph,[set(g) for g in groups],weight='weight'))
def calculate(agents,edges,groups):
    return {'cooperation':sum(a['action']=='cooperate' for a in agents)/len(agents) if agents else 0.0,
      'disagreement':disagreement([a['opinion'] for a in agents]),'largest_component':largest_component(agents,edges),
      'polarization':polarization([a['opinion'] for a in agents]),'inequality':gini([a['resource'] for a in agents]),
      'modularity':modularity(edges,groups),'diversity':diversity([a['opinion'] for a in agents]),
      'cascade':sum(a['informed'] for a in agents)}
def summarize(deltas,threshold=.02,direction='decrease'):
    a=np.array(deltas,dtype=float); n=len(a); ci=None
    if n>1:
        draws=np.random.default_rng(20261008).choice(a,size=(2000,n),replace=True).mean(axis=1)
        ci=[float(x) for x in np.quantile(draws,[.025,.975])]
    signed=-a if direction=='decrease' else a
    return {'n':n,'deltas':deltas,'mean':float(np.mean(a)),'std':float(np.std(a,ddof=1)) if n>1 else None,
      'ci95':ci,'frequency':float(np.mean(signed>=threshold)),'threshold':threshold,'direction':direction,
      'method':'paired percentile bootstrap; 2000 resamples; seed 20261008'}
def change_points(series,threshold=.15,window=3):
    hits=[]
    for t in range(window,len(series)):
        d=series[t]['cooperation']-sum(s['cooperation'] for s in series[t-window:t])/window
        if abs(d)>=threshold: hits.append({'round':t,'metric':'cooperation','change':d,'rule':'absolute change >= 0.15 versus preceding 3-round mean'})
    return hits
