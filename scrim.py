from math import *
from random import *
from abjad import *
from copy import *
#8/17/14 you can generalize this density scrim thing -- first, the macro (how many flagged leaves per each measure?):
#the interface is that you pass it a function and some measures:
'''
scrim function -- Which leaves are transformed? Discrete approximation of a function applied measure by measure.
transform function -- What's to be done to the leaves once identified for transformation?

First, scrim functions:
'''
def calculateScrimDensitiesFromMeasures(measures,scrimFunction,extra_middle=0,halfway=False):
    return scrimFunction(measures,extra_middle,halfway)

def sigmoid(x):
    return 1 / (1 + exp(-x))

def halfSinScrim(measures,extra_middle=0,halfway=False):
    #sample a sin curve from 3pi/2 to 2pi such that there's one element corresponding to each measure of the staff assumed palindrome.
    #values are between 0 and 1.
    densities = []
    if halfway == False:
        if len(measures)%2 == 0:
            numValues = len(measures)/2 - extra_middle - 1
            densities = [ (sin(2*pi*(15/20.0 + (1/4.0 * x/numValues) )) + 1) for x in range(int(numValues)) ]
            down = reversed(deepcopy(densities))
        else:
            numValues = len(measures)/2 - extra_middle
            densities = [ (sin(2*pi*(15/20.0 + (1/4.0 * x/numValues) )) + 1) for x in range(int(numValues)) ]
            down = reversed(deepcopy(densities))
        if len(measures)%2 == 0:
            densities.extend([1.0]*2)
        else:
            densities.extend([1.0])
            densities.extend( [1.0]*extra_middle )
            densities.extend(down)
    else:
        numValues = len(measures) - extra_middle - 1
        densities = [ (sin(2*pi*(15/20.0 + (1/4.0 * x/numValues) )) + 1) for x in range(int(numValues)) ]
        densities.extend([1.0])
        densities.extend( [1.0]*extra_middle )
    densities.extend(down)
    return densities

def sigmoidScrim(measures,extra_middle=0,halfway=False):
    densities = []
    if len(measures)%2 == 0:
        numValues = len(measures)/2 - extra_middle - 1
    else:
        numValues = len(measures)/2 - extra_middle
    densities = [ sigmoid( 20 * x/numValues - 10 ) for x in range(numValues) ]
    down = reversed(deepcopy(densities))
    if len(measures)%2 == 0:
        densities.extend([1.0]*2)
    else:
        densities.extend([1.0])
    densities.extend( [1.0]*extra_middle )
    densities.extend(down)
    print "densities is",len(densities),"long."
    return densities

def linearScrim(measures,extra_middle=0,halfway=False):
    densities = []
    if len(measures)%2 == 0:
        numValues = len(measures)/2 - extra_middle - 1
    else:
        numValues = len(measures)/2 - extra_middle
    densities = [ float(x)/numValues for x in range(numValues) ]
    down = reversed(deepcopy(densities))
    if len(measures)%2 == 0:
        densities.extend([1.0]*2)
    else:
        densities.extend([1.0])
    densities.extend( [1.0]*extra_middle )
    densities.extend(down)
    print "densities is",len(densities),"long."
    return densities

#the very micro: given one measure's density, which leaves does the scrim flag?
def assembleSchemeByDensity(numLeaves,numLeavesImpacted,halfway=False):
    #randomly generates a string of 0s and 1s to reflect the specified density. 
    theList = []
    numLeavesNot = numLeaves - numLeavesImpacted
    for x in range(numLeavesImpacted):
        theList.append(1)
    for x in range(numLeavesNot):
        theList.append(0)
    shuffle(theList)
    out = ""
    for x in theList:
        out += str(x)
    return out

def chooseDensitySchemeForMeasure(density,measure):
    numLeaves = len(measure.select_leaves())
    numLeavesImpacted = int(density * numLeaves)
    #print "for measure",measure
    #print "\tdensity:",density
    #print "\tnumLeaves:",numLeaves
    #print "\tnumLeavesImpacted:",numLeavesImpacted," (out of", numLeaves," leaves)"
    scheme = assembleSchemeByDensity(numLeaves,numLeavesImpacted)
    #print "\t\tscheme:",scheme
    return scheme

#and you can generate and apply a scheme to an arbitrary staff
def makeDensityScrimForMeasures(measures,scrimFunction,extra_middle=0,halfway=False):
    scrim = []
    densities = calculateScrimDensitiesFromMeasures(measures,scrimFunction,extra_middle,halfway)
    for density,measure in zip(densities,measures):
        scrim.append( chooseDensitySchemeForMeasure(density,measure) )
    return scrim

#pass any application function as an argument to be enacted on the scrim's flagged leaves.
def applySchemeToMeasure(scheme,measure,applicationFunction):
    leaves = measure.select_leaves()
    applicationFunction(scheme,leaves)

def applyDensityScrimToMeasures(measures,scrim,applicationFunction):
    for scheme,measure in zip(scrim,measures):
        applySchemeToMeasure(scheme,measure,applicationFunction)

'''
transform function -- What's to be done to the leaves once identified for transformation?
'''

#now you can make whatever transforms you want bar-by-bar, and the functions will take care of the density changes for the whole passage:
def colorLeavesByScheme(scheme,leaves,invert=False):
    for pair in zip(scheme,leaves):
        if int(pair[0]) == 1:
            override(pair[1]).note_head.color = 'red'

def replaceLeavesWithTupletsByScheme(scheme,leaves,invert=False):
    for pair in zip(scheme,leaves):
        if int(pair[0]) == 1:
            tuplet = Tuplet.from_duration_and_ratio(pair[1].written_duration, [1,1,1])
            mutate(pair[1]).replace( tuplet )

def replaceLeavesWithRestsByScheme(scheme,leaves,invert=False):
    for pair in zip(scheme,leaves):
        if int(pair[0]) == 0:
            mutate(pair[1]).replace( Rest(pair[1].written_duration) )

def distortPitchByScheme(scheme,leaves,invert=False):
    for pair in zip(scheme,leaves):
        if int(pair[0]) == 1 and not isinstance(pair[1],Rest):
            pair[1].written_pitch += randint(1,3)

'''
distortRhythmByScheme
this transform function displaces a leave's attack by dividing the leaf into a tuplet consisting of two parts and tying/pitch the first part
identically with the previous leaf, thus assuring that the attack will not be moved to a point on the default metric grid (a problem with quant and noise).
'''

def chooseDistortionTupletRatio():
    divisors = [3,5,7]
    divisor = choice(divisors)
    partOne = randint(1,divisor-1)
    partTwo = divisor - partOne
    return [partOne,partTwo]

def pitchAndTieLeavesNote(pitch,leaves):
    for leaf in leaves:
        leaf.written_pitch = pitch
    tie = Tie()
    attach(tie,leaves)

def pitchAndTieLeavesChord(pitches,leaves):
    for leaf in leaves:
        mutate(leaf).replace( Chord(pitches,leaf.written_duration) )
    tie = Tie()
    attach(tie,leaves)

def fuseLastTwoLeaves(component):
    leaves = component.select_leaves()
    lastLeaf = leaves[-1]
    penultimateLeaf = leaves[-2]
    sumOfLastTwoLeaves = lastLeaf.written_duration + penultimateLeaf.written_duration
    if sumOfLastTwoLeaves == Duration(3,16):
        mutate(component[-2:]).fuse()
        nextLeaf = inspect(component).get_leaf(1)
    
def septupletKluge(tuplet):
    multiplier = tuplet.multiplier
    if multiplier.denominator == 7:
        fuseLastTwoLeaves(tuplet)

def distortRhythmByScheme(scheme,leaves):
    for pair in zip(scheme,leaves):
        if  int(pair[0]) == 1 and not isinstance(pair[1],Rest):
            tuplet = Tuplet.from_duration_and_ratio(pair[1].written_duration,chooseDistortionTupletRatio())
            if isinstance(pair[1],Note):
                pitchAndTieLeavesNote(pair[1].written_pitch,tuplet[1:])
            else:
                pitchAndTieLeavesChord(pair[1].written_pitches,tuplet[1:])
            mutate(pair[1]).replace(tuplet)
            previousLeaf = inspect(tuplet[0]).get_leaf(-1)
            if previousLeaf and not isinstance(previousLeaf,Rest):
                if isinstance(previousLeaf,Note):
                    mutate(tuplet[0]).replace( Chord( [previousLeaf.written_pitch], tuplet[0].written_duration) )
                else:
                    mutate(tuplet[0]).replace( Chord( previousLeaf.written_pitches, tuplet[0].written_duration) )
                tie = Tie()
                septupletKluge(tuplet)
                attach(tie,[previousLeaf,tuplet[0]])

'''
ornamentRhythmByScheme
DivisionVariationToOrnament a musical line.
'''
def chooseOrnamentPitchFromLeaf(leaf):
    basePitch = leaf.written_pitch
    flip = choice([0,1])
    if flip == 1:
        ornamentPitch = basePitch + randint(1,7)
    else:
        ornamentPitch = basePitch - randint(1,7)
    if ornamentPitch > 36:
        ornamentPitch = 36
    if ornamentPitch < -12:
        ornamentPitch = -12
    return ornamentPitch
    
def makeOrnamentedTupletFromLeaf(leaf):
    possibilities = [ [2,3], [1,3,1], [1,1,3], [3,1,1] ]
    choice = randint(0,3)
    ratio = possibilities[choice]
    tuplet = Tuplet.from_duration_and_ratio(leaf.written_duration, ratio)
    if ratio == [2,3]:
        tuplet[0].written_pitch = chooseOrnamentPitchFromLeaf(leaf)
        tuplet[1].written_pitch = leaf.written_pitch
    elif ratio == [1,3,1]:
        tuplet[0].written_pitch = chooseOrnamentPitchFromLeaf(leaf)
        tuplet[1].written_pitch = leaf.written_pitch
        tuplet[2].written_pitch = chooseOrnamentPitchFromLeaf(leaf)
    elif ratio == [1,1,3]:
        tuplet[0].written_pitch = chooseOrnamentPitchFromLeaf(leaf)
        tuplet[1].written_pitch = leaf.written_pitch
        tuplet[2].written_pitch = chooseOrnamentPitchFromLeaf(leaf)
    elif ratio == [3,1,1]:
        tuplet[0].written_pitch = chooseOrnamentPitchFromLeaf(leaf)
        tuplet[1].written_pitch = leaf.written_pitch
        tuplet[2].written_pitch = chooseOrnamentPitchFromLeaf(leaf)
    return tuplet

def ornamentLeavesByScheme(scheme,leaves,invert=False):
    for pair in zip(scheme,leaves):
        if int(pair[0]) == 1:
            tuplet = makeOrnamentedTupletFromLeaf(pair[1])
            mutate(pair[1]).replace(tuplet)

'''
addDescendingOrnamentToLeavesByScheme
add a descending ornament.
'''
def makeDescendingTuplet(leaf):
    tupletDict = {3: [leaf.written_pitch,leaf.written_pitch - 1, leaf.written_pitch - 3, leaf.written_pitch - 5], 5:[leaf.written_pitch,leaf.written_pitch - 1, leaf.written_pitch - 3, leaf.written_pitch - 5, leaf.written_pitch - 7, ], 6: [leaf.written_pitch,leaf.written_pitch - 1, leaf.written_pitch - 3, leaf.written_pitch - 5, leaf.written_pitch - 7, leaf.written_pitch - 8 ]}
    key = choice([3,5,6])
    pitches = tupletDict[key]
    tuplet = Tuplet.from_duration_and_ratio(leaf.written_duration,[1]*key)
    for pitch,leaf in zip(pitches,tuplet):
        leaf.written_pitch = pitch
    return tuplet

def addDescendingOrnamentToLeavesByScheme(scheme,leaves):
    for pair in zip(scheme,leaves):
        if int(pair[0]) == 1:
            tuplet = makeDescendingTuplet(pair[1])
            mutate(pair[1]).replace(tuplet)

def transformMeasuresByMeasure(measures,scrimFunction,transformFunction,extra_middle=0):
    scrim = makeDensityScrimForMeasures(measures,scrimFunction,extra_middle=0)
    applyDensityScrimToMeasures(measures,scrim,transformFunction)

def transformStaffByMeasure(staff,scrimFunction,transformFunction,extra_middle=0,halfway=False):
    #change the leaves of measures according to specified scrim function and transform function.
    scrim = makeDensityScrimForMeasures(staff[:],scrimFunction,extra_middle,halfway)
    applyDensityScrimToMeasures(staff[:],scrim,transformFunction)

def transformScoreByMeasure(score,scrimFunction,transformFunction,extra_middle=0):
    for staff in score:
        transformStaff(staff,scrimFunction,transformFunction,extra_middle)

'''
Or use statistical feedback.
'''
def adjustWeight(oldPair,histogramValue):
    newWeights = []
    for coupling in zip(oldPair,histogram):
        difference = coupling[0][1] - coupling[1]
        newWeight = coupling[0][1] + difference
        newWeights.append( (coupling[0][0], newWeight)  )
    return newWeights

'''
Or just compose a scheme for the whole thing.
scheme = [
]
scheme.extend([0]*23)
scheme.append(1)
scheme.extend([0]*6)
scheme.extend([1]*2)
'''