#written with Abjad 2.14. Last revision before premiere on 9/12/14
from abjad import *
from itertools import *
from random import *
from scrim import *
from statisticalFeedback import *
from makeFinalScore import *

seed(3)

#9/11/14 must change: no lower voice note should be lower than the bottom of the midle voice,

def make_piano_staff():
    piano_staff = scoretools.PianoStaff()
    top_staff = Staff()
    top_staff.name = "top"
    middle_staff = Staff()
    middle_staff.name = "middle"
    bottom_staff = Staff()
    bottom_staff.name = "bottom"
    c = Clef('bass')
    attach(c,bottom_staff)
    piano_staff.extend([top_staff, middle_staff,bottom_staff])
    #marktools.LilyPondCommandMark('override StaffGrouper.staffgroup-staff-spacing.basic-distance = #200')(piano_staff[0])
    return piano_staff

def makeNoteListsFromDownsAndUps(downs,ups):
    lists = []
    for pair in zip(downs,ups):
        noteList = []
        down = pair[0]
        up = pair[1]
        noteList.append(down)
        noteList.extend( [Note(0,(1,4)), Note(4,(1,4))] )
        noteList.append(up)
        lists.append(noteList)
    return lists

def extractPitchesFromNoteLists(noteLists):
    outs = []
    for l in noteLists:
        outs.append( [x.written_pitch for x in l] )
    return outs        
    
def makeVerticalityListsFromPitchVector(scale,pitchVector):
    #returns a list of lists, each of which are the simultaneous quarter notes/chords.
    notes = scale.make_notes(7,(1,4))
    downs = [-x for x in pitchVector]
    downs = [Note(notes[x%7]) for x in downs]
    downs.insert(0,Note(0,(1,4)))
    for note in downs[1:]:
        note.written_pitch -= 12
    ups = [Note(notes[x%7]) for x in pitchVector]
    ups.insert(0,Note(0,(1,4)))
    for up in ups:
        up.written_pitch += 12 
    lists = makeNoteListsFromDownsAndUps(downs,ups)
    lists = extractPitchesFromNoteLists(lists)
    return lists

def addMeasuresToPianoStaff(score):
    for staff in score[0]:
        shards = mutate(staff[:]).split([(5,4)], cyclic=True)
        for shard in shards:
            scoretools.Measure((5,4), shard)

def makePitchVectorsFromScale(scale):
    pitchVectors = [x for x in permutations([1,2,3,4])]
    shuffle(pitchVectors)
    return pitchVectors
    
def DistortRhythmProportionally(score):
    for x in range(3):
        transformMeasuresByMeasure(score[0][0][8*x:8*(x+1)],halfSinScrim,distortRhythmByScheme)
        transformMeasuresByMeasure(score[0][2][8*x:8*(x+1)],halfSinScrim,distortRhythmByScheme)

def generateVerticalities(scale):
    pitchVectors = makePitchVectorsFromScale(scale)
    verticalities = []
    for v in pitchVectors:
        verticalities.extend( makeVerticalityListsFromPitchVector(scale,v) )
    return verticalities

def generateDistortionSchemas(choices,befores,afters,bdaProps):
    items = 60
    generated = bdaInterp(choices,befores,afters,items,bdaProps)
    back = reversed(deepcopy(generated))
    generated.extend(back)
    return generated

def distortPitch(pitch):
    flip = choice([0,1])
    if flip == 0:
        pitch += randint(1,3)
    else:
        pitch -= randint(1,3)
    return pitch

def distortVerticalityByScheme(verticality,numPitchesToTag):
    choices = range(5)
    tagged = sample(choices,numPitchesToTag)
    distorted = []
    for x,pitch in enumerate(verticality):
        if x in tagged:
            pitch = distortPitch(pitch)
        distorted.append(pitch)
    while distorted[1] == distorted[2]:
        pitch = distorted.pop(2)
        distortedPitch = distortPitch(pitch)
        distorted.insert(2,distortedPitch)
    return distorted
            
def distortBasePitchesProportionally(verticalities,choices,befores,afters,bdaPropsBase):
    schemas = generateDistortionSchemas(choices,befores,afters,bdaPropsBase)
    distortedVerticalities = []
    count = 1
    for x,pair in enumerate(zip(verticalities,schemas)):
        distorted = distortVerticalityByScheme(pair[0],pair[1])
        distortedVerticalities.append( distorted )
        if x%5 == 0:
            count += 1
    return distortedVerticalities

def preprocessPitches(pitches):
    if pitches[1] < pitches[0]:
        pitches = [pitches[1],pitches[0],pitches[2],pitches[3]]
    if pitches[2] < pitches[0]:
        pitches = [pitches[2],pitches[1],pitches[0],pitches[3]]
    if (pitches[1].pitch_number == 1 and pitches[2].pitch_number == 1) or pitches[1] == pitches[0]:
        return [(pitches[0],),(pitches[2],),(pitches[3],)]
    else:
        return [(pitches[0],),(pitches[1],pitches[2]),(pitches[3],)]
    
def appendLeafToStaff(staff,pitchTuple):
    pitches = list(pitchTuple)
    if len(pitches) == 2:
        staff.append( Chord(pitches,(1,4)) )
    else:
        staff.append( Note(pitches[0],(1,4)) )

def addPitchesToPianoStaffFromList(pianoStaff,pitches):
    notes = reversed(preprocessPitches(pitches))
    for pair in zip(pianoStaff,notes):
        appendLeafToStaff(pair[0],pair[1])

def formatBassStaff(staff):
    c = Clef('bass')
    attach(c,staff)

def makeScoreFromNoteLists(lists):
    score = Score([])
    pianoStaff = make_piano_staff()
    formatBassStaff(pianoStaff[2])
    for l in lists:
        addPitchesToPianoStaffFromList(pianoStaff,l)
    score.append(pianoStaff)
    return score

def formatPiece(score):
    formatScore(score)
    lilypondFile = makeLilypondFile(score)
    formatLilypondFile(lilypondFile)
    show(lilypondFile)
    play(lilypondFile)

def moveWideIntervalFromMiddleToBottom(components):
    if isinstance(components[1],Chord):
        chordPitches = components[1].written_pitches
        #if chordPitches[1].pitch_number == 7:
        if chordPitches[1].pitch_number - chordPitches[0].pitch_number > 5:
            mutate(components[1]).replace( Note(chordPitches[1],components[1].written_duration) )
            mutate(components[2]).replace( Chord([components[2].written_pitch,chordPitches[0]],components[2].written_duration) )
      #  if chordPitches[1].pitch_number - chordPitches[0].pitch_number < -5:
            #print "\tand now components are:",components
    #    if chordPitches[1].pitch_number - chordPitches[0].pitch_number > 5:
        #    mutate(components[1]).replace( Note(chordPitches[1],components[1].written_duration) )
        #    mutate(components[2]).replace( Chord([components[2].written_pitch,chordPitches[0]],components[2].written_duration) )
            #print "\tand now components are:",components

def optimizePhysicalityWhenHomophonic(score):
    pianoStaff = score[0]
    print pianoStaff
    for x,moment in enumerate(iterate(score).by_vertical_moment()):
        starts = moment.start_components
        if len(starts) == 3 and all([not isinstance(x,Tuplet) for x in starts]):
            moveWideIntervalFromMiddleToBottom(starts)

def fixErrantChord(bassNote,middleChord):
    chordPitches = middleChord.written_pitches
    mutate(bassNote).replace( Chord([bassNote.written_pitch,chordPitches[0]],bassNote.written_duration) )
    mutate(middleChord).replace( Note(chordPitches[1],middleChord.written_duration) )

def fixErrantChords(score):
    bassNote = score[0][2][16][-1]
    middleChord = score[0][1][16][-1]
    fixErrantChord(bassNote,middleChord)
    bassNote = score[0][2][14][-2]
    middleChord = score[0][1][14][-2]
    fixErrantChord(bassNote,middleChord)
    bassNote = score[0][2][15][-1]
    middleChord = score[0][1][15][-1]
    fixErrantChord(bassNote,middleChord)
    
            
def makePiece(scale,bdaPropsBase,bdaPropsOrnament):
    verticalityNoteLists = generateVerticalities(scale)
    choices = range(5)
    befores = [ (0,.9),(1,.1),(2,0),(3,0),(4,0) ]
    afters = [ (0,0), (1,.1),(2,.2),(3,.2),(4,.5)]
    verticalityNoteLists = distortBasePitchesProportionally(verticalityNoteLists,choices,befores,afters,bdaPropsBase)
    score = makeScoreFromNoteLists(verticalityNoteLists)
    addMeasuresToPianoStaff(score)
    DistortRhythmProportionally(score)
    optimizePhysicalityWhenHomophonic(score)
    fixErrantChords(score)
    formatPiece(score)
    
scale = tonalanalysistools.Scale('c','minor')
bdaPropsBase = [.2,.7,.1]
bdaPropsOrnament = [.3,.55,.05]
makePiece(scale,bdaPropsBase,bdaPropsOrnament)