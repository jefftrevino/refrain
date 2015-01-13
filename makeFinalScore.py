from abjad import *
from os import *

def formatStaff(staff):
    command = indicatortools.LilyPondCommand("#(set-accidental-style 'forget)")
    attach(command,staff)

def formatScore(score):
    #the lowest staff is a bass clef staff.
    for staff in score[0]:
        formatStaff(staff)   
    t = Tempo((1,4),46)
    attach(t,score[0][0])
    b = indicatortools.BarLine(':|.')
    attach(b,score[0][0].select_leaves()[-1])
    moment = schemetools.SchemeMoment(1,16)
    contextualize(score).proportional_notation_duration = moment
    contextualize(score).tuplet_full_length = True
    override(score).spacing_spanner.uniform_stretching = False
    override(score).spacing_spanner.strict_note_spacing = False
    override(score).tuplet_bracket.padding = 2
    override(score).tuplet_number.text = schemetools.Scheme('tuplet-number::calc-fraction-text')
    override(score).metronome_mark.padding = 2
    mark = Dynamic('ff')
    attach(mark,score[0][0][0][0])
    mark = Dynamic('mf')
    attach(mark,score[0][1][0][0])
    mark = Dynamic('ff')
    attach(mark,score[0][2][0][0])

def makeLilypondFile(score):
    lilypondFile = lilypondfiletools.make_basic_lilypond_file(score)
    #lilypondFile.default_paper_size = 'tabloid', 'portrait'
    lilypondFile.global_staff_size = 14
    lilypondFile.layout_block.indent = 0
    lilypondFile.layout_block.ragged_right = True
    lilypondFile.paper_block.top_margin = 15
    lilypondFile.paper_block.left_margin = 20
    lilypondFile.paper_block.right_margin = 15
    lilypondFile.paper_block.markup_system_spacing__basic_distance = 5
    lilypondFile.paper_block.ragged_bottom = False
    lilypondFile.paper_block.system_system_spacing = layouttools.make_spacing_vector(0, 0, 8, 0)
    directory = path.abspath( getcwd() )
    fontTree = directory+'/fontTree.ly'
    lilypondFile.file_initial_user_includes.append(fontTree)
    return lilypondFile

def formatLilypondFile(lilypondFile):
    lilypondFile.paper_block.paper_width = 8.5 * 25.4
    lilypondFile.paper_block.paper_height = 11 * 25.4
    lilypondFile.paper_block.top_margin = 1.0 * 25.4
    lilypondFile.paper_block.bottom_margin = 0.5 * 25.4
    lilypondFile.paper_block.left_margin = 1.0 * 25.4
    lilypondFile.paper_block.right_margin = 1.0 * 25.4
    lilypondFile.paper_block.ragged_bottom = False
    lilypondFile.global_staff_size = 16
    lilypondFile.layout_block.indent = 0
    lilypondFile.layout_block.ragged_right = False
    lilypondFile.paper_block.system_system_spacing = layouttools.make_spacing_vector(30, 0, 0, 0)
    directory = path.dirname(path.abspath(__file__))
    fontTree = path.join(directory,'fontTree.ly')
    lilypondFile.file_initial_user_includes.append(fontTree)
    context_block = lilypondfiletools.ContextBlock()
    #context_block.context_name = r'PianoStaff \RemoveEmptyStaves'
    override(context_block).vertical_axis_group.remove_first = True
    lilypondFile.layout_block.context_blocks.append(context_block)
