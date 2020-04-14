import os
import sys
import math
import random
import bintree as bt
import crypt as cr
import json
import odnode




password = 'myP@th0rAM'							# Define the local password
passHash = cr.H(password)						# Hash the local password in order to use it as a key for AES
Z = 4											# Define the number of blocks in a bucket


BS = 16																#
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)		# pad and unpad methods used to match AES block size
unpad = lambda s: s[:-ord(s[len(s)-1:])]							#


def oramAccess(op, block_node):
	global S
	S = []										# Initialize local stash as a list of tuples
	oramPath = []
	
	if op != 'readandremove' and op != 'add': raise ValueError
	
	def writeBucket(bucketID, block_list):
		while len(block_list) < Z:																					# Pad the bucket with dummy ..
			block_list.append(('----------------', '----------------', '9999999999999999', '----------------'))	  	# .. blocks until its size is Z
		
		# Encrypt the bucket blocks to be written in the ORAM
		enBucket = [(cr.E(bytes(pad(bl[0]).encode('utf-8')), passHash),
		cr.E(bytes(pad(bl[1]).encode('utf-8')), passHash),
		cr.E(bytes(pad(str(bl[2])).encode('utf-8')), passHash),
		cr.E(bytes(pad(str(bl[3])).encode('utf-8')), passHash)) for bl in block_list]
		# Write the encrypted bucket in the ORAM
		oram.nod[bucketID].value = enBucket									

	jnode = json.dumps(block_node.__dict__)			# Serialize object block_node to JSON
	dnode = json.loads(jnode)						# Turn JSON into python dictionary
	
	x = dnode['pos']
	oramPath = oram.P(oram.nod[L, x])				# Get the path of leaf x and store it locally in a list of buckets
	
	# Add to the local stash S the decrypted blocks of the oramPath list
	for l in range(L+1):
		for b in range(Z):
			blockContent = (unpad(cr.D(oramPath[l][b][0], passHash).decode('utf-8')),
			unpad(cr.D(oramPath[l][b][1], passHash).decode('utf-8')),
			int(unpad(cr.D(oramPath[l][b][2], passHash).decode('utf-8'))),
			unpad(cr.D(oramPath[l][b][3], passHash).decode('utf-8')))
			if blockContent[0] != '----------------':
				S.append(blockContent)

	block = next((a for a in S if a[0] == dnode['label']), ('None', 'Null', 0, {}))	# Read the block in question from the local stash

	if op == 'add':																	# If the operation is 'add':
		print('(Add)')
		if block in S:
			S.remove(block)															# Remove the old block from the stash if it's there
		S.append((dnode['label'], dnode['data'], dnode['pos'], dnode['chPos']))		# Add the new block, data and its children positions or the old block with new data
	
	if block in S:
		S.remove(block)
	S_temp = []
	for l in range(L, -1, -1):
		S_temp = [b for b in S if oram.Pl(oram.nod[L, x], l) == oram.Pl(oram.nod[L, b[2]], l)]	# S_temp = {b in S : P(x, l) = P(position[b], l)}
		S_temp = S_temp[:min(len(S_temp), Z)]													# S_temp = {Select min(|S_temp|, Z) elements from S_temp}
		S = [item for item in S if item not in S_temp]											# S = S - S_temp
		writeBucket(oram.Pl(oram.nod[L, x], l), S_temp)											# WriteBucket(P(x, l), S_temp)

	if op == 'readandremove':
		print('(ReadAndRemove)')
		askedBlock = odnode.Odnode(block[0], block[1], block[2], json.loads(str(block[3]).replace("'", '"')))
		return askedBlock



###########################  Initial data entry functions  ###########################

def dataInput(Ν):
	print('\n\nInitial data entry')
	print('------------------')
	
	global root
	global top 
	for i in range(N):
		blockLabel = input('Label of {} No. {}: '.format(blockAlias, i))
		blockData = input('Data of {} No. {}: '.format(blockAlias, i))
		print()
		pos = random.randint(0, 2**L - 1)
		blkNode = odnode.Odnode(blockLabel, blockData, pos, {})		# Create instance of Odnode class and assign the values of the current block (node)
		blocks.append(blkNode)										# Construct a list holding the data blocks (nodes) 								

	# Store children's positions in a dictionary for each node
	for i, j in enumerate(blocks):											
		if i < len(blocks)-1:									
			cName = blocks[i+1].label								# Assign to cName current block's child label
			cPos = blocks[i+1].pos									# Assign to cPos current block's child position
			j.chPos = {cName : cPos}								# Add to current block the pair {Child_id : position}
			if i == 0:												# Store the root of the ..
				root = j											# .. data structure in variable 'root'
	top = blocks[len(blocks)-1]										# Store last node of the list in 'top'

	# Write given data blocks in ORAM	
	for k in blocks:
		oramAccess('add', k)

###################################################################

def heapify(nodelist, index, N):
	left = 2*index + 1
	right = 2*index + 2

	if (left < N) and (int(nodelist[left].data) < int(nodelist[index].data)):
		smallest = left
	else:
		smallest = index

	if (right < N) and (int(nodelist[right].data) < int(nodelist[smallest].data)):
		smallest = right

	if smallest != index:
		nodelist[index], nodelist[smallest] = nodelist[smallest], nodelist[index]	# Perform swap if needed
		heapify(nodelist, smallest, N)
	blocks[:] = nodelist

###################################################################

def dataInputHeap(Ν):
	print('\n\nInitial data entry')
	print('------------------')
	
	global root
	global last
	for i in range(N):
		blockLabel = input('ID of {} No. {}: '.format(blockAlias, i))
		blockData = input('Key of {} No. {}: '.format(blockAlias, i))
		print()
		pos = random.randint(0, 2**L - 1)
		blkNode = odnode.Odnode(blockLabel, blockData, pos, {})		# Create instance of Odnode class and assign the values of the current block (node)
		blocks.append(blkNode)										# Construct a list holding the data blocks (nodes)

	
	# Calculate the last parent node depending on input size
	lastParent = math.floor(len(blocks)/2) - 1

	# Heapify 
	for i in range(lastParent, -1, -1):
		heapify(blocks, i, N)			
	
	last = len(blocks)


	# Store children's positions in a dictionary for each node
	for i, j in enumerate(blocks):											
		if i <= lastParent:											# Until we reach the index of the parent of last node in the heap									
			indexLeft = 2*i + 1										# Calculate the index of left child
			indexRight = 2*i + 2									# Calculate the index of right child
			cLName = blocks[indexLeft].label						# Assign to cLName current block's Left child label
			cLPos = blocks[indexLeft].pos							# Assign to cLPos current block's Left child position
			if indexRight < len(blocks):
				cRName = blocks[indexRight].label					# Assign to cRName current block's Right child label
				cRPos = blocks[indexRight].pos						# Assign to cRPos current block's Right child position
				j.chPos = {cLName : cLPos, cRName : cRPos}			# Add to current block the children positions dictionary
			else:
				j.chPos = {cLName : cLPos}							# The current node has only a left child
			if i == 0:												# Store the root of the ..
				root = j											# .. data structure in variable 'root'

	# Write given data blocks in ORAM	
	for k in blocks:
		oramAccess('add', k)






##############################   ODS Framework Functions   ############################## 


def odsStart():								# Update cache to contain the root
	global cache
	global root
	cache.clear()
	if root != None:
		cache.append(root)



###################  Read  ###################

def read(nodeLabel):
	global cache
	
	isInCache = any(x.label == nodeLabel for x in cache)						# True if the block in question is already in cache
	if isInCache == False:
		n = 0
		while isInCache == False:												#
			childDictKeys = list(cache[n].chPos.keys())							#
			childName = childDictKeys[0]										# 
			childPosition = cache[n].chPos[childName]							# Traverse through the nodes .. 
			if not any(x.label == childName for x in cache):					# .. using their children positions ..
				ask = odnode.Odnode(childName, 'null', childPosition, {})		# .. until the requested one is found.
				fetch = oramAccess('readandremove', ask)						# 
				cache.append(fetch)												#
			isInCache = any(x.label == nodeLabel for x in cache)				#
			n += 1																#
	return cache[-1]															# Return the last object (node) in cache



####################  Insert  ####################

def insert(newNodeLabel, newNodeData):
	global cache
	global root
	global top

	newNode = odnode.Odnode(newNodeLabel, newNodeData, 0, {})		# Create Odnode instance for the new block (node)
	
	if cache != []:
		read(top.label)
	else:
		root = newNode

	cache.append(newNode)												# Insert new block in cache



################   Update(Write)   ################

def write(nodeLabel, newData):
	global cache
	isInCache = any(x.label == nodeLabel for x in cache)				# True if the block in question is already in cache
	if isInCache == False:
		read(nodeLabel)
	next((n for n in cache if n.label == nodeLabel)).data = newData



#################   Delete   #################

def delete(nodeLabel):
	global cache
	global root

	if len(cache) == 0:
		print('\nThe Oblivious Data Structure is empty!\n')
	elif len(cache) == 1 and cache[0].chPos == {}:
		cache.clear()
		root = None
	else:
		#isInCache = any(x.label == nodeLabel for x in cache)				# True if the block in question is already in cache
		node = read(nodeLabel)
		
		if node.chPos == {}:
			cache[-2].chPos = cache[-1].chPos								# Pass the chPos of last node to the previous one
		else:
			read(list(node.chPos.keys())[0])								# Bring root's next node into cache
		
		cache.remove(next((n for n in cache if n.label == nodeLabel)))
		


################   Finalize   ################

def finalize(typeIs):
	global cache
	global root
	global top

	if cache != []:
		# Assign new random position to each node in cache
		for n in cache:
			pos = random.randint(0, 2**L - 1)
			n.pos = pos
																	
		# Update children's positions in each node
		if typeIs == 'linear':
			for i, j in enumerate(cache):											
				if i < len(cache)-1:									
					cName = cache[i+1].label					# Assign to cName current block's child label
					cPos = cache[i+1].pos						# Assign to cPos current block's child position
					j.chPos = {cName : cPos}					# Add to current block the pair {Child_id : position}
					if i == 0:									# Store the root of the ..
						root = j								# .. data structure in variable 'root'
			top = cache[len(cache)-1]							# Store last node of the list in 'top'
		
		if typeIs == 'tree_path':
			for i, j in enumerate(cache):											
				if i < len(cache)-1:									# Until we reach the parent of last node in cache									
					cName = cache[i+1].label							# Assign to cName current block's child label
					cPos = cache[i+1].pos								# Assign to cPos current block's child position map
					j.chPos[cName] = cPos
					if i == 0:											# Store the root of the ..
						root = j										# .. data structure in variable 'root'

		# Write cahe back to ORAM
		for k in cache:
			oramAccess('add', k)
		
		# Empty client cache
		cache.clear()








###############################  Main program loop  ###############################
while True:

	#S = []											# Initialize local stash as a list
	#position = {}									# Initialize position map as a dictionary
	blocks = []										# Initialize the list holding the data blocks (nodes)
	cache = []										# Initialize local (client) cache

	os.system('clear')											
	print('\n\nODS (Oblivious Data Structure) CREATION')
	print('---------------------------------------')
	print('\n[1] --> Oblivious Stack')
	print('\n[2] --> Oblivious Queue')
	print('\n[3] --> Oblivious Heap')
	print('\n[4] --> Oblivious AVL Tree')
	print('\n[5] --> Path ORAM explorer')
	print('\n[ENTER] --> EXIT\n\n\n')

	oblStruct = input('Please enter your selection : ')
	
	if (oblStruct != '5') and (oblStruct != ''):
		N = int(input('\nInitial number of items/nodes = '))		# Get the number of items the stack will contain
		L = math.ceil(math.log(N, 2))								# Calculate path-oram's tree height L 
		oram = bt.binTree(L, Z, passHash)							# Construct an instance of the binTree class with the given parametres

	if oblStruct == '1':
		cache.clear()
		os.system('clear')
		blockAlias = 'item'
		print('\n\nOBLIVIOUS STACK')
		print('---------------')
		dataInput(N)
		
		while True:
			# present stack menu
			os.system('clear')
			
			print('\n\nOblivious Stack Options')
			print('-----------------------')
			print('\n[1] --> Push(item)')
			print('\n[2] --> Pop()')
			print('\n[3] --> IsEmpty()')
			print('\n[ENTER] --> EXIT\n\n\n')

			select = input('Please enter your selection : ')

			if select == '':
				break

			odsStart()
			if select == '1':
				newBlockName = input('\nEnter the ID of the item you want to push : ')
				newBlockData = input("Enter the data of item '{0}' : ".format(newBlockName))

				def push(node, data):
					insert(node, data)
					finalize('linear')
				
				push(newBlockName, newBlockData)

				print('\nOperation finished successfully!')
				input('\nPlease press [ENTER] to continue...')
		
			if select == '2':

				def pop():
					global cache
					global root
					global top

					oldTop = top
					if root != None:
						delete(top.label)			
						finalize('linear')
					else:
						oldTop = None
					
					return oldTop
				
				topItem = pop()
				if topItem != None:
					print('\nItem ID :', topItem.label)
					print('Item Data :', topItem.data)
				else:
					print('\nThe Oblivious Stack is empty!')
				
				input('\nPlease press [ENTER] to continue...')

			
			if select == '3':
				
				def isEmpty():
					return (len(cache) == 0)

				ans = isEmpty()
				if ans:
					print('\nTRUE - The Oblivious Stack is empty.')
				else:
					print('\nFALSE - The Oblivious Stack is NOT empty.')
				
				input('\nPlease press [ENTER] to continue...')




	elif oblStruct == '2':
		cache.clear()
		os.system('clear')
		blockAlias = 'item'
		print('\n\nOBLIVIOUS QUEUE')
		print('---------------')
		dataInput(N)
		
		while True:
			# present queue menu
			os.system('clear')
			
			print('\n\nOblivious Queue Options')
			print('-----------------------')
			print('\n[1] --> Enqueue(item)')
			print('\n[2] --> Dequeue()')
			print('\n[3] --> IsEmpty()')
			print('\n[ENTER] --> EXIT\n\n\n')

			select = input('Please enter your selection : ')

			if select == '':
				break

			odsStart()
			if select == '1':
				newBlockName = input('\nEnter the ID of the item you want to enqueue : ')
				newBlockData = input("Enter the data of item '{0}' : ".format(newBlockName))

				def enqueue(node, data):
					insert(node, data)
					finalize('linear')
				
				enqueue(newBlockName, newBlockData)

				print('\nOperation finished successfully!')
				input('\nPlease press [ENTER] to continue...')
		
			if select == '2':

				def dequeue():
					global cache
					global root
					
					tail = ()

					if root != None:
						tail = (root.label, root.data)
						delete(root.label)
						if cache != []:
							root = cache[0]
						finalize('linear')
					return tail
				
				tailItem = dequeue()
				if tailItem != ():
					print('\nItem ID :', tailItem[0])
					print('Item Data :', tailItem[1])
				else:
					print('\nThe Oblivious Queue is empty!')
				
				input('\nPlease press [ENTER] to continue...')
			
			if select == '3':
				
				def isEmpty():
					return (len(cache) == 0)

				ans = isEmpty()
				
				if ans:
					print('\nTRUE - The Oblivious Queue is empty.')
				else:
					print('\nFALSE - The Oblivious Queue is NOT empty.')
				
				input('\nPlease press [ENTER] to continue...')



	elif oblStruct == '3':
		cache.clear()
		os.system('clear')
		blockAlias = 'element'
		print('\n\nOBLIVIOUS HEAP (PRIORITY QUEUE)')
		print('-------------------------------')
		dataInputHeap(N)

		def readPath(operation):
			global cache
			global root
			global last

			depth = math.floor(math.log2(last))
			currentNode = oramAccess('readandremove', root)

			binLast = last + 1
			
			if ((binLast & (binLast - 1)) != 0) or (operation == 'extract'):				# Last node is not at the end of a tree row
				for k in range(depth-1, 0, -1):
					# Check if the last parent has already 2 children. If yes, go to the next
					if k == 1 and (last % 2 == 1) and (operation == 'insert'):
						ind = math.floor(last/2)
					else:
						ind = math.floor(last/math.pow(2,k)) - 1

					if (ind % 2) == 1:
						leftChildLabel = list(currentNode.chPos.keys())[0]
						leftChildPos = currentNode.chPos[leftChildLabel]
						ask = odnode.Odnode(leftChildLabel, 'null', leftChildPos, {})		# Ask for the left child .. 
						fetch = oramAccess('readandremove', ask)							# .. to be fetched from ORAM		
					else:
						rightChildLabel = list(currentNode.chPos.keys())[1]
						rightChildPos = currentNode.chPos[rightChildLabel]
						ask = odnode.Odnode(rightChildLabel, 'null', rightChildPos, {})		# Ask for the right child .. 
						fetch = oramAccess('readandremove', ask)							# .. to be fetched from ORAM
					
					cache.append(fetch)														# Append fetched node to cache
					currentNode = fetch
			else:
				for k in range(depth):
					leftChildLabel = list(currentNode.chPos.keys())[0]
					leftChildPos = currentNode.chPos[leftChildLabel]
					ask = odnode.Odnode(leftChildLabel, 'null', leftChildPos, {})			# Ask for the left child .. 
					fetch = oramAccess('readandremove', ask)								# .. to be fetched from ORAM
					cache.append(fetch)														# Append fetched node to cache
					currentNode = fetch	
		

		while True:
			# present heap menu
			os.system('clear')
			
			print('\n\nOblivious Heap Options')
			print('----------------------')
			print('\n[1] --> Insert(element)')
			print('\n[2] --> ExtractMin()')
			print('\n[3] --> IsEmpty()')
			print('\n[ENTER] --> EXIT\n\n\n')

			select = input('Please enter your selection : ')

			if select == '':
				break

			odsStart()
			if select == '1':
				newBlockName = input('\nEnter the ID of the element you want to insert : ')
				newBlockData = input("Enter the key of element '{0}' : ".format(newBlockName))	
				
				def insertKey(id, key):
					readPath('insert')
					print([(a.label, a.data, a.pos, a.chPos) for a in cache])
					newNode = odnode.Odnode(id, key, 0, {})											# Create Odnode instance for the new node
					cache.append(newNode)															# Append new node in cache
					cache[-2].chPos[cache[-1].label] = cache[-1].pos								# Attach new node to the heap

					#################################  Upheap  #################################
					k = len(cache)-1
					while (k > 0) and (int(cache[k].data) < int(cache[k-1].data)):
						cache[k-1].label, cache[k].label = cache[k].label, cache[k-1].label			# Swap cache objects id's to restore order
						cache[k-1].data, cache[k].data = cache[k].data, cache[k-1].data				# Swap cache objects keys to restore order
						
						childKeys = list(cache[k-1].chPos.keys())
						
						######################################################################## If swapped node was left child
						if childKeys[0] == cache[k-1].label:
							if len(childKeys) == 2:										
								newPos = {cache[k-1].label : cache[k].label, childKeys[1] : childKeys[1]}
								cache[k-1].chPos = dict((newPos[key], value) for (key, value) in cache[k-1].chPos.items())
							else:
								newPos = {cache[k-1].label : cache[k].label}
								cache[k-1].chPos = dict((newPos[key], value) for (key, value) in cache[k-1].chPos.items())
							# If swapped node hasn't reached the root
							if k-2 >= 0:
								childKeysParent = list(cache[k-2].chPos.keys())
								# If swapped node was left child
								if childKeysParent[0] == cache[k].label:
									newPosParent = {cache[k].label : cache[k-1].label, childKeysParent[1] : childKeysParent[1]}
									cache[k-2].chPos = dict((newPosParent[key], value) for (key, value) in cache[k-2].chPos.items())
								# If swapped node was right child
								if childKeysParent[1] == cache[k].label:
									newPosParent = {childKeysParent[0] : childKeysParent[0], cache[k].label : cache[k-1].label}
									cache[k-2].chPos = dict((newPosParent[key], value) for (key, value) in cache[k-2].chPos.items())

						######################################################################## If swapped node was right child
						if len(childKeys) > 1 and childKeys[1] == cache[k-1].label:										
							newPos = {childKeys[0] : childKeys[0], cache[k-1].label : cache[k].label}
							cache[k-1].chPos = dict((newPos[key], value) for (key, value) in cache[k-1].chPos.items())
							# If swapped node hasn't reached the root
							if k-2 >= 0:
								childKeysParent = list(cache[k-2].chPos.keys())
								# If swapped node was left child
								if childKeysParent[0] == cache[k].label:
									newPosParent = {cache[k].label : cache[k-1].label, childKeysParent[1] : childKeysParent[1]}
									cache[k-2].chPos = dict((newPosParent[key], value) for (key, value) in cache[k-2].chPos.items())
								# If swapped node was right child
								if childKeysParent[1] == cache[k].label:
									newPosParent = {childKeysParent[0] : childKeysParent[0], cache[k].label : cache[k-1].label}
									cache[k-2].chPos = dict((newPosParent[key], value) for (key, value) in cache[k-2].chPos.items())
						
						k -= 1

					finalize('tree_path')
				
				insertKey(newBlockName, newBlockData)

				print('\nOperation finished successfully!')
				input('\nPlease press [ENTER] to continue...')
		
			if select == '2':

				def extractMin():
					global cache
					global root
					global last

					readPath('extract')
					currentNode = cache[-1]
					# If last node in cache is not a leaf, fetch another one
					if currentNode.chPos != {}:													
						ind = last - 1
						if (ind % 2) == 1:
							leftChildLabel = list(currentNode.chPos.keys())[0]
							leftChildPos = currentNode.chPos[leftChildLabel]
							ask = odnode.Odnode(leftChildLabel, 'null', leftChildPos, {})		# Ask for the left child .. 
							fetch = oramAccess('readandremove', ask)							# .. to be fetched from ORAM		
						else:
							rightChildLabel = list(currentNode.chPos.keys())[1]
							rightChildPos = currentNode.chPos[rightChildLabel]
							ask = odnode.Odnode(rightChildLabel, 'null', rightChildPos, {})		# Ask for the right child .. 
							fetch = oramAccess('readandremove', ask)							# .. to be fetched from ORAM
						
						cache.append(fetch)														# Append fetched node to cache

					min = (cache[0].label, cache[0].data)										# Assign minimum element to min
					cache[0].label = cache[-1].label											# Last element becomes the new .. 
					cache[0].data  = cache[-1].data												# .. root leaving chPos's as they are
					del cache[-1]																# Remove last element from cache
					del cache[-1].chPos[cache[0].label]											# Remove previous last element from its parent's chPos dictionary
					#print([(a.label, a.data, a.pos, a.chPos) for a in cache])
					print('Minimum :', min)
					finalize('tree_path')

					
					#################################  Downheap  #################################
					
					odsStart()
					oramAccess('readandremove', root)
					currentNode = cache[0]
					previousNode = None

					k = 0
					while k < last:
						childKeys = list(currentNode.chPos.keys())
						if len(childKeys) > 0:														# If current node has at least 1 child
							leftChildLabel = list(currentNode.chPos.keys())[0]
							leftChildPos = currentNode.chPos[leftChildLabel]
							ask = odnode.Odnode(leftChildLabel, 'null', leftChildPos, {})			# Ask for the left child .. 
							leftChild = oramAccess('readandremove', ask)							# .. to be fetched from ORAM
							cache.append(leftChild)													# Add left child to cache
							indexLeft = cache.index(cache[-1])
							rightChild = None														# Initialize right child node												
						if len(childKeys) > 1:														# If current node has 2 children
							rightChildLabel = list(currentNode.chPos.keys())[1]
							rightChildPos = currentNode.chPos[rightChildLabel]
							ask = odnode.Odnode(rightChildLabel, 'null', rightChildPos, {})			# Ask for the right child .. 
							rightChild = oramAccess('readandremove', ask)							# .. to be fetched from ORAM
							cache.append(rightChild)												# Add right child to cache
							indexRight = cache.index(cache[-1])
						if len(childKeys) == 0:
							# The node has no children
							break
						
						if rightChild != None:
							if leftChild.data < rightChild.data:
								if currentNode.data > leftChild.data:
									currentNode.label, cache[indexLeft].label = cache[indexLeft].label, currentNode.label			# Swap cache objects id's to restore order
									currentNode.data, cache[indexLeft].data = cache[indexLeft].data, currentNode.data				# Swap cache objects keys to restore order
									# Correction of the chPos dictionary (label:data) pairs in current node									
									if len(childKeys) == 2:										
										newPos = {currentNode.label : cache[indexLeft].label, childKeys[1] : childKeys[1]}
										currentNode.chPos = dict((newPos[key], value) for (key, value) in currentNode.chPos.items())
									else:
										newPos = {currentNode.label : cache[indexLeft].label}
										currentNode.chPos = dict((newPos[key], value) for (key, value) in currentNode.chPos.items())
									# Correction of the chPos dictionary (label:data) pairs in previous node
									if previousNode != None:
										previousChildKeys = list(previousNode.chPos.keys())
										if cache[indexLeft].label == previousChildKeys[0]:						# If swapped node was a left child
											newPos = {cache[indexLeft].label : currentNode.label, previousChildKeys[1] : previousChildKeys[1]}
											previousNode.chPos = dict((newPos[key], value) for (key, value) in previousNode.chPos.items())
										else:																	# If swapped node was a right child
											newPos = {previousChildKeys[0] : previousChildKeys[0], cache[indexLeft].label : currentNode.label}
											previousNode.chPos = dict((newPos[key], value) for (key, value) in previousNode.chPos.items())
									previousNode = currentNode													# Assign current node to previousNode
									currentNode = cache[indexLeft]												# Let current node be the left child
									k = 2*k + 1																	# Move node index to left child
								else:
									# The root node reached the right position in the heap
									break																
							else:
								if currentNode.data > rightChild.data:
									currentNode.label, cache[indexRight].label = cache[indexRight].label, currentNode.label			# Swap cache objects id's to restore order
									currentNode.data, cache[indexRight].data = cache[indexRight].data, currentNode.data				# Swap cache objects keys to restore order
									# Correction of the chPos dictionary (label:data) pairs in current node									
									newPos = {childKeys[0] : childKeys[0], currentNode.label : cache[indexRight].label}
									currentNode.chPos = dict((newPos[key], value) for (key, value) in currentNode.chPos.items())
									# Correction of the chPos dictionary (label:data) pairs in previous node
									if previousNode != None:
										previousChildKeys = list(previousNode.chPos.keys())
										if cache[indexRight].label == previousChildKeys[0]:						# If swapped node was a left child
											newPos = {cache[indexRight].label : currentNode.label, previousChildKeys[1] : previousChildKeys[1]}
											previousNode.chPos = dict((newPos[key], value) for (key, value) in previousNode.chPos.items())
										else:																	# If swapped node was a right child
											newPos = {previousChildKeys[0] : previousChildKeys[0], cache[indexRight].label : currentNode.label}
											previousNode.chPos = dict((newPos[key], value) for (key, value) in previousNode.chPos.items())
									previousNode = currentNode													# Assign current node to previousNode
									currentNode = cache[indexRight]												# Let current node be the right child
									k = 2*k + 2																	# Move node index to right child
								else:
									# The root node reached the right position in the heap
									break
						else:
							if currentNode.data > leftChild.data:
								currentNode.label, cache[indexLeft].label = cache[indexLeft].label, currentNode.label			# Swap cache objects id's to restore order
								currentNode.data, cache[indexLeft].data = cache[indexLeft].data, currentNode.data				# Swap cache objects keys to restore order
								# Correction of the chPos dictionary (label:data) pairs in parent node									
								if len(childKeys) == 2:										
									newPos = {currentNode.label : cache[indexLeft].label, childKeys[1] : childKeys[1]}
									currentNode.chPos = dict((newPos[key], value) for (key, value) in currentNode.chPos.items())
								else:
									newPos = {currentNode.label : cache[indexLeft].label}
									currentNode.chPos = dict((newPos[key], value) for (key, value) in currentNode.chPos.items())
							break
					print([(a.label, a.data, a.pos, a.chPos) for a in cache])
					finalize('heap')
		
				extractMin()
				
				input('\nPlease press [ENTER] to continue...')

			
			if select == '3':
				
				def isEmpty():
					return (len(cache) == 0)

				ans = isEmpty()
				
				if ans:
					print('\nTRUE - The Oblivious Priority Queue is empty.')
				else:
					print('\nFALSE - The Oblivious Priority Queue is NOT empty.')
				
				input('\nPlease press [ENTER] to continue...')
		
	elif oblStruct == '4':
		cache.clear()
		os.system('clear')
		blockAlias = 'node'
		'''
		print('OBLIVIOUS AVL TREE')
		print('------------------')
		dataInput(N)
		# present AVL menu
		'''
		break

	elif oblStruct == '5':
		while True:
			os.system('clear')
			print('\n\nPath ORAM explorer')
			print('------------------')
			print('\n[1] --> Display the ORAM binary tree (Decrypted)')
			print('\n[2] --> Display the ORAM binary tree (Encrypted)')
			print('\n[ENTER] --> EXIT\n\n\n')

			com = input('Please enter your choice : ')

			if com == '':
				break

			###################  Display the ORAM (Decrypted)  ###################
			elif com == '1':
				print()
				for k in sorted(oram.nod.keys()):
					print('\nBucket id =', k)
					blst = [(unpad(cr.D(oram.nod[k].value[i][0], passHash).decode('utf-8')),
					unpad(cr.D(oram.nod[k].value[i][1], passHash).decode('utf-8')),
					int(unpad(cr.D(oram.nod[k].value[i][2], passHash).decode('utf-8'))),
					unpad(cr.D(oram.nod[k].value[i][3], passHash).decode('utf-8'))) for i in range(Z)]
					print(blst)
				input('\nPlease press [ENTER] to continue...')


			###################  Display the ORAM (Encrypted)  ###################
			elif com == '2':
				print()
				for k in sorted(oram.nod.keys()):
					print('\nBucket id =', k)
					blst = [(oram.nod[k].value[i][0].hex(), oram.nod[k].value[i][1].hex(),
					(oram.nod[k].value[i][2].hex(), oram.nod[k].value[i][3].hex())) for i in range(Z)]
					print(blst)
				input('\nPlease press [ENTER] to continue...')


	elif oblStruct == '':
		break