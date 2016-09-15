#!/usr/bin/python

OVERITERATE_FACTOR=4

def getIdealIterationNumber(AttractorType, screenDim, subsamplingRate):
	pxSize = subsamplingRate*subsamplingRate*screenDim[0]*screenDim[1]

	idealIter = int(OVERITERATE_FACTOR*pxSize)
	if AttractorType == 'dejong':
		idealIter *=4

	return idealIter

