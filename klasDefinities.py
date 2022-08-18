import Rhino
import Rhino.Geometry as rg
import ghpythonlib.components as gh
import math


def omzetten(reeks, verdiep):
    if ',' in reeks:
        return [tuple((verdiep, int(el))) for el in reeks.split(',')]
    elif len(reeks) > 0:
        return [tuple((verdiep, int(reeks)))]
    else:
        return []


def getNodes(ids, lijst):
    rLijst = []
    for i in ids:
        for el in lijst:
            if el.getID() == i:
                rLijst.append(el)
    return rLijst

#ids moeten doorgegeven worden
# checkt of een node in buren van een nodegroep zit --> alle buren van iedere node worden overlopen
def overlap(node,  nodeGroep2, planN ):
    lijst = []
    tussen = set()

    for el in getNodes(nodeGroep2, planN):
        for n in el.getBuren():
            tussen.add((n, el.getID()))

    for i in tussen:
        if node == i[0]:
            lijst.append((i))

    return lijst


def overlapDegree(node1, node2, nodeLijst):
    lijst =[]
    for el in getNodes(node1.getBuren(), nodeLijst):
        for i in getNodes(node2.getBuren(), nodeLijst):
            if el.getID() == i.getID(): lijst.append(el.getID())
    return (len(lijst), lijst)


def afstand(node, node2):
    xi, yi, zi = gh.Deconstruct(node.getGeo().CenterPoint())
    xp, yp, zp = gh.Deconstruct(node2.getGeo().CenterPoint())
    return round(math.sqrt((xi - xp) ** 2 + (yi - yp) ** 2 + (zi - zp) ** 2), 4)



class Node:

    def __init__(self, id, roomType, opp, muurRel = None, deurRel = None, buitenRel = None, geo = None, raam = None, ijkpunten = None):

        self.identifier = id
        self.roomType = roomType
        self.muurRel = muurRel
        self.deurRel = deurRel
        self.buitenRel = buitenRel
        self.refgeo = geo
        self.opp = opp
        self.raam = raam
        self.difFloorRel = set()
        self.ijkpunten = ijkpunten
        self.plan_vis = None
        self.status = False




    #fixed is een optionele param waarbij enkel de niet-vastgezette nodes geteld worden
    #zou ik beter als een lijst  opslaan dan is de code korter/sneller
    def  getNodeDegree(self, pos = False):
        count = len(self.deurRel)
        if pos:
            count += len(self.muurRel)

        if self.difFloorRel:
            count += len(self.difFloorRel)

        return count

    def getFreeNodeDegree(self,NodeList):
        counter = 0
        for el in getNodes(self.deurRel, NodeList):
            if not el.getType():
                counter += 1

        return counter


    def getBuren(self, pos = False):
        lijst =[el for el in self.deurRel]

        if self.connectedFloorRooms() :
            for el in self.connectedFloorRooms(): lijst.append(el)

        if pos:
            for el in self.muurRel: lijst.append(el)

        return lijst


    def getID(self):
        return self.identifier

    def getRoomType(self):
        return self.roomType

    def changeRoomType(self, nieuw):
        assert isinstance(nieuw, str), 'geen string'
        if isinstance(nieuw, str):
            self.roomType = nieuw

    def mogelijkeConnecties(self):
        return self.muurRel

    def heeftBuitenConnectie(self):
        if self.buitenRel:
            return True
        return False

    def heeftRaam(self):
        return self.raam

    def getOpp(self):
        return float(self.opp)

    def getGeo(self):
        return self.refgeo

    def getNode(self):
        return self

    def getType(self):
        return self.status

    def changeType(self, stat):
        self.status = stat

    def connectedFloorRooms(self):
        return self.difFloorRel

    def getFloor(self):
        return self.identifier[0]

    def changeVConnection(self, verdiep, knoop):
        self.difFloorRel.add(tuple((verdiep, knoop)))

    def getDistanceTP(self):
        return self.ijkpunten


class Edge:
    def __init__(self, node1, node2, planN):
        if node2 in getNodes(node1.getBuren(False), planN): self.type = 1
        else: self.type = 0.5
        self.edge = (node1, node2)

    def getType(self):
        return self.type
    def nxt(self):
        return self.edge[1]

    def prv(self):
        return self.edge[0]

    def getGeo(self):
        return(self.edge[0].getGeo(),self.edge[1].getGeo())


class Neighborhood:
    #seed of zaadje van de neighborhood of buurtstructuur is de start van de uittakking
    #degree is het aantal hubs er rond het zaadje worden bekeken
    #planN zijn alle nodes opgesteld voordien in het grashopperfile
    #edges zorgen voor de relaties tussen de nodes, hiermee kan later een pad gevonden worden tussen nodes
    #https: // gist.github.com / mattmcclean / 3580574
    def __init__(self, seed, degree, planN):
        self.seed = seed
        self.degree = degree
        self.edges = {seed: getNodes(seed.getBuren(True), planN)}
        self.nodes = [seed]
        self.planN = planN

        prev = getNodes(seed.getBuren(True), planN)
        cycl = degree -1

        while cycl > 0:
            tussen = []
            for el in prev:
                self.edges[el] = getNodes(el.getBuren(True), planN)
                for n in getNodes(el.getBuren(True), planN):
                    self.nodes.append(n)
                    tussen.append(n)

            prev = tussen
            cycl -= 1

        self.prev = prev

    def end_nodes(self):
        return self.prev

    def has_key(self, node):
        if node in self.edges: return True


def find_all_paths(graph, start, end, path = []):
        if path is None: path = path + [start]
        else: path = path + [start]

        if start == end:
            return [path]
        if not graph.has_key(start):
            return []
        paths = []
        for node in graph.edges[start]:
            if node not in path:
                newpaths = find_all_paths(graph, node, end, path)
                for newpath in newpaths:
                    paths.append(newpath)

        return paths

def find_loop(graph, start, path=[]):
    path=path+[start]
    for node in graph.edges[start]:
        if node not in path:
            return find_loop(graph,node,path)
        else:
            return path
    return False


def find_shortest_path(graph, start, end, path=[]):
    path=path+[start]
    if start == end:
        return [path]
    if not graph.has_key(start):
        return []
    shortest_path = []
    for node in graph.edges[start]:
        if node not in path:
            newpaths = find_all_paths(graph,node,end,path)
            for newpath in newpaths:
                if newpath and (len(shortest_path) == 0 or len(newpath) < len(shortest_path)):
                    shortest_path = newpath
    return shortest_path

def find_spec_paths(graph, container):
    pos =[]
    for el in container:
        for path in el:
            if len(path) == graph.degree +1:
                pos.append(path)

    return pos




class Dic:

    ##
    #   Creates a new dic
    #
    def __init__(self,d):
        self._d = d

    ##
    #   Returns the internal dictionary
    #
    def getDictionary(self):
        return self._d

    ##
    #   Override the repr function
    #
    def __repr__(self):
        return self._d.__repr__()

    ##
    #   Override the str function
    #
    def __str__(self):
        return self._d.__str__()

    def __len__(self):
        return len(self._d)

# volgende definities zijn afkomstig van: https://gist.github.com/bengolder/1032493
# volgende definities dienen om layers te bewerken

import System
import System.Collections.Generic as SCG
import Rhino
import scriptcontext

import rhinoscriptsyntax as rs
from Rhino.FileIO import FileWriteOptions, FileReadOptions

def addRhinoLayer(layerName, layerColor=System.Drawing.Color.Black):
    """Creates a Layer in Rhino using a name and optional color. Returns the
    index of the layer requested. If the layer
    already exists, the color is updated and no new layer is created."""
    docLyrs = scriptcontext.doc.Layers
    layerIndex = docLyrs.Find(layerName, True)
    if layerIndex == -1:
        layerIndex = docLyrs.Add(layerName,layerColor)
    else: # it exists
        layer = docLyrs[layerIndex] # so get it
        if layer.Color != layerColor: # if it has a different color
            layer.Color = layerColor # reset the color
    return layerIndex

def layerAttributes(layerName, layerColor=System.Drawing.Color.Black):
    """Returns a Rhino ObjectAttributes object for a rhino layer with an optional color."""
    att = Rhino.DocObjects.ObjectAttributes()
    att.LayerIndex = addRhinoLayer(layerName, layerColor)
    return att

def deleteLayer(layerName, quiet=True):
    """Deletes a layer by Name. returns nothing."""
    layer_index = scriptcontext.doc.Layers.Find(layerName, True)
    settings = Rhino.DocObjects.ObjectEnumeratorSettings()
    settings.LayerIndexFilter = layer_index
    objs = scriptcontext.doc.Objects.FindByFilter(settings)
    ids = [obj.Id for obj in objs]
    scriptcontext.doc.Objects.Delete(ids, quiet)
    scriptcontext.doc.Layers.Delete(layer_index, quiet)

def bakeMany(listOfThings, objectAttributes=None):
    if not objectAttributes:
        objectAttributes = Rhino.DocObjects.ObjectAttributes()
    for thing in listOfThings:
        # move from specific to broad
        if isinstance(thing, Rhino.Geometry.Point3d):
            scriptcontext.doc.Objects.AddPoint(thing, objectAttributes)
        elif isinstance(thing, Rhino.Geometry.Point):
            scriptcontext.doc.Objects.AddPoint(thing.Location, objectAttributes)
        elif isinstance(thing, Rhino.Geometry.Curve):
            scriptcontext.doc.Objects.AddCurve(thing, objectAttributes)
        elif isinstance(thing, Rhino.Geometry.Surface):
            scriptcontext.doc.Objects.AddSurface(thing, objectAttributes)
        elif isinstance(thing, Rhino.Geometry.Brep):
            scriptcontext.doc.Objects.AddBrep(thing, objectAttributes)
        elif isinstance(thing, Rhino.Geometry.Mesh):
            scriptcontext.doc.Objects.AddSurface(thing, objectAttributes)
        elif isinstance(thing, Rhino.Geometry.Hatch):
            scriptcontext.doc.Objects.AddHatch(thing, objectAttributes)
        elif isinstance(thing, Rhino.Display.Text3d):
            scriptcontext.doc.Objects.AddText(thing, objectAttributes)
        else:
            print ('''Unrecognized object type: %s''' % type(thing))

def deleteAll():
    """Deletes everything in the current Rhino scriptcontext.doc. Returns nothing."""
    guidList = []
    objType = Rhino.DocObjects.ObjectType.AnyObject
    objTable = scriptcontext.doc.Objects
    objs = objTable.GetObjectList(objType)
    for obj in objs:
        guidList.append(obj.Id)
    for guid in guidList:
        objTable.Delete(guid, True)

def exportFile(filePath,
        version=4,
        geomOnly=False,
        selectedOnly=False,
        ):
    '''Export a file.'''
    opt = FileWriteOptions()
    opt.FileVersion = version
    opt.WriteGeometryOnly = geomOnly
    opt.WriteSelectedObjectsOnly = selectedOnly
    return scriptcontext.doc.WriteFile(filePath, opt)

def exportLayers(layerNames, filePath, version=4):
    '''Export only the items on designated layers to a file.'''
    # save selection
    oldSelection = rs.SelectedObjects()
    # clear selection
    rs.UnselectAllObjects()
    # add everything on the layers to selection
    for name in layerNames:
        objs = scriptcontext.doc.Objects.FindByLayer(name)
        guids = [obj.Id for obj in objs]
        scriptcontext.doc.Objects.Select.Overloads[SCG.IEnumerable[System.Guid]](guids)
    # export selected items
    exportFile(filePath, version, selectedOnly=True)
    #clear selection
    rs.UnselectAllObjects()
    # restore selection
    if oldSelection:
        scriptcontext.doc.Objects.Select.Overloads[SCG.IEnumerable[System.Guid]](oldSelection)
    print ('exported %s' % filePath)

