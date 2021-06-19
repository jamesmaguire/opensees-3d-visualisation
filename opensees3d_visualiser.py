import pandas as pd
import numpy  as np
import matplotlib.pyplot as pl
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D

''' INPUT FILES
Enter the filenames of the files where the node coordinates, elements
and displacement data is stored.
*Note: The file must be located in the same directory as this notebook,
or the full path should be provided
*Note: Node coordinates must be explicitly defined. If nodes are created
using loops, the script will not identify them
'''
nodeFile = './example/example-model.tcl'  # tcl file which defines nodes
elemFile = './example/example-model.tcl'  # tcl file which defines elements
dispFile = './example/example-disps.out'  # output containing node disp data
fig = pl.figure(figsize=(10, 10))
sysc_time = 1 # time between viewer refresh (in seconds)
''' TCL READER
This function reads the files and extracts lines which begin with the
startwith argument. n_cols tells the reader how many columns to extract
from the line.
'''
def OpenSeesTclRead(tclFile, startswith, n_cols):
    fileInfo = []
    file = open(tclFile,'r')
    for line in file:
        if line[:len(startswith)] == startswith:
            args = line.split()
            for i in range(0, n_cols):
                fileInfo.append(args[i])
    file.close()
    return np.array(fileInfo).reshape((-1, n_cols))

nodeInfo = OpenSeesTclRead(nodeFile, 'node', 5)
elemInfo = OpenSeesTclRead(elemFile, 'element', 5)
rlnkInfo = OpenSeesTclRead(elemFile, 'rigidLink', 4)


''' OUTPUT READER
This function reads the output files produced by the OpenSees disp reco-
rder. XML output files are supported.
'''
def OpenSeesOutputRead(outFile):
    if outFile[-4:] == '.xml':
        skip = 4
    else: skip = 0
    outData = pd.read_csv(outFile, delim_whitespace=True, header=None,
                          comment='<', skiprows=skip)
    return np.array(outData)

outData = OpenSeesOutputRead(dispFile)
n_steps = len(outData[:,0])


'''
PLOTTER
This section takes produces a 3D interactive plot for model visualisati-
on. In order to view your model, plot the nodes using the *plotNodes*
function, and the elements using the *plotElements* function.
*plotNodes* - this function takes the inputs: initNodeCoords or dispNod-
eCoords; node colour; node size
*plotElements* this function takes the inputs: elemInfo or rlnkInfo;
nodeList; initNodeCoords or dispNodeCoords; line colour; line style
('-','--',':', etc); line thickness; \*element type (only plot specific
type of element); \*min element ID and \*max element ID (only plot elem-
ents with ID in range)
Make sure to check the axis limits (ax.set_xlim...). It is recommended
that the limits are chosen over a constant range so that the view is not
distorted. Eg - xlim(0,5), ylim(0,2), zlim(0,2) will result in a squash-
ed x-axis as the ranges are all scaled to an equal length on the screen.
Set the figure size using pl.rcParams['figure.figsize'] = (*figWidth*,
*figHeight*). It is recomended that *figWidth* = *figHeight* to avoid
distortion.
Set the scalefactor to scale the displacements
Set the azimuth and elevation to control the viewing angle
Set the step to view the timestep (1, 2, 3, ...)
'''

# Function to plot nodes
def plotNodes(nodeCoords, nodeColour, nodeSize):
    x = nodeCoords[:,0]
    y = nodeCoords[:,1]
    z = nodeCoords[:,2]
    ax.scatter(x, y, z, c=nodeColour, edgecolor=nodeColour, s=nodeSize)

# Function to plot elements
def plotElements(elemList, nodeList, nodeCoords, lineColour, lineStyle,
                 lineThickness, eleType=None, elemMin=0, elemMax=float('inf')):
    for i in range(0, len(elemList[:,0])):
        if (eleType==None or elemList[i,1]==eleType) \
        and (elemMin<=elemList[i,2].astype(float)<=elemMax):
            nodeiRow = int(np.argwhere(nodeList[:,1]==elemList[i,-2]))
            nodejRow = int(np.argwhere(nodeList[:,1]==elemList[i,-1]))
            element = np.append([nodeCoords[nodeiRow,:]],
                                [nodeCoords[nodejRow,:]], axis=0)
            ax.plot(element[:,0], element[:,1], element[:,2], c=lineColour,
                    lw=lineThickness, ls=lineStyle)

ani = animation.FuncAnimation(fig, plotElements, interval=sysc_time*1000,
                                  fargs=(nodeFile,))
ani = animation.FuncAnimation(fig, elemFile, interval=sysc_time*1000,
                                  fargs=(elemFile,))

# Set viewpoint, scalefactor for displacement and timestep
scalefactor = 1
azimuth = -50
elevation = 20
step = 10

# Data preparation
timestep = outData[int(step)-1,0]
deformation = outData[int(step)-1,1:].reshape(-1,3)
initNodeCoords = nodeInfo[:,2:5].astype(float)
dispNodeCoords = initNodeCoords + (scalefactor*deformation)

# Plot 3D axes
fig = pl.figure(figsize=(10, 10))
ax = fig.add_subplot(111, projection='3d')
ax.view_init(elev=elevation, azim=azimuth)
ax.set_xlim(-2,3)
ax.set_ylim(-0.5,4.5)
ax.set_zlim(0,5)

# Plot initial node locations
plotNodes(initNodeCoords,'silver',0.5)
# Plot displaced node locations
plotNodes(dispNodeCoords,'black',2)
# Plot Initial  elements as lines
plotElements(elemInfo, nodeInfo, initNodeCoords, 'grey', ':', 0.5, None, 100, 499)
# Plot Uprights elements as lines
plotElements(elemInfo, nodeInfo, dispNodeCoords, 'grey', '-', 1.5, 'elasticBeamColumn', 100, 299)
# Plot Bracing  elements as lines
plotElements(elemInfo, nodeInfo, dispNodeCoords, 'grey', '-', 1.0, 'truss', 300, 399)
# Plot Beams    elements as lines
plotElements(elemInfo, nodeInfo, dispNodeCoords, 'chocolate', '-', 1.0, 'elasticBeamColumn', 400, 499)
# Plot Pallets  elements as lines
plotElements(elemInfo, nodeInfo, dispNodeCoords, 'grey', '-', 0.5, 'elasticBeamColumn', 600, 699)
# Plot RigidLnk elements as lines
plotElements(rlnkInfo, nodeInfo, dispNodeCoords, 'grey', '-', 1.0)

pl.savefig('example/example.png')
pl.show()
