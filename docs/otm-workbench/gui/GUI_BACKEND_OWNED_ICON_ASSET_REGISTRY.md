# GUI Backend-Owned Icon And Label Registry

**Status:** design decision
**Figma source:** Iconly V3.0 Free + Iconly Pro Community
**Figma file key:** `8h6mUDOqSXent0hqlSY7k7`

## 1. Decision

Navigation icons, module labels, action labels, and program display metadata
must be backend-owned.

The frontend may render approved icon components, but it must not decide module
identity, labels, icon family, icon variant, route visibility, or lifecycle
wording from local maps.

## 2. Figma Finding

The Iconly reference file has separate icon library pages:

```text
Library | Light
Library | Dark
```

The inspected naming convention is stable enough for a registry:

```text
Iconly/<family>/<style>/<icon name>
```

Examples found in both light and dark pages include:

```text
Iconly/Regular/Broken/Home
Iconly/Regular/Broken/Folder
Iconly/Regular/Broken/Document
Iconly/Regular/Broken/Chart
Iconly/Regular/Broken/Setting
Iconly/Regular/Broken/Upload
Iconly/Regular/Broken/Download
Iconly/Regular/Broken/Location
Iconly/Sharp/Bold/Work
Iconly/Sharp/Bulk/Activity
```

This makes Iconly a good candidate library for sidebar and module identity,
provided we store references and approved keys in the backend instead of
binding the frontend directly to Figma node IDs.

## 3. Backend Contract

Add or extend backend-owned UI metadata with these responsibilities:

```text
- module_id
- route_path
- label_key
- display_label
- description
- icon_key
- icon_family
- icon_variant
- icon_style
- icon_light_ref
- icon_dark_ref
- sort_order
- status
- required_capability
```

The existing `/api/v1/platform/navigation` contract should return these fields
after the registry is implemented. The frontend should render only what the
backend returns.

Recommended icon reference shape:

```json
{
  "icon_key": "catalog",
  "icon_family": "iconly",
  "icon_variant": "regular",
  "icon_style": "broken",
  "icon_name": "Folder",
  "light_ref": {
    "figma_file_key": "8h6mUDOqSXent0hqlSY7k7",
    "figma_page": "Library | Light",
    "figma_node_name": "Iconly/Regular/Broken/Folder"
  },
  "dark_ref": {
    "figma_file_key": "8h6mUDOqSXent0hqlSY7k7",
    "figma_page": "Library | Dark",
    "figma_node_name": "Iconly/Regular/Broken/Folder"
  },
  "fallback_icon_key": "folder"
}
```

## 4. Data Model Direction

The first implementation should prefer explicit registry tables over frontend
constants.

Candidate tables:

```text
ui_icon_assets
ui_program_labels
ui_navigation_items
```

If the current module registry already owns navigation, it can be extended
instead of duplicated. The important rule is that module identity and UI display
metadata are persisted and auditable.

`ui_icon_assets` should hold approved icon keys and references, not arbitrary
remote SVG execution.

`ui_program_labels` should hold display strings with locale and context support
so module labels can later move toward translation without a frontend deploy.

`ui_navigation_items` or the module registry should bind a module/program to its
label key, icon key, route, sort order, status, and required capability.

## 5. Frontend Boundary

The frontend owns rendering mechanics only:

```text
- choose light or dark asset variant from backend preference state
- map backend icon_key to an approved renderer or sanitized asset
- provide accessible names from backend labels
- fall back to a safe generic icon when an approved icon is missing
```

The frontend must not:

```text
- decide sidebar labels locally
- hardcode module icon identity in route components
- fetch arbitrary Figma assets at runtime
- execute unsanitized SVG or HTML from the database
- infer status labels or lifecycle wording locally
```

The current Lucide shell icons remain acceptable as fallback renderers until the
backend registry and asset export pipeline are implemented.

## 6. Security And QA Requirements

Icon assets must be treated as UI-controlled assets:

```text
- only approved icon families and icon keys are allowed
- SVGs must be sanitized before storage or serving
- Figma references are metadata, not runtime dependencies
- dark/light variants must be covered by visual QA
- missing icon keys must degrade to a generic accessible icon
- labels must be tested with long synthetic names
```

## 7. Implementation Slice

Recommended next slice:

```text
1. Add backend migration/model/seed data for UI icon and label registry.
2. Extend platform navigation response with icon_key and label_key metadata.
3. Update frontend sidebar/action rendering to consume backend icon_key.
4. Add tests proving module labels/icons come from backend payloads.
5. Add static guardrail blocking module-specific sidebar icon maps.
6. Update Linear with any module that still has hardcoded display metadata.
```

This can be implemented independently from module workflow work because it is a
platform contract.
