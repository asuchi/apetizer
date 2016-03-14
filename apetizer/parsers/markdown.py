# markdown to items and items to markdonw


def markdown_to_item(node, md, recurse=False):
	
	# check for md node if they exists
	lines = md.split('\n')
	
	# remove possible empty first lines
	while lines:
		if len(lines) and not lines[0]:
			lines.pop(0)
		else:
			break
	
	# parse header
	ol = 0
	if len(lines) > 0 \
		and len(lines[0]) \
		and lines[0][0:2] == '> ':
		node.label = lines[0][2:]
		ol = 1
		if len(lines) > 1 \
			and len(lines[1]) \
			and lines[1][0:2] == '# ':
			node.title = lines[1][2:]
			ol = 2
	if not node.label: node.label = node.id
	if not node.title: node.title = node.label
	
	# 
	node.description = '\n'.join(lines[ol+1:])
	
	return node

def item_to_markdown(node, recurse=False):
		
	md = u''
	md += '> '+node.label+'\n'
	md += '# '+node.title+'\n\n'
	md += ''+node.description+'\n'
	
	return md