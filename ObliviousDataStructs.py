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
		askedBlock = odnode.Odnode(block[0], block[1], block[2], json.loads(str(block[3]).replace("'", '"')))
		return askedBlock



###########################  Initial data entry function  ###########################

def dataInput(Ν):
	print('\n\nInitial data entry')
	print('------------------')
	
	global root
	for i in range(N):
		blockLabel = input('Label of {} No. {}: '.format(blockAlias, i))
		blockData = input('Data of {} No. {}: '.format(blockAlias, i))
		print()
		pos = random.randint(0, 2**L - 1)
		blkNode = odnode.Odnode(blockLabel, blockData, pos, {})		# Create instance of Odnode class and assign the values of the current block (node)
		blocks.append(blkNode)										# Construct a list holding the data blocks (nodes) 								

	# Store children's positions in a dictionary for each node
	for i, j in enumerate(blocks):											
		if blocks.index(j) < len(blocks)-1:									
			cName = blocks[blocks.index(j)+1].label					# Assign to cName current block's child label
			cPos = blocks[blocks.index(j)+1].pos					# Assign to cPos current block's child position
			j.chPos = {cName : cPos}								# Add to current block the pair {Child_id : position}
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
		# Get root node from ORAM on first access
		ask = odnode.Odnode(root.label, root.data, root.pos, root.chPos)
		oramAccess('readandremove', ask)
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

	newNode = odnode.Odnode(newNodeLabel, newNodeData, 0, {})		# Create Odnode instance for the new block (node)
	
	if cache != []:
		# Traverse the structure until the last entry
		eos = False
		while eos == False:
			lastInCache = cache[-1]
			if lastInCache.chPos == {}:
				eos = True
			else:
				read(list(lastInCache.chPos.keys())[0])
	else:
		root = newNode

	cache.append(newNode)											# Insert new block in cache



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

def finalize():
	global cache
	global root

	if cache != []:
		# Assign new random position to each node in cache
		for n in cache:
			pos = random.randint(0, 2**L - 1)
			n.pos = pos
																		
		# Update children's positions in each node
		for i, j in enumerate(cache):											
			if cache.index(j) < len(cache)-1:									
				cName = cache[cache.index(j)+1].label					# Assign to cName current block's child label
				cPos = cache[cache.index(j)+1].pos						# Assign to cPos current block's child position
				j.chPos = {cName : cPos}								# Add to current block the pair {Child_id : position}
				if i == 0:												# Store the root of the ..
					root = j											# .. data structure in variable 'root'

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
	print('CREATE AN ODS (Oblivious Data Structure)')
	print('----------------------------------------')
	print('\n[1] --> Oblivious Stack')
	print('\n[2] --> Oblivious Queue')
	print('\n[3] --> Oblivious Heap')
	print('\n[4] --> Oblivious AVL Tree')
	print('\n[5] --> Path ORAM explorer')
	print('\n[ENTER] --> EXIT\n\n')

	oblStruct = input('Please enter your selection : ')
	
	if (oblStruct != '5') and (oblStruct != ''):
		N = int(input('\nInitial number of items/nodes = '))		# Get the number of items the stack will contain
		L = math.ceil(math.log(N, 2))								# Calculate path-oram's tree height L 
		oram = bt.binTree(L, Z, passHash)							# Construct an instance of the binTree class with the given parametres

	if oblStruct == '1':
		cache.clear()
		os.system('clear')
		blockAlias = 'item'
		print('OBLIVIOUS STACK')
		print('---------------')
		dataInput(N)
		
		while True:
			# present stack menu
			os.system('clear')
			
			print('Oblivious Stack Options')
			print('-----------------------')
			print('\n[1] --> Push(item)')
			print('\n[2] --> Pop()')
			print('\n[ENTER] --> EXIT\n\n')

			select = input('Please enter your selection : ')

			if select == '':
				break

			odsStart()
			if select == '1':
				newBlockName = input('\nEnter the ID of the item you want to push : ')
				newBlockData = input("Enter the data of the item '{0}' : ".format(newBlockName))

				def push(node, data):
					insert(node, data)
					finalize()
				
				push(newBlockName, newBlockData)

				print('\nOperation finished successfully!')
				input('\nPlease press [ENTER] to continue...')
		
			if select == '2':

				def pop():
					global cache
					global root

					if root != None:
						# Traverse the structure until the last entry
						eos = False
						while eos == False:
							top = cache[-1]
							if top.chPos == {}:
								eos = True
							else:
								top = read(list(top.chPos.keys())[0])	
						
						delete(top.label)
						finalize()
					else:
						top = None
					
					return top
				
				topItem = pop()
				if topItem != None:
					print('\nItem ID :', topItem.label)
					print('Item Data :', topItem.data)
				else:
					print('\nThe Oblivious Stack is empty!')
				
				input('\nPlease press [ENTER] to continue...')



	elif oblStruct == '2':
		cache.clear()
		os.system('clear')
		blockAlias = 'item'
		print('OBLIVIOUS QUEUE')
		print('---------------')
		dataInput(N)
		
		while True:
			# present queue menu
			os.system('clear')
			
			print('Oblivious Queue Options')
			print('-----------------------')
			print('\n[1] --> Enqueue(item)')
			print('\n[2] --> Dequeue()')
			print('\n[ENTER] --> EXIT\n\n')

			select = input('Please enter your selection : ')

			if select == '':
				break

			odsStart()
			if select == '1':
				newBlockName = input('\nEnter the ID of the item you want to enqueue : ')
				newBlockData = input("Enter the data of the item '{0}' : ".format(newBlockName))

				def enqueue(node, data):
					insert(node, data)
					finalize()
				
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
						finalize()
					return tail
				
				tailItem = dequeue()
				if tailItem != ():
					print('\nItem ID :', tailItem[0])
					print('Item Data :', tailItem[1])
				else:
					print('\nThe Oblivious Queue is empty!')
				
				input('\nPlease press [ENTER] to continue...')



	elif oblStruct == '3':
		cache.clear()
		os.system('clear')
		blockAlias = 'node'
		print('OBLIVIOUS HEAP')
		print('--------------')
		dataInput(N)
		# present heap menu
		break
	elif oblStruct == '4':
		cache.clear()
		os.system('clear')
		blockAlias = 'node'
		print('OBLIVIOUS AVL TREE')
		print('------------------')
		dataInput(N)
		# present AVL menu
		break

	elif oblStruct == '5':
		while True:
			os.system('clear')
			print('Path ORAM explorer')
			print('------------------')
			print('\n[1] --> Display the ORAM binary tree (Decrypted)')
			print('\n[2] --> Display the ORAM binary tree (Encrypted)')
			print('\n[ENTER] --> EXIT\n\n')

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