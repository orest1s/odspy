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
	
	if op != 'read' and op != 'add': raise ValueError
	
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
	#pos = random.randint(0, 2**L - 1)
	#dnode['pos'] = pos 								# Assign new random integer between 0 and (2^L - 1) to the current block

	'''
	# Update child's position in parent node
	for block in blocks:
		for k in block.chPos:
			if dnode['label'] in k:
				block.chPos[k] = pos
	'''
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

	block = next((a for a in S if a[0] == dnode['label']), (dnode['label'], 'Not Found'))			# Read the block in question from the local stash

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

	if op == 'read':
		askedBlock = odnode.Odnode(block[0], block[1], block[2], json.loads(str(block[3]).replace("'", '"')))
		return askedBlock

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



while True:														# Main program loop

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




while True:
	os.system('clear')						# Clear screen in order to present the options menu

	print('P - O R A M    O P T I O N S')
	print('-----------------------------')
	print('[1] --> Read and Remove a data block')
	print('[2] --> Add a new data block')
	print('[3] --> Update a data block')
	print('[4] --> Display the ORAM binary tree (Decrypted)')
	print('[5] --> Fetch all ORAM raw contents (Encrypted)')
	print('[ENTER] --> EXIT\n\n')

	com = input('Please enter your choice : ')

	if com == '':
		break
	
	############### Read And Remove ###############
	elif com == '1':
		print()
		nameBlk = input('Enter label of the block to remove: ')
		
		# Root node removal from ORAM to cache
		cache = []
		ask = odnode.Odnode(root.label, root.data, root.pos, root.chPos)
		fetch = oramAccess('read', ask)
		cache.append(fetch)
		
		isInCache = any(x.label == nameBlk for x in cache)				# True if the block in question is already in cache
		
		if isInCache == False:
			n = 0
			while isInCache == False:
				childDictKeys = list(cache[n].chPos.keys())
				currentName = childDictKeys[0]
				currentPosition = cache[n].chPos[currentName]
				ask = odnode.Odnode(currentName, 'null', currentPosition, {})
				fetch = oramAccess('read', ask)
				cache.append(fetch)
				isInCache = any(x.label == nameBlk for x in cache)
				n += 1
		print([a.label for a in cache])
		print('\nOperation finished successfully!')
		input('\nPlease press [ENTER] to continue...')

	elif com == '2':
		print()
		print()
		nameBlk = input('Enter the name of the block you want to add : ')
		newData = input("Enter the data of the block '{0}' : ".format(nameBlk))
		pos = random.randint(0, 2**L - 1)
		position[nameBlk] = pos 							# Assign random integer between 0 and (2^L - 1) to new block
		oramAccess('add', nameBlk, newData, {})
		print('\nOperation finished successfully!')
		input('\nPlease press [ENTER] to continue...')
	
	elif com == '3':
		print()
		print('Available block names :')
		print(sorted([blk[0] for blk in blocks]))
		print()
		nameBlk = input('Enter the name of the block you want to update : ')
		newData = input("Enter the new contents of block '{0}' : ".format(nameBlk))
		oramAccess('add', nameBlk, newData)
		print('\nOperation finished successfully!')
		input('\nPlease press [ENTER] to continue...')


	elif com == '4':
		print()
		for k in sorted(oram.nod.keys()):
			print('\nBucket id =', k)
			blst = [(unpad(cr.D(oram.nod[k].value[i][0], passHash).decode('utf-8')),
			unpad(cr.D(oram.nod[k].value[i][1], passHash).decode('utf-8')),
			int(unpad(cr.D(oram.nod[k].value[i][2], passHash).decode('utf-8'))),
			unpad(cr.D(oram.nod[k].value[i][3], passHash).decode('utf-8'))) for i in range(Z)]
			print(blst)
		input('\nPlease press [ENTER] to continue...')

	elif com == '5':
		print()
		for k in sorted(oram.nod.keys()):
			print('\nBucket id =', k)
			blst = [(oram.nod[k].value[i][0].hex(), oram.nod[k].value[i][1].hex()) for i in range(Z)]
			print(blst)
		input('\nPlease press [ENTER] to continue...')