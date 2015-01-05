import arcpy
import os

##
##### Helper Functions
##

def map_elements (map_doc, element_type):
    ''' Takes an Element Type i.e. "GRAPHIC_ELEMENT", "TEXT_ELEMENT" and
        builds a dictionary with the name of the element as the key and the
        object as the value. Excludes all elements not given a name '''
    element_map = sorted([(str(obj.name), obj)
        for obj in arcpy.mapping.ListLayoutElements(map_doc, element_type)
                   if len(str(obj.name)) > 0], key = lambda name: name[0])
    return {element[0]:element[1] for element in element_map}

def get_element_dimensions (element_object):
    ''' return tuple with element dimensions '''
    return element_object.elementHeight, element_object.elementWidth

def get_element_coordinates (element_object):
    ''' return tuple of element coordinates '''
    return element_object.elementPositionY, element_object.elementPositionX

def to_pdf(map_doc, destination, page_id, page_index):
    ''' moves through data driven pages, exporting pdf '''
    map_doc.dataDrivenPages.currentPageID = page_id
    print "Exporting to PDF: {}".format(page_index)
    export_name = os.path.join(destination, "{}.pdf".format(page_index))
    map_doc.dataDrivenPages.exportToPDF(export_name, "CURRENT",
        resolution=300, picture_symbol="VECTORIZE_BITMAP")

##
##### MISC Functions
##

def move_arrow (map_doc, position_x, position_y):
    ''' adjust the north arrow as needed dependent on whether north arrow
        obstructs a view in ddp '''
    north_arrow = map_elements(map_doc, "MAPSURROUND_ELEMENT")["North Arrow"]
    north_arrow.elementPositionY = position_x
    north_arrow.elementPositionX = position_y

##
##### Application
##

class GenerateTable(object):
    ''' To cycle through a ddp setup in an mxd and export out a unique table
        on each map, field names must match exactly between graphic and text
        elements in an mxd and the table passed into the class. Further, the
        ddp index name must also match a field in the table. '''
    def __init__ (self, mxd, data, destination):
        self.mxd = mxd
        self.table = data
        self.destination = destination
        self.ddp_field = arcpy.mapping.MapDocument(mxd).dataDrivenPages.pageNameField.name

    def initialize(self):
        ''' A temporary MXD is created to find the datasource of the ddp in
            the mxd, and then a cursor loops through the mxd wherein each loop
            translates to one map constructed and exported '''
        temp_map_doc = arcpy.mapping.MapDocument(self.mxd)
        ddp_layer = arcpy.mapping.ListLayers(temp_map_doc,
            temp_map_doc.dataDrivenPages.indexLayer)[0].dataSource
        cursor = arcpy.SearchCursor(ddp_layer)
        for page_id, map_page in enumerate(cursor, start=1):
            self.construct_table(page_id, map_page)
        del cursor

    def construct_table(self, page_id, map_page):
        ''' A new mxd is stfarted to purge any previous tables that may have
            been constructed beforehand '''
        map_doc = arcpy.mapping.MapDocument(self.mxd)
        page_index = map_page.getValue(self.ddp_field)
        self.stage_data(map_doc, page_index)
        to_pdf(map_doc, self.destination, page_id, page_index)

    def stage_data(self, map_doc, page_index):
        ''' Grab all the named elements (text and graphic elements should be
            of equal length and equal keys) and then build out each column,
            they key that binds all this is the element name which should
            match the field name in the table and ddp field name '''
        graphics =  map_elements(map_doc, "GRAPHIC_ELEMENT")
        text = map_elements(map_doc, "TEXT_ELEMENT")
        for field in text.keys():
            self.build_column(field, graphics[field], text[field], page_index)

    def build_column(self, field, graphic_object, text_object, page_index):
        ''' Constructs a column given an attribute field for all values that
            match current index of data driven page. Center text elements in
            mxd to center elements in table'''
        table_cursor = arcpy.SearchCursor(self.table)
        i = 1
        for table_row in table_cursor:
            if table_row.getValue(self.ddp_field) == page_index:
                graphic = graphic_object.clone()
                text = text_object.clone()

                graphic_height, graphic_width = get_element_dimensions(graphic_object)
                graphic_x = get_element_coordinates(graphic_object)[1]
                graphic.elementPositionY -= (graphic_height*i)

                text.elementPositionY -= (graphic_height*i)
                text.text = table_row.getValue(field)
                text_width = get_element_dimensions(text)[1]
                text.elementPositionX = (graphic_x + (graphic_width / 2.0)) - (text_width / 2.0)
                i += 1
        del table_cursor

##
##### Application initialization
##

if __name__ == '__main__':
    MXD_PATH = r''
    TABLE = r''
    DESTINATION = r''
    APP = GenerateTable(MXD_PATH, TABLE, DESTINATION)
    APP.initialize()