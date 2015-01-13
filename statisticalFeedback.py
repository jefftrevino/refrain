from random import randint, uniform, random
from math import *

def wChoice( theList ): #makes a weighted choice (by Kevin Parks at snippets.dzone.com)
	n = uniform(0, 1)
	for item, weight in theList:
		if n < weight:
			break
		n = n - weight
	return item

#for the most part, you like half-cosine interpolations that get quantized:
	
def get_value_between_bounds_along_cosine_curve(a,b,theWayThere):
	y = cos(pi * (3/2.0 + 1/2.0 * theWayThere))
	value = (1-y)*a[1] + y*b[1]
	return value
	

def list_n_samples_between_bounds_along_cosine_curve(a,b, numSamples):
		interp = get_value_between_bounds_along_cosine_curve
		increment = 1.0/numSamples
		values = [interp(a,b,x * increment) for x in range(numSamples + 1)]
		roundedValues = [round(x) for x in values]
		return values

def makeInterpWeights(choices, befores, afters, wayThere):
	#input: 1) choices. 2)weights before interp. 3) weights after interp. 4) how far through interp (0 to 1).
	#output: a weights list that depends on a variable called "wayThere" that goes between 0 and 1.
	# for use with wChoice, z.b.  :
	#abjad> wChoice(makeInterpWeights([0,1],[0,1],[1,0],0))
	#(weights are [(0, -1.8369701987210297e-16), (1, 1.0000000000000002)])
	#1
	#abjad> wChoice(makeInterpWeights([0,1],[0,1],[1,0],1))
	#[(0, 1.0), (1, 0.0)]
	weights = []
	for x in range(len(choices)):
	    weight = (  choices[x], get_value_between_bounds_along_cosine_curve(befores[x],afters[x],wayThere) )
	    weights.append(weight)	
	return weights
	
def wChoiceInterp(choices,befores,afters,wayThere):
	# wrapper for previous function.
	choice = wChoice(makeInterpWeights(choices,befores,afters,wayThere))
	return choice


def probToInterpInterp(weightsStart,weightsDone,numItems,bdaProps):
	#input: 1) list of (choice,weight) tuples; elements must be ordered along a continuum. 2) number of elements to choose. 3) a bda tuple which determines the ratios of before, during, and after choices. Before choices will be made according to probabilities. After choices will proceed along a continuum.
	#output: weighted choice from weights.
	#comment: given a list of weights, and endpoints to a curve, make a half-cosine interpolation that determines whether or not to make a probablity-based weighted choice or to make a choice along a half-cosine interpolation from the first element to the last element of the choices in the weights.
	#NOTE -- while "wayThere" determines which item to select, the bda envelope effects only the interpolation between probabilities of choosing from probabilities vs. choosing from an interpolation. 
	
	#TODO: use wChoiceInterp([choices,befores,afters,wayThere) to change weights as transition happens.]
	bdaItems  = bdaPropsToItems(numItems,bdaProps)
	outputs = []
	before = bdaItems[0]
	during = bdaItems[1]
	after = bdaItems[2]
	for x in range(before):
		wayThere = float(x/dur)
		probOrInterp= wChoice([  ( 0,1 ),  (1,0) ])
		if probOrInterp == 0:
			output = wChoice(weights)
		if probOrInterp == 1:
			choices = [x[0] for x in weights]
			output = iChoice(weights,wayThere)
		outputs.append(output)
	for x in range(during):
		wayThere = float(x/dur)
		probOrInterp= wChoice([  ( 0, get_value_between_bounds_along_cosine_curve(1,0,wayThere) ),  (1, get_value_between_bounds_along_cosine_curve(0,1,wayThere)) ])
		if probOrInterp == 0:
			output = wChoice(weights)
		if probOrInterp == 1:
			choices = [x[0] for x in weights]
			output = iChoice(weights,wayThere)
		outputs.append(output)
	return outputs
	
def iChoice(weights,wayThere):
	#input: 1)list of (choice, distance) tuples 2) how far between 0 and 1 the transition has gone (float).
	#output: selected choice. (dynamic type)
	#comment: arranges a list of choices along a continuum according to the distances part of the tuples. Note that a list of (choice,distance) tuples looks identical to a list of (choice,weight) tuples.
	n = wayThere
	for item, weight in weights:
		if n < weight:
			break
		n = n - weight
	return item
		
def bdaPropsToItems(numItems,bdaProps):
#input: 1) dur -- the number of items for the transition. 2) bdaProps -- a list of proportions [before,during,after] that indicates the proportions of items to be before, during, or after the interpolation respectively. The numbers should add up to one.
#output: a three-int list of the number of items before, during, and after the interpolation.
#comment: Converts a list of decimal proportions to closest fractions and returns a list of before, during, and after item numbers. sample input: (10,[.33333,.33333,.33333]) sample output: [3,3,4] Note -- if the numerators of the fractions add up to a number smaller or larger than the total number of items, the number of items in the "after" segment will make up for the difference.
	fractProps = []
	for x in range(len(bdaProps)):
		minError = 100000
		bestY = 0
		for y in range(numItems):
			localError = abs( y/float(numItems) - bdaProps[x]) 
			if localError < minError:
				minError = localError
				bestY = y
		fractProps.append((bestY,numItems)) 
	#if anything's left over, add it to the "during" fraction.
	itemNums = [x[0] for x in fractProps]
	listSum = reduce(lambda x, y: x + y, itemNums)
	diff = numItems - listSum
	fractProps[-1] = (fractProps[-1][0]+diff,numItems)
	return [x[0] for x in fractProps]
	#1/3,1/3, and 1/3 should be 3,3,4.
	
def bdaInterp(choices,befores,afters,numItems,bdaProps):
	#input: 1) choices; 2) weights when wayThere is 0; 3) weights when wayThere is 1; 4) numItems to choose; 5) proportions of before, during, and after for the interpolation.
	bda = bdaPropsToItems(numItems,bdaProps)
	output = []
	for x in range(bda[0]):
		output.append(   wChoiceInterp(choices,befores,afters,0)    )
	for x in range(bda[1]):
		wayThere = x/float(bda[1])
		output.append(   wChoiceInterp(choices,befores,afters,wayThere)   )
	for x in range(bda[2]):
		output.append(   wChoiceInterp(choices,befores,afters,wayThere)   )
	return output