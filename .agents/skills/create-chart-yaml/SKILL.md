---
name: create-chart-yaml
description: Create or edit a Facetra chart YAML in the Discover content repository, including sources, dataset SQL, parameters and native, value or ECharts rendering.
---

# Create a chart YAML

Create a portable chart in an existing workspace, or create a complete workspace
when the requested chart starts a new topic.

1. Read [AGENTS.md](../../../AGENTS.md) and the
   [workspace/parameter format](../../../docs/workspace-yaml.md). Identify the
   topic, data provenance, required fields/units and desired renderer. Inspect
   that workspace's manifest, README and existing chart IDs before writing.
2. Read the [chart format](../../../docs/chart-yaml.md). Choose the acquisition
   source, then describe transformations in dataset SQL and rendering in chart.
   The source/reference variants and renderer fields are exclusive; use only the
   fields documented for that variant.
3. Use [the CSV starter](../../../docs/starter/charts/sales.yaml) for a simple
   chart. For a new topic, copy the
   [complete starter](../../../docs/contributing.md#start-a-workspace).
   For ECharts, consult the binding table in the chart guide and
   [the business example](../../../workspaces/example/charts/Example/ECharts/example_echarts_business.yaml).
   Adapt IDs, titles, SQL and fields to the request; do not overwrite existing resources.
4. Save under workspaces/<topic>/charts/<optional-folders>/<chart-id>.yaml. Match metadata.id
   to the filename and chart.dataset to dataset.id. Put id/title/notes/tags in
   top-level metadata, separate from rendering. Keep data in that topic's
   data/ directory and references within the same workspace. Bind SQL values as
   $parameter and external references through with; do not interpolate SQL.
   Give parameters useful defaults so imported charts can run independently.
5. Add public/fictional data when needed, and document source, units and local
   connection setup in the topic README. Declare connection IDs/aliases in
   workspace.yaml when the workspace needs them. Never include connection values.
6. Run the tests and --validate-only command in AGENTS.md from the repository
   root. Fix errors with their file/field context. If Facetra is available,
   confirm output columns and rendering; otherwise state that runtime preview
   was not performed.

Report the chart path/ID, dependencies, connection requirements and validation
result. Creating content does not itself authorize publishing a catalog or merging a PR.
