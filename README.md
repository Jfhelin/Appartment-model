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

## Project direction

1. Establish the apartment shell and room layout.
2. Refine openings, built-ins, and visible fixtures using confirmed information.
3. Add furniture as a later, separate layer of work.
4. Refine the Blender shell and replace provisional dimensions with measurements when available.

## Getting started

Open `apartment.blend` in Blender 5.3 or later to inspect the current model. To regenerate or revise the blockout, open `blender/apartment_model.py` in Blender's Scripting workspace and choose **Run Script**; save the result as `apartment.blend` in the repository root. The script replaces only its named provisional model collection, retains the camera and light, and configures them for a plan view. Edit the traced plan coordinates and clearly marked assumptions in the script as better measurements become available. This is a visualization workflow, not construction documentation.

## Contributing

See [`AGENTS.md`](AGENTS.md) for project-specific guidance for AI coding agents and contributors.
