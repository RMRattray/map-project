
import tkinter
import bisect
import math
import geopandas
import os

# Read the data file for country boundaries.
COUNTRIES_DATA_TABLE = geopandas.read_file(os.path.join('World shapefiles','World_Countries','World_Countries.shp'))
COUNTRIES_DATA_TABLE[["westmost","southmost","eastmost","northmost"]] = COUNTRIES_DATA_TABLE["geometry"].bounds
COUNTRIES_SIMPLE_POLYGONS = [] # Make a column in the table for the coordinate-tuple forms of countries,
for eachcountry in COUNTRIES_DATA_TABLE["geometry"]: # as opposed to Shapely objects
    if eachcountry.geom_type == 'MultiPolygon': # whose coordinate properties are
        SUBLIST = [] # some special Shapely object anyway (as Tkinter cannot handle that.)
        for eachgon in eachcountry.geoms:
            SUBLIST.append(tuple(eachgon.exterior.coords))
        COUNTRIES_SIMPLE_POLYGONS.append(tuple(SUBLIST))
    else:
        COUNTRIES_SIMPLE_POLYGONS.append(tuple(eachcountry.exterior.coords))
COUNTRIES_DATA_TABLE["simple geometry"] = COUNTRIES_SIMPLE_POLYGONS

def expressLat(latitude):
    if latitude > 0:
        return f"{latitude:.1f}°N"
    elif latitude < 0:
        return f"{abs(latitude):.1f}°S"
    else:
        return "Equator"

def expressLong(longitude):
    if longitude > 0:
        return f"{longitude:.1f}°E"
    elif longitude < 0:
        return f"{abs(longitude):.1f}°W"
    else:
        return "0°"

class MapWindow(tkinter.Tk):
    def __init__(self):
        tkinter.Tk.__init__(self)
        self.title("Standard-Ratio Equal-Area Projection")
        if self.winfo_screenwidth() > self.winfo_screenheight() * (2 ** 0.5):
            self.permwidth = int(self.winfo_screenheight()*2**0.5)
            self.permheight = self.winfo_screenheight()
        else:
            self.permwidth = self.winfo_screenwidth()
            self.permheight = int(self.winfo_screenwidth()*2**-0.5)
        self.geometry(f"{self.permwidth}x{self.permheight}")
        self.config(bg='black')
        self.zoom = 1.0
        self.zoomsize = 15
        self.focusLong = 0.0
        self.focusLat = 0.0

        self.evenLat = 20.0

        self.canvas = tkinter.Canvas(self,bg='black')
        self.canvas.place(relx=0,rely=0,relwidth=1,relheight=1)
        self.longitudeMarks = []
        self.longitudeMarkLabels = []
        self.latitudeMarks = []
        self.latitudeMarkLabels = []

        self.shapes = []

        self.buttons = [tkinter.Button(self,text="+",command=lambda: self.zoomIn()),
        tkinter.Button(self,text="-",command=lambda: self.zoomOut()),
        tkinter.Button(self,text="⬆️",command=lambda: self.panUp()),
        tkinter.Button(self,text="➡️",command=lambda: self.panRt()),
        tkinter.Button(self,text="⬅️",command=lambda: self.panLf()),
        tkinter.Button(self,text="⬇️",command=lambda: self.panDn())]
        self.drawButtons()

    def drawButtons(self):
        pad = 0.005
        wid = 0.02
        self.buttons[0].place(relx=pad,rely=pad*2**0.5,relwidth=wid,relheight=wid*2**0.5)
        self.buttons[1].place(relx=pad,rely=(2*pad+wid)*2**0.5,relwidth=wid,relheight=wid*2**0.5)
        self.buttons[2].place(relx=1-2*(wid+pad),rely=pad*2**0.5,relwidth=wid,relheight=wid*2**0.5)
        self.buttons[3].place(relx=1-(wid+pad),rely=(2*pad+wid)*2**0.5,relwidth=wid,relheight=wid*2**0.5)
        self.buttons[4].place(relx=1-3*(wid+pad),rely=(2*pad+wid)*2**0.5,relwidth=wid,relheight=wid*2**0.5)
        self.buttons[5].place(relx=1-2*(wid+pad),rely=(3*pad+2*wid)*2**0.5,relwidth=wid,relheight=wid*2**0.5)

    def convertLong(self,longitude): # These methods convert longitude and latitude to x and y on the canvas.
        return int(self.permwidth*(0.5+(longitude-self.focusLong)/(360*self.zoom)))

    def convertLat(self,latitude):
        #return int(self.permheight/2*(1-math.sin(math.radians(latitude))-math.sin(math.radians(self.focusLat)))/self.zoom)
        return int(self.permheight/2*(1-(math.sin(math.radians(latitude))-math.sin(math.radians(self.focusLat)))/self.zoom))

    def zoomIn(self):
        self.zoom *= 0.8
        self.drawLines()

    def zoomOut(self):
        self.zoom *= 1.25
        if self.zoom > 1.0:
            self.zoom = 1.0
        if math.sin(math.radians(self.focusLat))+self.zoom > 1:
            self.focusLat = math.degrees(math.asin(1-self.zoom))
        if math.sin(math.radians(self.focusLat))-self.zoom < -1:
            self.focusLat = math.degrees(math.asin(self.zoom-1))
        if self.rightLong() > 180:
            self.focusLong = 180*(1-self.zoom)
        if self.leftLong() < -180:
            self.focusLong = -180*(1-self.zoom)
        self.drawLines()

    def panRt(self):
        self.focusLong += self.zoomsize*self.zoom
        if self.rightLong() > 180:
            self.focusLong = 180*(1-self.zoom)
        self.drawLines()

    def panLf(self):
        self.focusLong -= self.zoomsize*self.zoom
        if self.leftLong() < -180:
            self.focusLong = -180*(1-self.zoom)
        self.drawLines()

    def panUp(self):
        self.focusLat = math.degrees(math.asin(math.sin(math.radians(self.focusLat))+self.zoom*self.permwidth*self.zoomsize/(180*self.permheight)))
        if math.sin(math.radians(self.focusLat))+self.zoom > 1:
            self.focusLat = math.degrees(math.asin(1-self.zoom))
        self.drawLines()

    def panDn(self):
        self.focusLat = math.degrees(math.asin(math.sin(math.radians(self.focusLat))-self.zoom*self.permwidth*self.zoomsize/(180*self.permheight)))
        if math.sin(math.radians(self.focusLat))-self.zoom < -1:
            self.focusLat = math.degrees(math.asin(self.zoom-1))
        self.drawLines()

    # The formulas below can be deduced from the equations for x and y from the
    # zoom, focus coordinates, and window dimensions, by substituting 0 and the
    # dimensions for x and y in the equations.
    def topLat(self):
        return math.degrees(math.asin(math.sin(math.radians(self.focusLat))+self.zoom))

    def bottomLat(self):
        return math.degrees(math.asin(math.sin(math.radians(self.focusLat))-self.zoom))

    def leftLong(self):
        return self.focusLong - 180 * self.zoom

    def rightLong(self):
        return self.focusLong + 180 * self.zoom

    def placeLong(self):
        INTERVALS = [0.5,1,2,5,10,15]
        interval = INTERVALS[bisect.bisect(INTERVALS,30*self.zoom)-1]
        longitude = (self.leftLong()//interval + 1)*interval
        for mark in self.longitudeMarks:
            self.canvas.delete(mark)
        for label in self.longitudeMarkLabels:
            self.canvas.delete(label)
        self.longitudeMarks = []
        self.longitudeMarkLabels = []
        while longitude < self.rightLong():
            x = self.convertLong(longitude)
            #print(f"Longitude: {longitude}\nX: {x}")
            self.longitudeMarks.append(self.canvas.create_line(x,0,x,self.permheight,fill='white'))
            self.longitudeMarkLabels.append(self.canvas.create_text((x,0),anchor=tkinter.NW,fill='white',text=expressLong(longitude)))
            longitude += interval

    def placeLat(self):
        INTERVALS = [0.5,1,2,5,10,15]
        #interval = INTERVALS[bisect.bisect(INTERVALS,(self.topLat()-self.bottomLat())/12)-1]
        interval = INTERVALS[bisect.bisect(INTERVALS,30*self.zoom)-1]
        latitude = (self.bottomLat()//interval + 1)*interval
        #print(f"Top: {self.topLat()}\nBottom: {self.bottomLat()}\nInterval: {interval}")
        for mark in self.latitudeMarks:
            self.canvas.delete(mark)
        for label in self.latitudeMarkLabels:
            self.canvas.delete(label)
        self.latitudeMarks = []
        self.latitudeMarkLabels = []
        while latitude < self.topLat():
            y = self.convertLat(latitude)
            self.latitudeMarks.append(self.canvas.create_line(0,y,self.permwidth,y,fill='white'))
            self.latitudeMarkLabels.append(self.canvas.create_text((0,y),anchor=tkinter.NW,fill='white',text=expressLat(latitude)))
            latitude += interval

    def convertSimplePolygon(self,polygon):
        newpolygon = []
        for point in polygon:
            newpolygon.append((self.convertLong(point[0]),self.convertLat(point[1])))
        return tuple(newpolygon)

    def convertAnyPolygon(self,polygon):
        if isinstance(polygon[0][0],tuple):
            newpolygon = []
            for subpolygon in polygon:
                newpolygon.append(self.convertSimplePolygon(subpolygon))
            return tuple(newpolygon)
        else:
            return self.convertSimplePolygon(polygon)

    def drawAnyPolygon(self,polygon,color='white',fillcolor=''):
        newpolygon = self.convertAnyPolygon(polygon)
        if isinstance(newpolygon[0][0],tuple):
            for subpolygon in newpolygon:
                self.shapes.append(self.canvas.create_polygon(subpolygon,fill=fillcolor,outline=color))
        else:
            self.shapes.append(self.canvas.create_polygon(newpolygon,fill=fillcolor,outline=color))

    def drawShapes(self):
        for shape in self.shapes:
            self.canvas.delete(shape)
        relevant_shapes = COUNTRIES_DATA_TABLE[(COUNTRIES_DATA_TABLE["westmost"] < self.rightLong()) & (COUNTRIES_DATA_TABLE["eastmost"] > self.leftLong()) & (COUNTRIES_DATA_TABLE["northmost"] > self.bottomLat()) & (COUNTRIES_DATA_TABLE["southmost"] < self.topLat())]
        for shape in relevant_shapes["simple geometry"]:
            self.drawAnyPolygon(shape)

    def drawLines(self):
        self.placeLat()
        self.placeLong()
        self.drawShapes()
        self.drawButtons()

OHIO = ((-85,41.6),(-85,39.1),(-82.5,38.5),(-81.3,39.3),(-80.5,40.6),(-80.5,41.9),(-81.7,41.5),(-83.4,41.7))

if __name__ == "__main__":
    root = MapWindow()
    root.drawLines()
    #root.drawAnyPolygon(OHIO,'red')
    root.mainloop()
