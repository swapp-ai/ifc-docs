"""
generate an ifc file with base structure only --
no geometries.
"""


import logging
import math
import pathlib
import time
import uuid

import ifcopenshell
import ifcopenshell.guid
import ifcopenshell.validate


def new_host_guid() -> str:
    return ifcopenshell.guid.compress(uuid.uuid1().hex)


def new_random_guid() -> str:
    return ifcopenshell.guid.compress(uuid.uuid4().hex)


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
    owner_hist.CreationDate = int(time.time())

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




def example1() -> ifcopenshell.file:
    # set logging to debug
    logging.root.setLevel(logging.DEBUG)

    # initialize ifc file:
    ifc_file = ifcopenshell.file(schema='IFC4')
    owner_hist = add_owner(ifc_file)
    unit_assignment = add_units(ifc_file)
    geom_context = add_default_geometry_context(ifc_file)
    project = add_project(ifc_file, owner_hist, unit_assignment, geom_context)

    # site details (ignored for documentation purposes)
    site = ifc_file.createIfcSite()
    site.GlobalId = new_host_guid()

    # document set
    docset = ifc_file.createIfcSite()
    docset.GlobalId = new_host_guid()
    docset.Name = 'DocumentSet'

    # connect "roots" of project
    ifc_file.create_entity(
        'IfcRelAggregates',
        GlobalId=new_host_guid(),
        RelatingObject=project,
        RelatedObjects=[site, docset]
    )

    # sheet1 |> viewport1 |> view1
    sheet1 = ifc_file.createIfcAnnotation()
    sheet1.GlobalId = new_host_guid()
    sheet1.Name = 'Sheet'

    viewport1 = ifc_file.createIfcAnnotation()
    viewport1.GlobalId = new_host_guid()
    viewport1.Name = 'ViewPort'

    ifc_file.create_entity(
        'IfcRelAggregates',
        GlobalId=new_host_guid(),
        RelatingObject=sheet1,
        RelatedObjects=[viewport1]
    )

    view1 = ifc_file.createIfcAnnotation()
    view1.GlobalId = new_host_guid()
    view1.Name = 'View'

    ifc_file.create_entity(
        'IfcRelAggregates',
        GlobalId=new_host_guid(),
        RelatingObject=viewport1,
        RelatedObjects=[view1]
    )

    # sheet2 |> viewport2 |> view2[a,b]
    sheet2 = ifc_file.createIfcAnnotation()
    sheet2.GlobalId = new_host_guid()
    sheet2.Name = 'Sheet'

    viewport2a = ifc_file.createIfcAnnotation()
    viewport2a.GlobalId = new_host_guid()
    viewport2a.Name = 'ViewPort'

    view2a = ifc_file.createIfcAnnotation()
    view2a.GlobalId = new_host_guid()
    view2a.Name = 'View'

    ifc_file.create_entity(
        'IfcRelAggregates',
        GlobalId=new_host_guid(),
        RelatingObject=viewport2a,
        RelatedObjects=[view2a]
    )

    viewport2b = ifc_file.createIfcAnnotation()
    viewport2b.GlobalId = new_host_guid()
    viewport2b.Name = 'ViewPort'

    view2b = ifc_file.createIfcAnnotation()
    view2b.GlobalId = new_host_guid()
    view2b.Name = 'View'

    ifc_file.create_entity(
        'IfcRelAggregates',
        GlobalId=new_host_guid(),
        RelatingObject=viewport2b,
        RelatedObjects=[view2b]
    )

    ifc_file.create_entity(
        'IfcRelAggregates',
        GlobalId=new_host_guid(),
        RelatingObject=sheet2,
        RelatedObjects=[viewport2a, viewport2b]
    )

    ifc_file.create_entity(
        'IfcRelAggregates',
        GlobalId=new_host_guid(),
        RelatingObject=docset,
        RelatedObjects=[sheet1, sheet2]
    )

    return ifc_file


def _main():
    ifc_file = example1()
    ifc_file = ifcopenshell.file.from_string(ifc_file.to_string())
    ifcopenshell.validate.validate(
        ifc_file,
        logger=logging.root,
        express_rules=True
    )
    ifc_file.write('example1.ifc')


if __name__ == '__main__':
    _main()
