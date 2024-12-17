"""
generate an ifc file with base structure including basic geometries.
"""

import logging
import math
import pathlib
import random
import time
import uuid
from dataclasses import dataclass

import ifcopenshell
import ifcopenshell.guid
import ifcopenshell.validate


@dataclass
class GuidGenerator:
    seed: int = 42

    def __post_init__(self) -> None:
        self._random_device = random.Random()
        self._random_device.seed(self.seed)

    def _next_consistent_uuid_seed(self) -> int:
        return self._random_device.getrandbits(128)

    def new_random_uuid1_guid(self) -> str:
        return ifcopenshell.guid.compress(uuid.uuid1().hex)

    def new_consistent_uuid1_guid(self) -> str:
        return ifcopenshell.guid.compress(uuid.UUID(int=self._next_consistent_uuid_seed(), version=1).hex)

    def new_random_uuid4_guid(self) -> str:
        return ifcopenshell.guid.compress(uuid.uuid4().hex)

    def new_consistent_uuid4_guid(self) -> str:
        return ifcopenshell.guid.compress(uuid.UUID(int=self._next_consistent_uuid_seed(), version=4).hex)


new_host_guid = GuidGenerator().new_consistent_uuid1_guid


def add_owner(ifc_file: ifcopenshell.file) -> ifcopenshell.entity_instance:
    # ifc organization
    org = ifc_file.createIfcOrganization()
    org.Name = 'SWAPP.ai'

    # ifc application
    app = ifc_file.createIfcApplication()
    app.ApplicationDeveloper = org
    app.Version = '0.1.0'
    app.ApplicationFullName = 'IFC Documentation Examples'
    app.ApplicationIdentifier = 'IFC Documentation Example'

    # ifc owner
    author = ifc_file.createIfcPerson()
    author.GivenName = 'Example'

    # ifc owner and organization
    author_and_org = ifc_file.createIfcPersonAndOrganization()
    author_and_org.ThePerson = author
    author_and_org.TheOrganization = org

    # owner history
    owner_hist = ifc_file.createIfcOwnerHistory()
    owner_hist.OwningUser = author_and_org
    owner_hist.OwningApplication = app
    owner_hist.CreationDate = int(time.mktime((2025, 1, 1, 0, 0, 0, 0, 0, 0)))

    return owner_hist


def add_units(ifc_file: ifcopenshell.file) -> ifcopenshell.entity_instance:
    # ifc units (metric)

    ## length
    length_unit = ifc_file.createIfcSIUnit()
    length_unit.UnitType = "LENGTHUNIT"
    length_unit.Name = "METRE"

    ## area
    area_unit = ifc_file.createIfcSIUnit()
    area_unit.UnitType = "AREAUNIT"
    area_unit.Name = "SQUARE_METRE"

    ## volume
    volume_unit = ifc_file.createIfcSIUnit()
    volume_unit.UnitType = "VOLUMEUNIT"
    volume_unit.Name = "CUBIC_METRE"

    ## plane
    plane_angle_unit = ifc_file.createIfcSIUnit()
    plane_angle_unit.UnitType = "PLANEANGLEUNIT"
    plane_angle_unit.Name = "RADIAN"

    ## angle
    angle_unit = ifc_file.createIfcMeasureWithUnit()
    angle_unit.UnitComponent = plane_angle_unit
    angle_unit.ValueComponent = ifc_file.createIfcPlaneAngleMeasure(math.pi / 180)

    ## convert base units
    convert_base_unit = ifc_file.createIfcConversionBasedUnit()
    convert_base_unit.Dimensions = ifc_file.createIfcDimensionalExponents(0, 0, 0, 0, 0, 0, 0)
    convert_base_unit.UnitType = "PLANEANGLEUNIT"
    convert_base_unit.Name = "DEGREE"
    convert_base_unit.ConversionFactor = angle_unit

    ## unit assignment
    unit_assignment = ifc_file.createIfcUnitAssignment([length_unit, area_unit, volume_unit, convert_base_unit])

    return unit_assignment


def add_default_geometry_context(ifc_file: ifcopenshell.file) -> ifcopenshell.entity_instance:
    # ifc geometries

    ## points of interest
    o = 0., 0., 0.
    x = 1., 0., 0.
    z = 0., 0., 1.

    ## axes
    xaxis = ifc_file.createIfcDirection(x)
    zaxis = ifc_file.createIfcDirection(z)

    ## origin
    origin = ifc_file.createIfcCartesianPoint(o)

    ## coordinate system (top-down view along z-axis)
    world_coordinate_system = ifc_file.createIfcAxis2Placement3D()
    world_coordinate_system.Location = origin
    world_coordinate_system.Axis = zaxis
    world_coordinate_system.RefDirection = xaxis

    ## geometry context
    geom_context = ifc_file.createIfcGeometricRepresentationContext()
    geom_context.ContextType = 'Model'
    geom_context.CoordinateSpaceDimension = 3
    geom_context.Precision = 1.e-05
    geom_context.WorldCoordinateSystem = world_coordinate_system

    return geom_context


def add_project(ifc_file: ifcopenshell.file,
                owner_hist: ifcopenshell.entity_instance,
                unit_assignment: ifcopenshell.entity_instance,
                geom_context: ifcopenshell.entity_instance
                ) -> ifcopenshell.entity_instance:
    # project details
    project = ifc_file.createIfcProject(new_host_guid())
    project.OwnerHistory = owner_hist
    project.Name = pathlib.Path(__file__).name.capitalize()
    project.RepresentationContexts = [geom_context]
    project.UnitsInContext = unit_assignment
    return project


def add_properties(ifc_file, element, properties_dict, property_set_name="DocumentationObjectProperties"):
    """
    Adds a property set with multiple key-value pairs to the given IFC element.

    Args:
        ifc_file: The IFC file object.
        element: The IFC element to which the property set will be attached.
        properties_dict: A dictionary containing key-value pairs.
        property_set_name: The name of the property set.
    """
    property_list = []

    for key, value in properties_dict.items():
        # Determine the appropriate IfcValue subtype
        if isinstance(value, str):
            value_instance = ifc_file.create_entity("IfcText", value)
        elif isinstance(value, int):
            value_instance = ifc_file.create_entity("IfcInteger", value)
        elif isinstance(value, float):
            value_instance = ifc_file.create_entity("IfcReal", value)
        else:
            raise ValueError(f"Unsupported value type: {type(value)}")

        # Create an IfcPropertySingleValue for each key-value pair
        property_single_value = ifc_file.createIfcPropertySingleValue(
            Name=key,
            Description=None,
            NominalValue=value_instance,
            Unit=None,
        )
        property_list.append(property_single_value)

    # Create the property set with all properties
    property_set = ifc_file.createIfcPropertySet(
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=None,
        Name=property_set_name,
        Description=None,
        HasProperties=property_list,
    )

    # Create the relationship between the element and the property set
    ifc_file.createIfcRelDefinesByProperties(
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=None,
        Name=None,
        Description=None,
        RelatedObjects=[element],
        RelatingPropertyDefinition=property_set,
    )


def create_polygon_representation(ifc_file, geometric_context, coords, origin=(0, 0, 0)):
    """
    Create a polygon representation for an IfcAnnotation.

    Args:
        ifc_file: The IFC file object.
        geometric_context: The geometric context (IfcGeometricRepresentationContext).
        coords: List of coordinate tuples defining the polygon (e.g., [(x1, y1), (x2, y2), ...]).

    Returns:
        tuple: (IfcProductDefinitionShape, IfcLocalPlacement)
    """
    # Create the polyline for the square
    points = [ifc_file.createIfcCartesianPoint(coord) for coord in coords]
    polyline = ifc_file.createIfcPolyline(points)
    # Create and return the shape representation
    representation = ifc_file.createIfcShapeRepresentation(
        ContextOfItems=geometric_context,
        RepresentationIdentifier="Annotation2D",
        RepresentationType="Curve2D",
        Items=[polyline],
    )

    # Assign the representation to the IfcAnnotation
    product_definition_shape = ifc_file.createIfcProductDefinitionShape(
        Representations=[representation]
    )

    # Create and assign the local placement
    origin_pt = ifc_file.createIfcCartesianPoint(tuple(float(v) for v in origin))
    axis2placement = ifc_file.createIfcAxis2Placement3D(origin_pt)
    local_placement = ifc_file.createIfcLocalPlacement(RelativePlacement=axis2placement)

    return product_definition_shape, local_placement


def create_square_representation(ifc_file, geometric_context, size=20, origin=(0, 0, 0)):
    # Define the corners of the square
    half_size = size / 2
    coords = [
        (-half_size, -half_size),
        (half_size, -half_size),
        (half_size, half_size),
        (-half_size, half_size),
        (-half_size, -half_size),  # Close the loop
    ]
    return create_polygon_representation(ifc_file, geometric_context, coords, origin=origin)


def example2() -> ifcopenshell.file:
    # set logging to debug
    logging.root.setLevel(logging.DEBUG)

    # initialize ifc file:
    ifc_file = ifcopenshell.file(schema='IFC4')
    ifc_file.header.file_name.time_stamp = "20250101T000000"

    owner_hist = add_owner(ifc_file)
    unit_assignment = add_units(ifc_file)
    geom_context = add_default_geometry_context(ifc_file)
    project = add_project(ifc_file, owner_hist, unit_assignment, geom_context)

    # site details (ignored for documentation purposes)
    site = ifc_file.createIfcSite()
    site.GlobalId = new_host_guid()

    # document set
    docset = ifc_file.createIfcAnnotation()
    docset.GlobalId = new_host_guid()
    docset.Name = 'My Document Set'
    add_properties(ifc_file, docset, {"type": "DocumentSet"})

    # connect "roots" of project
    ifc_file.create_entity(
        'IfcRelAggregates',
        GlobalId=new_host_guid(),
        RelatingObject=project,
        RelatedObjects=[site, docset]
    )

    # sheet |> viewport2 |> view2[a,b]
    sheet = ifc_file.createIfcAnnotation()
    sheet.GlobalId = new_host_guid()
    sheet.Name = 'Sample Sheet'
    sheet.Representation, sheet.ObjectPlacement = create_square_representation(ifc_file, geom_context, size=30)
    add_properties(ifc_file, sheet, {"type": "Sheet"})

    viewport1 = ifc_file.createIfcAnnotation()
    viewport1.GlobalId = new_host_guid()
    viewport1.Name = 'ViewPort 1'
    add_properties(ifc_file, viewport1, {"type": "ViewPort"})

    view1 = ifc_file.createIfcAnnotation()
    view1.GlobalId = new_host_guid()
    view1.Name = 'View: 10x10 square.'
    add_properties(ifc_file, view1, {"type": "View"})

    # Create the shape representation for the square
    view1.Representation, view1.ObjectPlacement = create_square_representation(ifc_file, geom_context,
                                                                               size=10,
                                                                               origin=(-5, 0, 0))

    ifc_file.create_entity(
        'IfcRelAggregates',
        GlobalId=new_host_guid(),
        RelatingObject=viewport1,
        RelatedObjects=[view1]
    )

    viewport2 = ifc_file.createIfcAnnotation()
    viewport2.GlobalId = new_host_guid()
    viewport2.Name = 'ViewPort 2'
    add_properties(ifc_file, viewport2, {"type": "ViewPort"})

    view2 = ifc_file.createIfcAnnotation()
    view2.GlobalId = new_host_guid()
    view2.Name = 'View: 8x8 square'
    add_properties(ifc_file, view2, {"type": "View"})
    view2.Representation, view2.ObjectPlacement = create_square_representation(ifc_file, geom_context,
                                                                               size=8,
                                                                               origin=(6, 0, 0))

    ifc_file.create_entity(
        'IfcRelAggregates',
        GlobalId=new_host_guid(),
        RelatingObject=viewport2,
        RelatedObjects=[view2]
    )

    ifc_file.create_entity(
        'IfcRelAggregates',
        GlobalId=new_host_guid(),
        RelatingObject=sheet,
        RelatedObjects=[viewport1, viewport2]
    )

    ifc_file.create_entity(
        'IfcRelAggregates',
        GlobalId=new_host_guid(),
        RelatingObject=docset,
        RelatedObjects=[sheet]
    )

    return ifc_file


def _main():
    ifc_file = example2()
    ifc_file = ifcopenshell.file.from_string(ifc_file.to_string())
    ifcopenshell.validate.validate(
        ifc_file,
        logger=logging.root,
        express_rules=True
    )
    ifc_file.write('example2.ifc')


if __name__ == '__main__':
    _main()
