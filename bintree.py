import sys
import math
import random
import crypt as cr



class Node:
    def __init__(self, id, val):
    	self.id = id
    	self.value = val
    	self.left = None
    	self.right = None
    	self.parent = None

    def set_left(self, nod):
    	self.left = nod
    	self.left.parent = self

    def set_right(self, nod):
    	self.right = nod
    	self.right.parent = self


class binTree(Node):
	def __init__(self, height, blocksPerBucket, passH):
		self.h = height
		self.z = blocksPerBucket
		self.key = passH

		self.nod = {}																		# Create a dictionary to hold the tree nodes

		for level in range(self.h + 1):														# Loop through the tree levels
			
			for i in range(2**level):														# Create 2^level nodes in every level
				self.bucket = []															# Initialize the bucket as a list

				for k in range(self.z):														# Create z dummy blocks for each bucket
					self.dummyName = cr.E(b'------NULL------\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10', self.key)
					self.dummyData = cr.E(b'---Dummy-Data---\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10', self.key)
					self.bucket.append((self.dummyName, self.dummyData))

				self.nod[(level, i)] = Node((level, i), self.bucket)						# Create a node holding a bucket at level 'level'
				
				if level != 0:																# If the current node isn't the root do the following: 
					self.nod[(level, i)].parent = self.nod[(level-1, math.floor(i/2))]		# Set its parent node
					if i%2 == 0:															
						self.nod[(level, i)].parent.set_left(self.nod[(level, i)])			#
					else:																	# Set its left and right children according to its position
						self.nod[(level, i)].parent.set_right(self.nod[(level, i)])			#
	

	# Function P returns the path from a leaf-node to the root of the tree (a list of buckets)
	def P(self, leaf):
		self.currentNode = leaf
		self.path = []
		
		while self.currentNode.parent != None:					# Until you reach the root DO:
			self.path.append(self.currentNode.value)
			self.currentNode = self.currentNode.parent
		self.path.append(self.currentNode.value)				# Append root bucket to the list
		
		return self.path


	# Class method Pl returns the bucket id at level 'level' lying in the path from leaf-node 'leaf' to the root of the tree
	def Pl(self, leaf, level):
		self.currentNode = leaf
		self.currentLevel = self.h

		while self.currentLevel > level:						# Until a certain level is reached DO:
			self.currentNode = self.currentNode.parent			# Move upwards in the leaf's path
			self.currentLevel -= 1

		bucket_id = self.currentNode.id 						# Get the id of the node at this level of leaf's path 

		return bucket_id