import sys
from math import log2
from operator import itemgetter

def tally(table, key):
	if key in table:
		table[key] += 1
	else:
		table[key] = 1

def countCharFreqs(text):
	freqs = {}
	for line in text:
		for char in line:
			tally(freqs, char)

	return freqs, sum(freqs.values())

def getSegmentsInit(text):
	segmentedText = []

	for line in text:
		segmentedText.append(list(line.rstrip()))

	return segmentedText

def countSubstring(substring, text):
	freqs = [line.count(substring) for line in text]
	return sum(freqs)

def countSegmentPair(seg1, seg2, segmentedText):
	count = 0

	for line in segmentedText:
		count += len([i for i in range(len(line)-1) if line[i] == seg1 and line[i+1] == seg2])

	return count

# H = E(I), where I is the self-information of each event (token)
def calcTotalI(freqTable):
	totalTokens = sum(freqTable.values())
	entropy = 0.0
	for key in freqTable:
		p = freqTable[key]/totalTokens
		entropy += p*log2(1.0/p)

	return entropy*totalTokens

# get segment starting at line_i, char_i of text, according to freqTable
def getSegment(char_i, line, freqTable):
	start = end = newEnd = char_i
	while end+1 <= len(line) and len([x for x in freqTable if x.startswith(line[start:newEnd+1])]) > 0:
		newEnd += 1
		if line[start:newEnd] in freqTable:
			end = newEnd

	return line[start:end], end

# create new frequency table in case of a merge
# by adding candidate to old freqTable, and subtracting candidate's frequency from those of merged elements
def getFreqTableIfMerge(seg1, seg2, freqTable, segmentedText):
	freqTableIfMerge = freqTable.copy()

	candidate = seg1 + seg2
	freqTableIfMerge[candidate] = countSegmentPair(seg1, seg2, segmentedText) 

	sys.stderr.write('seg1: ' + repr(freqTableIfMerge[seg1]) + '\t')
	sys.stderr.write('seg2: ' + repr(freqTableIfMerge[seg2]) + '\t')
	sys.stderr.write('candidate: ' + repr(freqTableIfMerge[candidate]) + '\n')

	freqTableIfMerge[seg1] -= freqTableIfMerge[candidate]
	if freqTableIfMerge[seg1] == 0: del freqTableIfMerge[seg1]
	freqTableIfMerge[seg2] -= freqTableIfMerge[candidate]
	if freqTableIfMerge[seg2] == 0: del freqTableIfMerge[seg2]

	return freqTableIfMerge, freqTableIfMerge[candidate]

def updateSegmentedText(seg1, seg2, segmentedText):
	for line_i in range(len(segmentedText)):
		line = segmentedText[line_i]
		segsToDel = set([])
		for i in range(len(line)-1):
			if line[i] == seg1 and line[i+1] == seg2:
				segmentedText[line_i][i] = seg1+seg2
				segsToDel.add(i+1)
		segmentedText[line_i] = [line[i] for i in range(len(line)) if i not in segsToDel]

def mergeSegments(text):
	freqTable, totalChars = countCharFreqs(text)
	segmentedText = getSegmentsInit(text)
	
	rejectedMergers = set([])
	totalI = calcTotalI(freqTable)
	for line_i in range(len(segmentedText)):
		seg_i = 0
		while seg_i < len(segmentedText[line_i])-1:
			seg1, seg2 = segmentedText[line_i][seg_i], segmentedText[line_i][seg_i+1]
			candidate = seg1 + seg2

			sys.stderr.write(repr((seg1, seg2)) + '\n')
			sys.stderr.write('Entries in freqTable: ' + repr(len(freqTable)) + '\n')

			if candidate in freqTable or candidate in rejectedMergers:
				seg_i += 1
				continue
			else:
				freqTableIfMerge, candidateFreq = getFreqTableIfMerge(seg1, seg2, freqTable, segmentedText)
				sys.stderr.write('In mergeSegments, freq(' + candidate + '): ' + repr(freqTableIfMerge[candidate]) + '\n')
				
				totalIIfMerge = calcTotalI(freqTableIfMerge)
				if totalIIfMerge < totalI and candidateFreq > 1:
					sys.stderr.write('Merge\n')
					freqTable = freqTableIfMerge
					totalI = totalIIfMerge
					updateSegmentedText(seg1, seg2, segmentedText)
				else:
					sys.stderr.write('No merge\n')
					rejectedMergers.add(candidate)
					seg_i += 1

			sys.stderr.write('\n')

	return freqTable, totalI, totalChars

def printTable(table):
	for k, v in sorted(table.items(), key=itemgetter(1), reverse=True):
		sys.stdout.write('\t'.join([k, repr(v)]) + '\n')
	sys.stdout.write('\n')

def printMetric(totalI, totalChars):
	sys.stdout.write('Expected self-information per character: ' + repr(totalI/totalChars) + '\n')

with open(sys.argv[1]) as inputFile:
	text = inputFile.readlines()
	freqTable, totalI, totalChars = mergeSegments(text)
	printTable(freqTable)
	printMetric(totalI, totalChars)
