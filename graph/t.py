from pygraph.classes.graph import graph
from pygraph.algorithms.searching import depth_first_search
from pygraph.algorithms.searching import breadth_first_search
from pygraph.algorithms.accessibility import accessibility, mutual_accessibility
from pygraph.algorithms.critical import transitive_edges, traversal
from pygraph.algorithms.minmax import maximum_flow, shortest_path_bellman_ford, shortest_path



gr = graph()
# Add nodes
gr.add_nodes(['A','B','C'])
gr.add_nodes(['D','E','F'])
gr.add_nodes(['G','H','I'])
# Add edges
gr.add_edge(('A','B'),wt=1,label='core1')
gr.add_edge(('B','C'),wt=1,label='prepreg')
gr.add_edge(('C','D'),wt=2,label='core2')
gr.add_edge(('C','E'),wt=3,label='air')
gr.add_edge(('C','F'),wt=1,label='core3')
gr.add_edge(('G','H'),wt=1,label='core4')
gr.add_edge(('G','I'),wt=1,label='core5')

print "The input graph"
print gr
print "\n"

# Depth first search rooted on node A
st, pre, post = depth_first_search(gr, root='A')
# Print the spanning tree
print "Depth first search"
print "Spanning tree"
print st
print "Preordering"
print pre
print "Postordering"
print post
print "\n"

bfs, bfsord= breadth_first_search(gr, root='A')
print "Breadth first search"
print "Spanning tree"
print bfs
print "level-based ordering"
print bfsord
print "\n"

print "Accessibility"
access= accessibility(gr)
print access
print "Mutual accessibility"
maccess= mutual_accessibility(gr)
print maccess
print "\n"

print "Traversal"
trav= traversal(gr, 'A', 'pre')
for t in trav:
  print t
print "Transitive Edges"
tredges= transitive_edges(gr)
print tredges
print "\n"

print "shortest_path_bellman_ford"
short= shortest_path_bellman_ford(gr, 'A')
print short

print "shortest_path"
shrt= shortest_path(gr, 'A')
print shrt