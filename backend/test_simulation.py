from .simulation import simulate, run_experiment, intervention_cost
def test_seed_reproducible():
    assert simulate(7)==simulate(7)
def test_intervention_changes_result():
    a=simulate(7); b=simulate(7,intervention={"agent":"A01","resource_delta":-20})
    assert a["final"] != b["final"]
def test_cost_is_explicit(): assert intervention_cost({"agent":"A01","resource_delta":-10}) == 1.5
def test_multiseed_experiment_has_matched_seeds():
    r=run_experiment({"agent":"A01","resource_delta":-10},[7,8]); assert r["seeds"]==[7,8] and len(r["delta"])==2
