# ./ceda_storage_pot.py
# PyXB bindings for NM:e92452c8d3e28a9e27abfc9994d2007779e7f4c9
# Generated 2012-04-23 13:45:09.861750 by PyXB version 1.1.3
# Namespace AbsentNamespace0

import pyxb
import pyxb.binding
import pyxb.binding.saxer
import StringIO
import pyxb.utils.utility
import pyxb.utils.domutils
import sys

# Unique identifier for bindings created at the same time
_GenerationUID = pyxb.utils.utility.UniqueIdentifier('urn:uuid:294b7112-8d42-11e1-aa50-0024d673e48e')

# Import bindings for namespaces imported into schema
import pyxb.binding.datatypes

Namespace = pyxb.namespace.CreateAbsentNamespace()
Namespace.configureCategories(['typeBinding', 'elementBinding'])
ModuleRecord = Namespace.lookupModuleRecordByUID(_GenerationUID, create_if_missing=True)
ModuleRecord._setModule(sys.modules[__name__])

def CreateFromDocument (xml_text, default_namespace=None, location_base=None):
    """Parse the given XML and use the document element to create a Python instance."""
    if pyxb.XMLStyle_saxer != pyxb._XMLStyle:
        dom = pyxb.utils.domutils.StringToDOM(xml_text)
        return CreateFromDOM(dom.documentElement)
    saxer = pyxb.binding.saxer.make_parser(fallback_namespace=Namespace.fallbackNamespace(), location_base=location_base)
    handler = saxer.getContentHandler()
    saxer.parse(StringIO.StringIO(xml_text))
    instance = handler.rootObject()
    return instance

def CreateFromDOM (node, default_namespace=None):
    """Create a Python instance from the given DOM node.
    The node tag must correspond to an element declaration in this module.

    @deprecated: Forcing use of DOM interface is unnecessary; use L{CreateFromDocument}."""
    if default_namespace is None:
        default_namespace = Namespace.fallbackNamespace()
    return pyxb.binding.basis.element.AnyCreateFromDOM(node, _fallback_namespace=default_namespace)


# Complex type CTD_ANON with content type ELEMENT_ONLY
class CTD_ANON (pyxb.binding.basis.complexTypeDefinition):
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = None
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element aggregation uses Python identifier aggregation
    __aggregation = pyxb.binding.content.ElementUse(pyxb.namespace.ExpandedName(None, u'aggregation'), 'aggregation', '__AbsentNamespace0_CTD_ANON_aggregation', True)

    
    aggregation = property(__aggregation.value, __aggregation.set, None, None)


    _ElementMap = {
        __aggregation.name() : __aggregation
    }
    _AttributeMap = {
        
    }



# Complex type CTD_ANON_ with content type ELEMENT_ONLY
class CTD_ANON_ (pyxb.binding.basis.complexTypeDefinition):
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = None
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element file_id uses Python identifier file_id
    __file_id = pyxb.binding.content.ElementUse(pyxb.namespace.ExpandedName(None, u'file_id'), 'file_id', '__AbsentNamespace0_CTD_ANON__file_id', False)

    
    file_id = property(__file_id.value, __file_id.set, None, None)

    
    # Element file_name uses Python identifier file_name
    __file_name = pyxb.binding.content.ElementUse(pyxb.namespace.ExpandedName(None, u'file_name'), 'file_name', '__AbsentNamespace0_CTD_ANON__file_name', False)

    
    file_name = property(__file_name.value, __file_name.set, None, None)

    
    # Element file_size uses Python identifier file_size
    __file_size = pyxb.binding.content.ElementUse(pyxb.namespace.ExpandedName(None, u'file_size'), 'file_size', '__AbsentNamespace0_CTD_ANON__file_size', False)

    
    file_size = property(__file_size.value, __file_size.set, None, None)


    _ElementMap = {
        __file_id.name() : __file_id,
        __file_name.name() : __file_name,
        __file_size.name() : __file_size
    }
    _AttributeMap = {
        
    }



# Complex type CTD_ANON_2 with content type ELEMENT_ONLY
class CTD_ANON_2 (pyxb.binding.basis.complexTypeDefinition):
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = None
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element storagedCurrentStatus uses Python identifier storagedCurrentStatus
    __storagedCurrentStatus = pyxb.binding.content.ElementUse(pyxb.namespace.ExpandedName(None, u'storagedCurrentStatus'), 'storagedCurrentStatus', '__AbsentNamespace0_CTD_ANON_2_storagedCurrentStatus', False)

    
    storagedCurrentStatus = property(__storagedCurrentStatus.value, __storagedCurrentStatus.set, None, None)

    
    # Element aggregation_id uses Python identifier aggregation_id
    __aggregation_id = pyxb.binding.content.ElementUse(pyxb.namespace.ExpandedName(None, u'aggregation_id'), 'aggregation_id', '__AbsentNamespace0_CTD_ANON_2_aggregation_id', False)

    
    aggregation_id = property(__aggregation_id.value, __aggregation_id.set, None, None)

    
    # Element file uses Python identifier file
    __file = pyxb.binding.content.ElementUse(pyxb.namespace.ExpandedName(None, u'file'), 'file', '__AbsentNamespace0_CTD_ANON_2_file', True)

    
    file = property(__file.value, __file.set, None, None)

    
    # Element timeToArchive uses Python identifier timeToArchive
    __timeToArchive = pyxb.binding.content.ElementUse(pyxb.namespace.ExpandedName(None, u'timeToArchive'), 'timeToArchive', '__AbsentNamespace0_CTD_ANON_2_timeToArchive', False)

    
    timeToArchive = property(__timeToArchive.value, __timeToArchive.set, None, None)


    _ElementMap = {
        __storagedCurrentStatus.name() : __storagedCurrentStatus,
        __aggregation_id.name() : __aggregation_id,
        __file.name() : __file,
        __timeToArchive.name() : __timeToArchive
    }
    _AttributeMap = {
        
    }



# Complex type CTD_ANON_3 with content type ELEMENT_ONLY
class CTD_ANON_3 (pyxb.binding.basis.complexTypeDefinition):
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = None
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element spot_id uses Python identifier spot_id
    __spot_id = pyxb.binding.content.ElementUse(pyxb.namespace.ExpandedName(None, u'spot_id'), 'spot_id', '__AbsentNamespace0_CTD_ANON_3_spot_id', False)

    
    spot_id = property(__spot_id.value, __spot_id.set, None, None)

    
    # Element aggregations uses Python identifier aggregations
    __aggregations = pyxb.binding.content.ElementUse(pyxb.namespace.ExpandedName(None, u'aggregations'), 'aggregations', '__AbsentNamespace0_CTD_ANON_3_aggregations', False)

    
    aggregations = property(__aggregations.value, __aggregations.set, None, None)


    _ElementMap = {
        __spot_id.name() : __spot_id,
        __aggregations.name() : __aggregations
    }
    _AttributeMap = {
        
    }



storage_pot = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, u'storage_pot'), CTD_ANON_3)
Namespace.addCategoryObject('elementBinding', storage_pot.name().localName(), storage_pot)



CTD_ANON._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, u'aggregation'), CTD_ANON_2, scope=CTD_ANON))
CTD_ANON._GroupModel = pyxb.binding.content.GroupSequence(
    pyxb.binding.content.ParticleModel(CTD_ANON._UseForTag(pyxb.namespace.ExpandedName(None, u'aggregation')), min_occurs=1, max_occurs=None)
    )
CTD_ANON._ContentModel = pyxb.binding.content.ParticleModel(CTD_ANON._GroupModel, min_occurs=1, max_occurs=1)



CTD_ANON_._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, u'file_id'), pyxb.binding.datatypes.anyType, scope=CTD_ANON_))

CTD_ANON_._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, u'file_name'), pyxb.binding.datatypes.anyType, scope=CTD_ANON_))

CTD_ANON_._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, u'file_size'), pyxb.binding.datatypes.anyType, scope=CTD_ANON_))
CTD_ANON_._GroupModel = pyxb.binding.content.GroupSequence(
    pyxb.binding.content.ParticleModel(CTD_ANON_._UseForTag(pyxb.namespace.ExpandedName(None, u'file_id')), min_occurs=1, max_occurs=1),
    pyxb.binding.content.ParticleModel(CTD_ANON_._UseForTag(pyxb.namespace.ExpandedName(None, u'file_name')), min_occurs=1, max_occurs=1),
    pyxb.binding.content.ParticleModel(CTD_ANON_._UseForTag(pyxb.namespace.ExpandedName(None, u'file_size')), min_occurs=1, max_occurs=1)
    )
CTD_ANON_._ContentModel = pyxb.binding.content.ParticleModel(CTD_ANON_._GroupModel, min_occurs=1, max_occurs=1)



CTD_ANON_2._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, u'storagedCurrentStatus'), pyxb.binding.datatypes.anyType, scope=CTD_ANON_2))

CTD_ANON_2._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, u'aggregation_id'), pyxb.binding.datatypes.anyType, scope=CTD_ANON_2))

CTD_ANON_2._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, u'file'), CTD_ANON_, scope=CTD_ANON_2))

CTD_ANON_2._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, u'timeToArchive'), pyxb.binding.datatypes.anyType, scope=CTD_ANON_2))
CTD_ANON_2._GroupModel = pyxb.binding.content.GroupSequence(
    pyxb.binding.content.ParticleModel(CTD_ANON_2._UseForTag(pyxb.namespace.ExpandedName(None, u'aggregation_id')), min_occurs=1, max_occurs=1),
    pyxb.binding.content.ParticleModel(CTD_ANON_2._UseForTag(pyxb.namespace.ExpandedName(None, u'storagedCurrentStatus')), min_occurs=1, max_occurs=1),
    pyxb.binding.content.ParticleModel(CTD_ANON_2._UseForTag(pyxb.namespace.ExpandedName(None, u'timeToArchive')), min_occurs=0L, max_occurs=1),
    pyxb.binding.content.ParticleModel(CTD_ANON_2._UseForTag(pyxb.namespace.ExpandedName(None, u'file')), min_occurs=1, max_occurs=None)
    )
CTD_ANON_2._ContentModel = pyxb.binding.content.ParticleModel(CTD_ANON_2._GroupModel, min_occurs=1, max_occurs=1)



CTD_ANON_3._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, u'spot_id'), pyxb.binding.datatypes.anyType, scope=CTD_ANON_3))

CTD_ANON_3._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, u'aggregations'), CTD_ANON, scope=CTD_ANON_3))
CTD_ANON_3._GroupModel_ = pyxb.binding.content.GroupSequence(
    pyxb.binding.content.ParticleModel(CTD_ANON_3._UseForTag(pyxb.namespace.ExpandedName(None, u'aggregations')), min_occurs=1, max_occurs=1)
    )
CTD_ANON_3._GroupModel = pyxb.binding.content.GroupSequence(
    pyxb.binding.content.ParticleModel(CTD_ANON_3._UseForTag(pyxb.namespace.ExpandedName(None, u'spot_id')), min_occurs=1, max_occurs=1),
    pyxb.binding.content.ParticleModel(CTD_ANON_3._GroupModel_, min_occurs=1, max_occurs=1)
    )
CTD_ANON_3._ContentModel = pyxb.binding.content.ParticleModel(CTD_ANON_3._GroupModel, min_occurs=1, max_occurs=1)
