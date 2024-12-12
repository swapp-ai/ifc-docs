# Representing 2D Documentation in IFC

## IFC Schema Proposal

### [SWAPP.AI](https://swapp.ai), December 2024

## Introduction

This document proposes a new convention for representing architectural 2D documentation within an IFC 4.3 model,
leveraging existing IFC classes and relationships without introducing new entity definitions. The approach is intended
to be both orthogonal and complementary to the existing IFC model, ensuring that new documentation objects can coexist
seamlessly with native BIM elements.

The primary goal is to achieve _semantic_ enrichment of 2D drawing and annotation elements, enabling drawing automation
and interoperability. Rather than merely exporting visual artifacts such as PDFs or SVGs, this proposal aims to
incorporate machine-readable documentation into the IFC model, allowing downstream tools to interpret, modify, or
regenerate the 2D documentation as needed.

The proposal draws inspiration from BIM tools (e.g., Revit) and open-source IFC workflows (e.g., BlenderBIM and Bonsai
projects), and is informed by SWAPP.AI’s practical experience with BIM interoperability.

### Caveats

This is an early draft intended for public review and feedback. While the conventions described here are general, the
examples and certain design choices are influenced by SWAPP.AI’s specific interoperability needs. Subsequent revisions
may refine or expand upon the concepts introduced.

## General Principles

**Key Idea:** Represent documentation objects as structured IFC elements using a combination of `IfcGroup`,
`IfcAnnotation`, and existing IFC relationships (`IfcRelAggregates`, `IfcRelAssignsToProduct`, etc.). The resulting
hierarchy allows for a rich representation of sheets, views, annotations, dimension lines, and references, all embedded
within a standard IFC dataset.

**Hierarchy Overview:**

```
IfcProject
   └── DocumentSet (represented as IfcGroup, 1..*)
       └── Sheet (IfcAnnotation, 1..*)
           └── ViewPort (IfcAnnotation, 1..*)
               └── View (IfcAnnotation, 1..1)
                   └── Annotation elements (IfcAnnotation, 1..*)
                       └── Nested Annotation elements (IfcAnnotation, 0..*)
                       ...
```

**Key Points:**

- Hierarchical relationships are represented using `IfcRelAggregates`.
- The top-level `DocumentSet` is an `IfcGroup`. All subordinate items (Sheet, ViewPort, View, Annotation elements) are
  represented as `IfcAnnotation` entities.
- Geometries follow IFC conventions. Each annotation’s geometry is defined in a suitable coordinate system, with
  transforms (`IfcLocalPlacement` and `IfcAxis2Placement3D`) capturing translation, rotation, and possibly uniform
  scaling relative to its parent.
- Scaling between world coordinates and sheet (paper) units is explicitly modeled at the `View` level.
- Elements may carry custom `IfcPropertySet` attributes for interoperability, metadata, and reference links to original
  BIM elements.

## Proposed Hierarchy and Entities

### DocumentSet (`IfcGroup`)

- **Definition:** An `IfcGroup` with `.Name = "DocumentSet"` that aggregates multiple `Sheet` entities.

- **Purpose:** Serves as a container for all sheets in the project. There may be multiple `DocumentSet` groups if
  needed.
- **Placement in IFC:** The `DocumentSet` can coexist alongside standard site/building/facility structures. Use
  `IfcRelAssignsToGroup` to assign sheets to the document set.

### Sheet (`IfcAnnotation`)

- **Definition:** Represents a single sheet of documentation (e.g., a drawing sheet).
- **Geometry:** Typically includes the sheet boundary, title block, and any other sheet-level graphics.
- **Relationships:** Each Sheet aggregates one or more `ViewPort` entities via `IfcRelAggregates`.

### ViewPort (`IfcAnnotation`)

- **Definition:** A `ViewPort` is a "window" or placeholder on the sheet where a `View` is placed.
- **Geometry:** Typically a rectangular boundary indicating where the view content appears.


- **Relationships:** Each `ViewPort` aggregates exactly one `View`.

### View (`IfcAnnotation`)

- **Definition:** Represents a 2D depiction of part of the model (e.g., a floor plan, elevation, section, detail view).
- **Geometry & Coordinates:**
    - The `View` content is typically defined in world coordinates.
    - To place the view onto the sheet, a uniform scaling is applied relative to the `ViewPort`. This scaling accounts
      for:

    1. Unit conversion from the view's world units (e.g. meters or feet) to the sheet's paper units (e.g. mm)
    2. The view scale-factor (e.g. 1:100 or 1:48).
- **Aggregation:** The `View` aggregates all view-level annotation elements and model elements relevant to that view.
  These may include:
    - Model-based annotations (e.g., walls, doors, windows displayed as 2D outlines)
    - Documentation-only elements (e.g., dimension lines, tags, grid lines)

**Rationale:** Each `View` serves as the root element for its 2D representation. By nesting all related elements under
it, the representation remains modular and independent. Actual model relationships (e.g., walls, doors) can be
cross-referenced via `IfcRelAssignsToProduct`.

Note that this View representation deviates from the way Bonsai represents views and sheets. [^bonsai]
[^bonsai]: Bonsai uses external SVG files for the drawings and an `IfcGroup` for the view.

### View Elements (Annotations)

- **Definition:** All view elements (walls, doors, tags, dimensions, etc.) are represented as `IfcAnnotation` entities.
- **Hierarchy & Nesting:**
    - Elements that logically belong to or are derived from other elements may be nested. For example:
        - A room tag could be a nested annotation under the `ViewSpace` (representing a room).
        - A dimension line segment could nest a label annotation.
        - References (points, lines) used for dimensioning may be nested under the element they reference (e.g., wall
          layer reference lines).

### Relations

- **Structural Aggregation:** `IfcRelAggregates` defines parent-child hierarchies (e.g., DocumentSet → Sheet →
  ViewPort → View → Annotation).
- **Cross-References:** `IfcRelAssignsToProduct` can link a 2D element (e.g., a wall annotation in the view) back to the
  corresponding 3D `IfcWall` in the main model. This ensures semantic integrity between the drawn element and its
  originating BIM entity.
- **Dimensional or Reference Relations:** Additional `IfcRelAssignsToProduct` or custom properties may define
  relationships between annotation elements and hidden reference geometry.

## Specialized Annotation Types

#### Dimension Lines

As mentioned, these are also `IfcAnnotation`s.  
We distinguish a simple hierarchy:

```
    DimensionLine 
    └── DimensionLineSegment (1..*)
        └── Label (0..1)

```

Each dimension line consists of a string of one or more segments, each with its own label.  
The dimension line itself may also have its own (unified) geometry.

It is expected that the length of the linear geometry of the `DimensionLineSegment` (in world units) would be
the dimension measured (up to local unit and scaling transforms).

#### Reference Elements

Maintaining a connection or relation between a view element and a model element, may be done in several ways.
If the model element exists in the IFC itself, one may use `IfcRelAssignsToProduct` to connect the two.
For BIM interop, we can also store custom attributes with the source element reference IDs which may be used to
re-import the IFC into the originating BIM tool.

However, some view elements require additional, non-*meta*data, _geometric_ information.
For example, wall layers and faces, door opening location, etc. This data is essential for view processing automation,
although it may not directly appear in the final drawing.

Reference elements provide geometric cues—like core boundaries or opening edges—that guide accurate dimensioning and
coordination with model elements. These references remain invisible in final outputs but deliver essential intelligence
for downstream processing.

For example, accurate dimension line placement and BIM tool interop, requires the dimension line element to connect to
a particular reference point, line or plane within the measured wall element[s]. This will allow correct and accurate
measurements, regardless of whether the dimension line endpoints are visible in the final PDF resolution.

Different BIM tools use different ways of representing geometric element reference. In fact, each edge of each geometry
shape could sometimes be a reference. Thus, exporting references should be done on a use case basis, as needed by the
view processing tool.

In this proposal, reference elements are represented as `IfcAnnotion`s with relevant geometries, nested under their
relevant element. They will be given custom `subtype` attributes to indicate their relevance.  
Elements that need to relate to them (e.g. a dimension line connects between two (wall) references will use the
`IfcRelAssignsToProduct` relation.

## Schema Properties

Every documentation object must have a `DocumentationObjectProperties` property set. This table defines the required
properties and their `type` (and `subtype` where applicable):

| Element                | key       | Value                                                                                                             |
|------------------------|-----------|-------------------------------------------------------------------------------------------------------------------|
| DocumentSet            | `type`    | `"DocumentSet"`                                                                                                   |
|                        |           |                                                                                                                   |
| Sheet                  | `type`    | `"Sheet"`                                                                                                         |
|                        |           |                                                                                                                   |
| View Port              | `type`    | `"ViewPort"`                                                                                                      |
|                        |           |                                                                                                                   |
| View                   | `type`    | `"View"`                                                                                                          |
|                        |           |                                                                                                                   |
| Room/Space             | `type`    | `"ViewSpace"`                                                                                                     |
|                        |           |                                                                                                                   |
| Wall                   | `type`    | `"ElementInView"`                                                                                                 |
|                        | `subtype` | `"wall"`                                                                                                          |
|                        |           |                                                                                                                   |
| Door                   | `type`    | `"ElementInView"`                                                                                                 |
|                        | `subtype` | `"door"`                                                                                                          |
|                        |           |                                                                                                                   |
| Window                 | `type`    | `"ElementInView"`                                                                                                 |
|                        | `subtype` | `"window"`                                                                                                        |
|                        |           |                                                                                                                   |
| Floor                  | `type`    | `"ElementInView"`                                                                                                 |
|                        | `subtype` | `"floor"`                                                                                                         |
|                        |           |                                                                                                                   |
| Grid Line              | `type`    | `"GridLine"`                                                                                                      |
|                        | `subtype` | `"grid_line"`                                                                                                     |
|                        |           |                                                                                                                   |
| Reference              | `type`    | `"Reference"`                                                                                                     |
|                        | `subtype` | `"EXTERIOR"`, `"INTERIOR"`,  <br/>`"CORE_EXTERIOR"`, `"CORE_INTERIOR"`,  <br/>`"OPENING"`,`"LINEAR"`, `"SURFACE"` |
|                        |           |                                                                                                                   |
| Tag                    | `type`    | `"Annotation"`                                                                                                    |
|                        | `subtype` | `"wall_tag"` `"door_tag"` `"window_tag"` `"room_tag"` `"railing_tag"` ...                                         |
|                        |           |                                                                                                                   |
| Dimension Line         | `type`    | `"DimensionLine"`                                                                                                 |
|                        |           |                                                                                                                   |
| Dimension Line Segment | `type`    | `"DimensionLineSegment"`                                                                                          |
|                        |           |                                                                                                                   |
| Label                  | `type`    | `"Label"`                                                                                                         |
|                        |           |                                                                                                                   |
| View Marker            | `type`    | `"ViewMarker"`                                                                                                    |
|                        | `subtype` | `"cropping_view_marker"`,`"view_reference"`,`"elevation_view_marker"`...                                          |
|                        |           |                                                                                                                   |
| Other Annotation       | `type`    | `"Annotation"`                                                                                                    |
|                        | `subtype` | `"text_note"`, `"matchline"` ...                                                                                  |

# Additional Notes

## Examples

Refer to the `examples` folder for scripts illustrating how to produce IFC files consistent with these principles.

## Styling

This proposal focuses on semantics rather than presentation. Although `IfcPresentationStyleAssignment` and related
mechanisms exist, styling is optional. The intent is to ensure that the underlying 2D documentation objects remain

meaningful and adaptable, not necessarily to replicate a particular PDF output appearance.

## Future Work

As this is an early draft, it may not address all conceivable documentation scenarios. Future enhancements include:

- Support for multiple named representations, potentially aligning with existing IFC constructs.
- Introducing templating and instancing strategies to minimize redundancy, improving efficiency when multiple identical
  elements appear across documents.



