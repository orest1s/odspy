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
S = []											# Initialize local stash as a list
position = {}									# Initialize position map as a dictionary
blocks = []										# Initialize the list holding the data blocks (nodes)
cache = []										# Initialize local (client) cache

BS = 16																#
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)		# pad and unpad methods used to match AES block size
unpad = lambda s: s[:-ord(s[len(s)-1:])]							##


def oramAccess(op, block_node):
	
	if op != 'readandremove' and op != 'add': raise ValueError
	
	def writeBucket(bucketID, block_list):
		while len(block_list) < Z:																					# Pad the bucket with dummy blocks until its size is Z
			block_list.append(('---Dummy-Label--', '---Dummy-Data---', '9999999999999999', '---Dummy-CPos---'))	  	##
		
		# Encrypt the bucket blocks to be written in the ORAM
		enBucket = [(cr.E(bytes(pad(bl[0]).encode('utf-8')), passHash),
		cr.E(bytes(pad(bl[1]).encode('utf-8')), passHash),
		cr.E(bytes(pad(str(bl[2])).encode('utf-8')), passHash),
		cr.E(bytes(pad(str(bl[3])).encode('utf-8')), passHash)) for bl in block_list]
		# Write the encrypted bucket in the ORAM
		oram.nod[bucketID].value = enBucket									

	jnode = json.dumps(block_node.__dict__)			# Serialize object block_node to JSON
	dnode = json.loads(jnode)						# Turn JSON into python dictionary
	
	global S
	oramPath = []
	x = dnode['pos']

	oramPath = oram.P(oram.nod[L, x])				# Get the path of leaf x and store it locally in a list of buckets
	
	# Add to the local stash S the decrypted blocks of the oramPath list
	for l in range(L+1):
		for b in range(4):
			blockContent = (unpad(cr.D(oramPath[l][b][0], passHash).decode('utf-8')),
			unpad(cr.D(oramPath[l][b][1], passHash).decode('utf-8')),
			int(unpad(cr.D(oramPath[l][b][2], passHash).decode('utf-8'))),
			unpad(cr.D(oramPath[l][b][3], passHash).decode('utf-8')))
			if blockContent[0] != '---Dummy-Label--':
				S.append(blockContent)

	block = next((a for a in S if a[0] == dnode['label']), ('Not Found', 'Null', 0, {}))	# Read the block in question from the local stash

	if op == 'add':																	# If the operation is 'add':
		if block in S:
			S.remove(block)															# Remove the old block from the stash if it's there
		S.append((dnode['label'], dnode['data'], dnode['pos'], dnode['chPos']))		# Add the new block, data and its children positions or the old block with new data

	if block in S:
		S.remove(block)
	S_temp = []
	for l in range(L, -1, -1):
		S_temp = [b for b in S if oram.Pl(oram.nod[L, x], l) == oram.Pl(oram.nod[L, b[2]], l)]	# S_temp = {b in S : P(x, l) = P(position[b], l)}
		S_temp = S_temp[:min(len(S_temp), Z)]
		S = [item for item in S if item not in S_temp]
		writeBucket(oram.Pl(oram.nod[L, x], l), S_temp)

	if op == 'readandremove':
		askedBlock = odnode.Odnode(block[0], block[1], block[2], json.loads(str(block[3]).replace("'", '"')))
		return askedBlock



#########################  Initial data entry function  #########################
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




###############################  Main program loop  ###############################
while True:

	os.system('clear')											# Clear screen

	print('CREATE AN ODS (Oblivious Data Structure)')
	print('----------------------------------------')
	print('\n[1] --> Oblivious Stack')
	print('\n[2] --> Oblivious Queue')
	print('\n[3] --> Oblivious Heap')
	print('\n[4] --> Oblivious AVL Tree')
	print('\n[ENTER] --> EXIT\n\n')

	oblStruct = input('Please enter your selection : ')
	N = int(input('\nInitial number of items/nodes = '))		# Get the number of items the stack will contain
	L = math.ceil(math.log(N, 2))								# Calculate path-oram's tree height L 
	oram = bt.binTree(L, Z, passHash)							# Construct an instance of the binTree class with the given parametres

	if oblStruct == '1':
		os.system('clear')
		blockAlias = 'item'
		print('OBLIVIOUS STACK')
		print('---------------')
		dataInput(N)
		# present stack menu
		break
	elif oblStruct == '2':
		os.system('clear')
		blockAlias = 'item'
		print('OBLIVIOUS QUEUE')
		print('---------------')
		dataInput(N)
		# present queque menu
		break
	elif oblStruct == '3':
		os.system('clear')
		blockAlias = 'node'
		print('OBLIVIOUS HEAP')
		print('--------------')
		dataInput(N)
		# present heap menu
		break
	elif oblStruct == '4':
		os.system('clear')
		blockAlias = 'node'
		print('OBLIVIOUS AVL TREE')
		print('------------------')
		dataInput(N)
		# present AVL menu
		break
	elif oblStruct == '':
		break





def odsStart():								# Update cache to contain the root
	global cache
	global root
	cache.clear()
	# Remove root node from ORAM on first access
	ask = odnode.Odnode(root.label, root.data, root.pos, root.chPos)
	oramAccess('readandremove', ask)
	cache.append(root)

odsStart()

while True:
	os.system('clear')						# Clear screen in order to present the options menu

	print('O D S  framework  O P T I O N S')
	print('-------------------------------')
	print('[1] --> Read a data block')
	print('[2] --> Insert a new data block')
	print('[3] --> Update(Write) a data block')
	print('[4] --> Delete a data block')
	print('[5] --> Finalize')
	print('[6] --> Display the client cache')
	print('[7] --> Display the ORAM binary tree (Decrypted)')
	print('[8] --> Display the ORAM binary tree (Encrypted)')
	print('[ENTER] --> EXIT\n\n')

	com = input('Please enter your choice : ')

	
	def read(nodeLabel):
		global cache
		'''
		# Remove root node from ORAM in first access
		if len(cache) == 1:
			ask = odnode.Odnode(root.label, root.data, root.pos, root.chPos)
			fetch = oramAccess('readandremove', ask)
			'''
		
		isInCache = any(x.label == nodeLabel for x in cache)						# True if the block in question is already in cache
		if isInCache == False:
			n = 0
			while isInCache == False:												#
				childDictKeys = list(cache[n].chPos.keys())							#
				currentName = childDictKeys[0]										# 
				currentPosition = cache[n].chPos[currentName]						# Traverse through the nodes .. 
				if not any(x.label == currentName for x in cache):					# .. using their children positions ..
					ask = odnode.Odnode(currentName, 'null', currentPosition, {})	# .. until the requested one is found.
					fetch = oramAccess('readandremove', ask)						# 
					cache.append(fetch)												#
				isInCache = any(x.label == nodeLabel for x in cache)				#
				n += 1																#
	

	if com == '':
		break
	


	###################  Read  ###################
	elif com == '1':
		blockName = input('\nEnter label of the block you want to read: ')
		
		read(blockName)
		print('\nOperation finished successfully!')
		input('\nPlease press [ENTER] to continue...')

	
	
	####################  Insert  ####################
	elif com == '2':
		newBlockName = input('\nEnter the label of the block you want to insert : ')
		newBlockData = input("Enter the data of the block '{0}' : ".format(newBlockName))

		def insert(newNodeLabel, newNodeData):
			global cache
			newNode = odnode.Odnode(newNodeLabel, newNodeData, 0, {})		# Create instance of Odnode for the new block (node)
			eos = False
			while eos == False:
				lastInCache = cache[-1]
				if lastInCache.chPos == {}:
					eos = True
				else:
					read(list(lastInCache.chPos.keys())[0])
			cache.append(newNode)											# Insert new block in cache

		insert(newBlockName, newBlockData)
		print('\nOperation finished successfully!')
		input('\nPlease press [ENTER] to continue...')



	################   Update(Write)   ################
	elif com == '3':
		blockName = input('\nEnter label of the block you want to update: ')
		newBlockData = input("Enter the data of the block '{0}' : ".format(blockName))
		
		def write(nodeLabel, newData):
			global cache
			isInCache = any(x.label == nodeLabel for x in cache)				# True if the block in question is already in cache
			if isInCache == False:
				read(nodeLabel)
			next((n for n in cache if n.label == nodeLabel)).data = newData

		write(blockName, newBlockData)
		print('\nOperation finished successfully!')
		input('\nPlease press [ENTER] to continue...')



	#################   Delete   #################
	elif com == '4':
		blockName = input('\nEnter label of the block you want to delete: ')

		def delete(nodeLabel):
			global cache
			isInCache = any(x.label == nodeLabel for x in cache)				# True if the block in question is already in cache
			if isInCache == False:
				read(nodeLabel)
			cache.remove(next((n for n in cache if n.label == nodeLabel)))

		delete(blockName)
		print('\nOperation finished successfully!')
		input('\nPlease press [ENTER] to continue...')



	################   Finalize   ################
	elif com == '5':

		def finalize():
			global cache
			global root

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

			# Write cahe back to ORAM and empty it
			for k in cache:
				oramAccess('add', k)
			
			# Empty client cache
			cache.clear()

		finalize()
		#odsStart()
		print('\nOperation finished successfully!')
		input('\nPlease press [ENTER] to continue...')



	###################  Display the ORAM (Decrypted)  ###################
	elif com == '6':
		print()
		print([a.label for a in cache])
		input('\nPlease press [ENTER] to continue...')
	
	

	###################  Display the ORAM (Decrypted)  ###################
	elif com == '7':
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
	elif com == '8':
		print()
		for k in sorted(oram.nod.keys()):
			print('\nBucket id =', k)
			blst = [(oram.nod[k].value[i][0].hex(), oram.nod[k].value[i][1].hex()) for i in range(Z)]
			print(blst)
		input('\nPlease press [ENTER] to continue...')