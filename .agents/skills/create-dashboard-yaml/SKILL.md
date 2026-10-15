---
name: create-dashboard-yaml
description: Create or edit a Facetra dashboard YAML in Discover using existing workspace charts, shared parameters, tabs, panel bindings and responsive grid layout.
---

# Create a dashboard YAML

Compose existing charts from one workspace into a dashboard. If a requested
chart is missing, author it using the repository chart guide or chart skill.

1. Read [AGENTS.md](../../../AGENTS.md),
   [workspace/parameter format](../../../docs/workspace-yaml.md) and
   [dashboard format](../../../docs/dashboard-yaml.md).
   Identify the topic, dashboard purpose, charts and tab arrangement.
2. Inspect each selected chart's metadata.id, params, defaults, ranges and options.
   Panel chart values use IDs, not file paths. Keep every chart dependency in
   this workspace. Repeated chart instances are allowed with distinct panel IDs.
3. Start from [the minimal dashboard](../../../docs/starter/dashboards/overview.yaml)
   or [the grid example](../../../workspaces/example/dashboards/example_mosaic_dashboard.yaml).
   Save to workspaces/<topic>/dashboards/<optional-folders>/<dashboard-id>.yaml, matching its
   filename to metadata.id. Include version: 1, kind: Dashboard, metadata, params and tabs.
   Put resource id/title/notes/tags in metadata; keep tab/panel IDs in their own blocks.
   Tab IDs are unique; panel IDs are unique across all tabs.
4. Define shared dashboard parameters deliberately. A matching chart parameter
   name does not create a binding: map each panel's chart parameter to
   {param: dashboard_parameter} or a typed literal. Cover required chart
   parameters without defaults; check type, ranges and options against the chart.
5. Choose a vertical tab or a grid tab. Only grid tabs accept width, row_span
   and responsive panel fields. Use the guide's ranges and height formula,
   preserve panel reading order, and choose a compact card height when helpful.
6. Write dashboard-specific notes and update the topic README with its included
   charts, intended reading order and connection requirements. Add workspace
   connection declarations if needed; connection values stay on the user's device.
7. Run the tests and --validate-only command in AGENTS.md. When Facetra is
   available, preview shared parameters and both wide/compact layouts; otherwise
   report that visual/runtime checks remain unverified.

Report the dashboard path/ID, chart IDs, parameter bindings and validation result.
Creating content does not itself authorize publishing a catalog or merging a PR.
