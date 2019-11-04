import os
import sys
import math
import random
import bintree as bt
import crypt as cr


password = 'myP@th0rAM'							# Define the local password
passHash = cr.H(password)						# Hash the local password in order to use it as a key for AES
Z = 4											# Define the number of blocks in a bucket
S = []											# Initialize local stash as a list
position = {}									# Initialize position map as a dictionary
blocks = []										# Initialize the list holding the data blocks
cache = []										# Initialize local (client) cache

BS = 16																#
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)		# pad and unpad methods used to match AES block size
unpad = lambda s : s[:-ord(s[len(s)-1:])]							##


def oramAccess(op, block_name, dataN = None):
	
	def writeBucket(bucketID, block_list):
		while len(block_list) < Z:											# Pad the bucket with dummy blocks until its size is Z
			block_list.append(('------NULL------', '---Dummy-Data---'))		##
		
		# Encrypt the bucket blocks to be written in the ORAM
		enBucket = [(cr.E(bytes(pad(bl[0]).encode('utf-8')), passHash), cr.E(bytes(pad(bl[1]).encode('utf-8')), passHash)) for bl in block_list]
		# Write the encrypted bucket in the ORAM
		oram.nod[bucketID].value = enBucket									

	global S
	oramPath = []
	x = position[block_name]
	pos = random.randint(0, 2**L - 1)
	position[block_name] = pos 					# Assign new random integer between 0 and (2^L - 1) to the current block

	oramPath = oram.P(oram.nod[L, x])			# Get the path of leaf x and store it locally in a list of buckets
	
	# Add to the local stash S the decrypted blocks of the oramPath list
	for l in range(L+1):
		for b in range(4):
			blockContent = (unpad(cr.D(oramPath[l][b][0], passHash).decode('utf-8')), unpad(cr.D(oramPath[l][b][1], passHash).decode('utf-8')))
			if blockContent[0] != '------NULL------':
				S.append(blockContent)

	block = next((a for a in S if a[0] == block_name), (block_name, 'Not Found'))			# Read the block in question from the local stash

	if op == 'write':							# If the operation is 'write':
		if block in S:
			S.remove(block)						# Remove the old block from the stash
		S.append((block_name, dataN))			# Add it back with the new data

	
	S_temp = []
	for l in range(L, -1, -1):
		S_temp = [b for b in S if oram.Pl(oram.nod[L, x], l) == oram.Pl(oram.nod[L, position[b[0]]], l)]	# S_temp = {b in S : P(x, l) = P(position[b], l)}
		S_temp = S_temp[:min(len(S_temp), Z)]
		S = [item for item in S if item not in S_temp]
		writeBucket(oram.Pl(oram.nod[L, x], l), S_temp)

	return block[1]

def dataIn(Ν):
	print('\n\nInitial data entry')
	print('------------------')
	for i in range(N):
		blockLabel = input('Label of {} No. {}: '.format(blockAlias, i))
		blockData = input('Data of {} No. {}: '.format(blockAlias, i))
		print()
		blocks.append((blockLabel, blockData))		# Construct a list holding the data blocks
		pos = random.randint(0, 2**L - 1)
		position[blockLabel] = pos 					# Assign random integer between 0 and (2^L - 1) to the current block
	
	# Write given data blocks in ORAM	
	for j in blocks:
		oramAccess('write', j[0], j[1])




while True:														# Main program loop

	os.system('clear')											# Clear screen
	print('CREATE AN ODS (Oblivious Data Structure)')
	print('----------------------------------------')
	print('\n[1] --> Oblivious Stack')
	print('\n[2] --> Oblivious Queue')
	print('\n[3] --> Oblivious Heap')
	print('\n[4] --> Oblivious AVL Tree')
	print('\n[ENTER] --> EXIT\n\n')

	obstruct = input('Please enter your selection : ')
	N = int(input('\nInitial number of items/nodes = '))		# Get the number of items the stack will contain
	L = math.ceil(math.log(N, 2))								# Calculate path-oram's tree height L 
	oram = bt.binTree(L, Z, passHash)							# Construct an instance of the binTree class with the given parametres

	if obstruct == '1':
		os.system('clear')
		blockAlias = 'item'
		print('OBLIVIOUS STACK')
		print('---------------')
		dataIn(N)
		# present stack menu
		break
	elif obstruct == '2':
		os.system('clear')
		blockAlias = 'item'
		print('OBLIVIOUS QUEUE')
		print('---------------')
		dataIn(N)
		# present queque menu
		break
	elif obstruct == '3':
		os.system('clear')
		blockAlias = 'node'
		print('OBLIVIOUS HEAP')
		print('--------------')
		dataIn(N)
		# present heap menu
		break
	elif obstruct == '4':
		os.system('clear')
		blockAlias = 'node'
		print('OBLIVIOUS AVL TREE')
		print('------------------')
		dataIn(N)
		# present AVL menu
		break
	elif obstruct == '':
		break





while True:
	os.system('clear')						# Clear screen in order to present the options menu
	print('P - O R A M    O P T I O N S')
	print('-----------------------------')
	print('[1] --> Read a data block')
	print('[2] --> Update a data block')
	print('[3] --> Display the ORAM binary tree (Decrypted)')
	print('[4] --> Fetch all ORAM raw contents (Encrypted)')
	print('[ENTER] --> EXIT\n\n')

	com = input('Please enter your choice : ')

	if com == '':
		break
	elif com == '1':
		print()
		print('Available block names :')
		print(sorted([blk[0] for blk in blocks]))
		print()
		nameBlk = input('Enter the name of the block you want to access : ')
		asked = oramAccess('read', nameBlk)
		print("\nContents of block '{0}' :".format(nameBlk))
		print(asked)
		input('\nPlease press [ENTER] to continue...')

	elif com == '2':
		print()
		print('Available block names :')
		print(sorted([blk[0] for blk in blocks]))
		print()
		nameBlk = input('Enter the name of the block you want to update : ')
		newData = input("Enter the new contents of block '{0}' : ".format(nameBlk))
		oramAccess('write', nameBlk, newData)
		print('\nOperation finished successfully!')
		input('\nPlease press [ENTER] to continue...')

	elif com == '3':
		print()
		for k in sorted(oram.nod.keys()):
			print('\nBucket id =', k)
			blst = [(unpad(cr.D(oram.nod[k].value[i][0], passHash).decode('utf-8')), unpad(cr.D(oram.nod[k].value[i][1], passHash).decode('utf-8'))) for i in range(Z)]
			print(blst)
		input('\nPlease press [ENTER] to continue...')

	elif com == '4':
		print()
		for k in sorted(oram.nod.keys()):
			print('\nBucket id =', k)
			blst = [(oram.nod[k].value[i][0].hex(), oram.nod[k].value[i][1].hex()) for i in range(Z)]
			print(blst)
		input('\nPlease press [ENTER] to continue...')