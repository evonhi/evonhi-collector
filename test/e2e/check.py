"""Check the payload an in-cluster run produced against a real API server.

Usage: check.py payload.json schema.json
Validates the contract, then analyzes the snapshot with evonhi-core and expects the attack route
planted by fixtures.yaml: web (public) -> patch deployments -> admin-sa -> db-creds.
"""
import json
import sys

import jsonschema
from evonhi_core.models import CrownJewelSpec, ScenarioConfig
from evonhi_core.planning import assess_risk
from evonhi_core.providers.kubernetes.provider import KubernetesProvider
from evonhi_core.providers.kubernetes.snapshot import cluster_model_from_snapshot

payload = json.load(open(sys.argv[1]))
jsonschema.validate(payload, json.load(open(sys.argv[2])))

workloads = {(w["namespace"], w["name"]): w for w in payload["workloads"]}
web, worker = workloads[("shop", "web")], workloads[("shop", "db-worker")]
assert web["public"] and web["exposed_by"] == ["service/LoadBalancer/web"], web
assert worker["public"] and worker["exposed_by"] == ["ingress/api"], worker
assert worker["mounted_secrets"] == ["db-creds"], worker
assert ("shop", "nightly") in workloads, "CronJobs must be collected (batch API group)"
assert all(not any("last-applied" in key for key in (sa.get("annotations") or {})) for sa in payload["service_accounts"])
kube_system = [w for w in payload["workloads"] if w["namespace"] == "kube-system"]
assert kube_system, "system workloads of a real cluster should be present"

model = cluster_model_from_snapshot(payload)
scenario = ScenarioConfig(crown_jewels=[CrownJewelSpec("secret", "db-creds", "shop")])
result = assess_risk(KubernetesProvider().build_graph(model, scenario))
routes = {path.nodes[0]: path for path in result.baseline_paths}
assert "workload:shop:web" in routes, f"expected a route from the public web workload, got {sorted(routes)}"
assert "spawn_workload_as" in routes["workload:shop:web"].relations, routes["workload:shop:web"].relations

print(f"snapshot: {len(payload['workloads'])} workloads, {len(payload['service_accounts'])} service accounts, "
      f"{len(payload['role_bindings']) + len(payload['cluster_role_bindings'])} bindings")
print(f"exposures to shop/db-creds: {result.baseline_exposures}, risk {result.baseline_risk:.2f}")
for path in result.baseline_paths:
    print("  " + path.headline)
