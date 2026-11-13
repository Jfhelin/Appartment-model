# Apartment Model

This project creates a revisable three-dimensional apartment model from the supplied floor plan. The architectural shell is being built first, with fixtures and built-ins kept separate so they can be refined independently. The current modeling workflow uses Blender 5.3 and the editable Python source in [`blender/apartment_model.py`](blender/apartment_model.py).

## Apartment layout

The supplied Swedish floor plan shows:

- **Sovrum** — bedroom
- **Badrum** — bathroom, with a shower, sink, toilet, and washing machine marked
- **Vardagsrum** — living room
- **Kök** — kitchen
- **Hall** — entrance hall

The drawing also marks built-in storage (`G`), kitchen appliances (`K` and `F`), windows, and the entrance. Preserve these features in the architectural model where they are legible.

## Reference and accuracy

Use [`assets/floor-plan.jpg`](assets/floor-plan.jpg) as the source for room arrangement and visible features. Its note says the plan is **not to scale** and that deviations may occur. No verified measurements, wall heights, or construction details are provided yet.

Do not present estimates inferred from the image as measured dimensions. Keep assumptions explicit and easy to revise; use verified measurements when they become available. Until then, any geometry based on proportions is a provisional visualization, not a dimensionally accurate or construction-ready model.

The first Blender blockout uses the supplied **53 m²** area and **2.40 m** height. The 2.40 m value is interpreted as floor-to-ceiling/wall height. The image proportions are scaled to make the modeled clear floor area approximately 53 m²; exterior dimensions, wall thicknesses, room proportions, opening sizes and heights, and fixture sizes remain estimates. Bathroom fixture positions follow the plan symbols, while the supplied bathroom photo informs their forms and orientation; fixtures are aligned flush to modeled interior wall faces. Kitchen photos inform the wall-connected casework, sink, oven/hob, and cabinets; K/F remain separate refrigerator/freezer appliances at the plan's marked location. No dining table or freestanding furniture is included. These assumptions are also stored as scene custom properties.

![Apartment floor plan](assets/floor-plan.jpg)

## Interior visual references

The supplied interior images are stored under [`assets/references/`](assets/references/), grouped by the room or area they primarily show. Start with the [reference catalog](assets/references/README.md) for inferred viewpoints, visible features, and cross-room clues.

These images are visual guidance, not verified survey photographs or dimensional evidence. Their provenance and consistency with the exact apartment have not been established. Use the floor plan for room adjacency and openings; confirm uncertain details and all dimensions before treating them as model facts.

## Project direction

1. Establish the apartment shell and room layout.
2. Refine openings, built-ins, and visible fixtures using confirmed information.
3. Add furniture as a later, separate layer of work.
4. Refine the Blender shell and replace provisional dimensions with measurements when available.

## Wardrobe component

The L-shaped wardrobe is a separate, movable collection, not part of the apartment shell. Its editable source is [`blender/wardrobe_component.py`](blender/wardrobe_component.py). In `apartment.blend`, select **Wardrobe - Move as one** in the Outliner and move it as a single unit; it starts beside the apartment model. To use it in another project or session, use **File > Append** and select the `Wardrobe Component` collection from `apartment.blend`, or run the component script in the target Blender scene.

The model uses the confirmed 1.50 m main run (three nominal 0.50 m bays), 0.35 m shelf depth, 0.60 m return, and 0.50 m mirror section. The 2.10 m height and 0.018 m panel thickness are explicitly provisional and editable at the top of the source script. The main run's 1.50 m width includes its dividers, so clear shelf openings are slightly narrower than 0.50 m. The reference photos guide the open-shelf and lower-drawer arrangement; they do not establish construction details. To rebuild or adjust the component, open `apartment.blend` in Blender 5.3+, run `blender/wardrobe_component.py` in the Scripting workspace, then save the project. Running the script replaces only the wardrobe collection.

## Getting started

Open `apartment.blend` in Blender 5.3 or later to inspect the current model. To regenerate or revise the blockout, open `blender/apartment_model.py` in Blender's Scripting workspace and choose **Run Script**; save the result as `apartment.blend` in the repository root. The script replaces only its named provisional model collection, retains the camera and light, and configures them for a plan view. Edit the traced plan coordinates and clearly marked assumptions in the script as better measurements become available. This is a visualization workflow, not construction documentation.

## Contributing

See [`AGENTS.md`](AGENTS.md) for project-specific guidance for AI coding agents and contributors.
