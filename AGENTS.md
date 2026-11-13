# Agent instructions

## Project goal

Build a revisable 3D representation of the apartment shown in the supplied floor plan. Prioritize the architectural shell and room layout first. Furniture is a later phase unless the user requests a separate, revisable component. Blender integration is being explored, not yet established.

## Working from the floor plan

- Treat `assets/floor-plan.jpg` as a reference for topology, room adjacency, and visible features—not as a measured or scaled plan.
- Use `assets/references/README.md` to navigate the room-grouped interior visual references. Viewpoint descriptions are inferred from the images; do not treat decor, fixtures, finishes, or apparent proportions as confirmed apartment facts.
- The labeled spaces are bedroom (`Sovrum`), bathroom (`Badrum`), living room (`Vardagsrum`), kitchen (`Kök`), and hall (`Hall`).
- Preserve legible features such as windows, the entrance, built-in storage (`G`), kitchen appliance markings (`K` and `F`), and bathroom fixtures where the modeling scope includes them.
- Do not invent exact lengths, wall thicknesses, ceiling heights, or fixture dimensions. Ask for measurements when dimensional accuracy matters; otherwise make estimates clearly provisional and straightforward to update.
- Keep design assumptions and unresolved questions visible in the relevant documentation or model metadata. Do not silently turn an estimate into a project fact.

## Implementation practices

- The current modeling workflow uses Blender 5.3+ and `blender/apartment_model.py`; keep the source script reproducible and update the README when its workflow changes.
- Keep the architectural shell, fixtures, and future furniture separable so each can be revised independently.
- Prefer editable, reproducible source files over undocumented one-off generated output. Document the steps to open, modify, and regenerate deliverables once a toolchain exists.
- Keep changes focused on the requested task, and validate them with the relevant checks available in the repository.
- Update the README and any affected project guidance when the chosen modeling toolchain or workflow changes.
