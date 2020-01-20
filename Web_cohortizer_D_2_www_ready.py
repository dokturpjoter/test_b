# -*- coding: utf-8 -*-
"""
Created on Wed Dec 16 11:26:06 2015

@author: Lipek
"""
###############################################################################
#import os, sys
import os
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import random
import pandas as pd
from collections import Counter    
import time

###############################################################################

full_path = os.path.realpath(__file__)
models_path   = os.path.join(os.path.dirname(full_path) + '/../../models/')
data_path     = os.path.join(os.path.dirname(full_path) + '/../../data/')
mappings_path = os.path.join(os.path.dirname(full_path) + '/../../mappings/')
this_path = os.path.join(os.path.dirname(full_path) + '/')

#from DotDict import DotDict 

############################################################################### 
############################################################################### 
###############################################################################
# get all neighbors of a given orderof ecah node
def all_neighbors_order(g, order):
    g = g.copy()
    
    neighbors_dict = {}
    
    for node in g.nodes():
        neighbors = list(g.neighbors(node))
        
        if(len(neighbors) > 0):
            for o in range(0,order - 1):                               
                neighbors_2 = []
                
                for nei in neighbors:
                    neighbors_2 = neighbors_2 + list(g.neighbors(nei))
                    
                neighbors = neighbors + list(set(neighbors_2))
                neighbors.remove(node)
                neighbors = list(set(neighbors))
            
        neighbors_dict[node] = neighbors
    
    return neighbors_dict
    
###############################################################################
# get all neighbors of a given orderof ecah node
def all_neighbors_multiorder(g, order):
    g = g.copy()
    
    neighbors_dict = {}
    ego_dict = {}
    
    for o in range(1,order+1):
        neighbors_dict[o] = {}
        ego_dict[o] = {}
    
    for node in g.nodes():
        ego = {}
        neigh = {}
        
        #################
        neighbors = list(g.neighbors(node))
        
        #print node
        #print neighbors
        
        ego[0] = set([node])
        ego[1] = set(neighbors)
        
        if(len(neighbors) > 0):
            for distance in range(2,order+1):                               
                neighbors_2 = []
                
                for neighbor in neighbors:
                    neighbors_2 = neighbors_2 + list(g.neighbors(neighbor))
                    
                neighbors = neighbors + list(set(neighbors_2))
                neighbors.remove(node)
                neighbors = list(set(neighbors))
                
                ego[distance] = set(neighbors)
        else:
            for distance in range(2,order+1):                               
                ego[distance] = set([])
      
        #####################

        for distance in range(1,order+1):            
            neigh[distance] = ego[distance].difference(ego[distance-1])
            neighbors_dict[distance][node] = list(neigh[distance]) 
            ego_dict[distance][node]       = list(ego[distance].difference([node])) 
            
    result = {}
    result['neighbors'] = neighbors_dict
    result['ego']       = ego_dict
  
    return result

############################################################################### 
############################################################################### 
############################################################################### 
# Color Normal  
# uses ordinary random walk to color the nodes
def color_nodes_normal(g, n, p, q, limit, neighbors_dict):
    g = g.copy()
    all_nodes = g.nodes()
    colors = {}
    colored = []
    clusters = {}
    seeds = {}

    for value in all_nodes:
        colors[value]   = 'g'
        clusters[value] = 0
        seeds[value] = 0 

    step  = 0 
    cluster_id = 1 
    
    random_node = random.choice(all_nodes)
    seeds[random_node] = cluster_id

    while(colors.values().count('r') < n):   
        if colors[random_node] == 'g':
            colors[random_node] = 'r'
            colored.append(random_node)
            clusters[random_node] = cluster_id
            last_colored = True
            step = 0  
        else:
            last_colored = False
            step = step + 1
                       
        if random.random() <= p or last_colored == False:
            try:
                random_node = random.choice(neighbors_dict[random_node]) 
            except:
                pass          
        else:
            potential_nodes = list(set(all_nodes).difference(set(colored)))
            random_node = random.choice(potential_nodes)            
            cluster_id += 1
            seeds[random_node] = cluster_id
                  
        if step > limit:
            potential_nodes = list(set(all_nodes).difference(set(colored)))
            random_node = random.choice(potential_nodes)            
            cluster_id += 1
            seeds[random_node] = cluster_id
                 
    remaining_colors     = {}
    remaining_colors_clr = {}
    
    for node, color in colors.items():
        if color == 'g':
            remaining_colors[node]     = 'g'
            remaining_colors_clr[node] = 'g'
        elif color == 'r':
            if random.random() <= q: 
                remaining_colors[node]     = 'r'
                remaining_colors_clr[node] = 'r'
            else:
                remaining_colors[node]     = 'y'
                remaining_colors_clr[node] = 'g'

    nx.set_node_attributes(g, 'color_old', colors)
    nx.set_node_attributes(g, 'color_clr', remaining_colors_clr)
    nx.set_node_attributes(g, 'color', remaining_colors)
    nx.set_node_attributes(g, 'cluster', clusters)
    nx.set_node_attributes(g, 'seed', seeds)

    return g, cluster_id
    
############################################################################### 
# Color Hybrid 
# uses modified random walk to color the nodes, 
# so it avoids colored nodes among neighbors of the current node
# if there are no uncolored neighbors it colors random neighbor of the cluster 
# clusters have elongated structures
def color_nodes_hybrid(g, n, p, q, limit, neighbors_dict):
    g = g.copy()
    all_nodes = g.nodes()
    colors = {}
    colored = []
    clusters = {} 
    seeds = {}

    for value in all_nodes:
        colors[value]   = 'g'
        seeds[value] = 0 
        clusters[value] = 0

    random_node = random.choice(all_nodes)
    
    step  = 0 
    cluster_id = 1 
    cluster_nodes = []
    cluster_neighbors = []
    
    while(colors.values().count('r') < n):       
        if colors[random_node] == 'g':
            colors[random_node] = 'r'
            colored.append(random_node)
            clusters[random_node] = cluster_id
            cluster_nodes.append(random_node)
            cluster_neighbors += neighbors_dict[random_node]
            cluster_neighbors = list(set(cluster_neighbors))
            last_colored = True
            step = 0
        else:
            last_colored = False
            step = step + 1
            
        if random.random() <= p or last_colored == False:         
            try:   
                #random_node = random.choice(neighbors_dict[random_node]) 
                potential_nodes = list(set(neighbors_dict[random_node]).difference(set(colored)))                
                #potential_nodes = list(set(cluster_neighbors).difference(set(colored)))
                
                if len(potential_nodes) > 0:
                    random_node = random.choice(potential_nodes)                         
                else:
                    potential_nodes = list(set(cluster_neighbors).difference(set(colored)))
                
                    if len(potential_nodes) > 0:
                        random_node = random.choice(potential_nodes)  
                    else:
                        potential_nodes = list(set(all_nodes).difference(set(colored)))
                        random_node = random.choice(potential_nodes)
                        cluster_id += 1
                        cluster_nodes = []
                        cluster_neighbors = []  
                        seeds[random_node] = cluster_id
            except:
                pass            
        else:
            potential_nodes = list(set(all_nodes).difference(set(colored)))
            random_node = random.choice(potential_nodes)            
            cluster_id += 1
            cluster_nodes = []
            cluster_neighbors = []
                  
        if step > limit:
            potential_nodes = list(set(all_nodes).difference(set(colored)))
            random_node = random.choice(potential_nodes)            
            cluster_id += 1
            cluster_nodes = []
            cluster_neighbors = []
             
    remaining_colors     = {}
    remaining_colors_clr = {}
    
    for node, color in colors.items():
        if color == 'g':
            remaining_colors[node]     = 'g'
            remaining_colors_clr[node] = 'g'
        elif color == 'r':
            if random.random() <= q: 
                remaining_colors[node]     = 'r'
                remaining_colors_clr[node] = 'r'
            else:
                remaining_colors[node]     = 'y'
                remaining_colors_clr[node] = 'g'
                
    nx.set_node_attributes(g, 'color_old', colors)
    nx.set_node_attributes(g, 'color_clr', remaining_colors_clr)
    nx.set_node_attributes(g, 'color', remaining_colors)
    nx.set_node_attributes(g, 'cluster', clusters)
    nx.set_node_attributes(g, 'seed', seeds)
    
    return g, cluster_id
  
############################################################################### 
# Color Compact
# uses compact random walk to color the nodes, 
# it colors random neighbor of the cluster 
def color_nodes_compact(g, n, p, q, limit, neighbors_dict):
    g = g.copy()
    all_nodes = g.nodes()
    colors = {}
    colored = []
    clusters = {}
    seeds = {}

    for value in all_nodes:
        colors[value]   = 'g'
        seeds[value] = 0 
        clusters[value] = 0

    random_node = random.choice(all_nodes)
    jump = True
    
    step  = 0 
    cluster_id = 1 
    cluster_nodes = []
    cluster_neighbors = []
    
    while(colors.values().count('r') < n):
        # coloring of the node if it is uncolored
        if colors[random_node] == 'g':
            if jump == True:
                seeds[random_node] = cluster_id
            
            colors[random_node] = 'r'
            colored.append(random_node)
            clusters[random_node] = cluster_id
            cluster_nodes.append(random_node)
            cluster_neighbors += neighbors_dict[random_node]
            cluster_neighbors = list(set(cluster_neighbors))
            last_colored = True
            step = 0
            jump = False
        else:
            last_colored = False
            step = step + 1
        
        # chose node within cluster to color if there are none uncolored try to jump
        if random.random() <= p or last_colored == False:         
            try:                
                potential_nodes = list(set(cluster_neighbors).difference(set(colored)))
                
                if len(potential_nodes) > 0:
                    random_node = random.choice(potential_nodes)  
                else:
                    potential_nodes = list(set(all_nodes).difference(set(colored)))
                    random_node = random.choice(potential_nodes)
                    cluster_id += 1
                    cluster_nodes = []
                    cluster_neighbors = []  
                    jump = True
            except:
                pass
        
        # try to jump by chosing randomly uncolored cluster    
        else: 
            potential_nodes = list(set(all_nodes).difference(set(colored)))
            random_node = random.choice(potential_nodes)            
            cluster_id += 1
            cluster_nodes = []
            cluster_neighbors = []
            jump = True
        
        # start new cluster if time limit is up          
        if step > limit:
            potential_nodes = list(set(all_nodes).difference(set(colored)))
            random_node = random.choice(potential_nodes)            
            cluster_id += 1
            cluster_nodes = []
            cluster_neighbors = []
            jump = True

    remaining_colors     = {}
    remaining_colors_clr = {}
    
    for node, color in colors.items():
        if color == 'g':
            remaining_colors[node]     = 'g'
            remaining_colors_clr[node] = 'g'
        elif color == 'r':
            if random.random() <= q: 
                remaining_colors[node]     = 'r'
                remaining_colors_clr[node] = 'r'
            else:
                remaining_colors[node]     = 'y'
                remaining_colors_clr[node] = 'g'          
    
    nx.set_node_attributes(g, 'color_old', colors)
    nx.set_node_attributes(g, 'color_clr', remaining_colors_clr)
    nx.set_node_attributes(g, 'color', remaining_colors)
    nx.set_node_attributes(g, 'cluster', clusters)
    nx.set_node_attributes(g, 'seed', seeds)
    
    return g, cluster_id

###############################################################################
###############################################################################
###############################################################################

def neighbors_order(g, node, order):
    g = g.copy()
    
    neighbors = list(g.neighbors(node))
    
    if(len(neighbors) > 0):
        for o in range(0,order - 1):       
                     
            neighbors_2 = []
            
            for nei in neighbors:
                neighbors_2 = neighbors_2 + list(g.neighbors(nei))
                
            neighbors = neighbors + list(set(neighbors_2))
            neighbors.remove(node)
        
    return neighbors
        
###############################################################################
        
def color_nodes_order(g, n, p, order):
    g = g.copy()
    colors = {}

    for value in g.nodes():
        colors[value] = 'g'

    random_node = random.choice(g.nodes())
    
    limit = 1000000
    step  = 0 
    
    while(colors.values().count('r') < n):   
        colors[random_node] = 'r'
           
        if (random.random() <= p):
            try:
                random_node = random.choice(neighbors_order(g, random_node, order)) 
            except:
                a = 1            
        else:
            random_node = random.choice(g.nodes())
            
        step = step + 1
        if step > limit:
            break

    nx.set_node_attributes(g, 'color', colors)
    #print 'colors: ' +  str(colors.values().count('r'))
    return g
 
###############################################################################
###############################################################################
###############################################################################
 
def get_colored_subgraph(g, color = 'r', equality = 'positive'):
    #print equality
    g = g.copy()
    nodes = []
    nodes_neg = []

    for value in g.node:
        if g.node[value]['color'] == color:
            nodes.append(value)
        else:
            nodes_neg.append(value)
            
    if(equality == 'positive'):
        g = g.subgraph(nodes)
    elif(equality == 'negative'):
        g = g.subgraph(nodes_neg)
                    
    return g 

###############################################################################
###############################################################################
###############################################################################

def get_collective_gene_expression(simulation_data, expressed_genes_under = None, expressed_genes_over = None, phenotype_table = None, mode = 'normal'):        
    start = time.time()
    
    fields        = simulation_data['fields']
    filter_range  = simulation_data['filter_range']

    #expressed_genes_row = {}        
    #expressed_genes_row['threshold'] = simulation_data['threshold']
    
    #print "time in 1  = " + str(time.time() - start)

    #######################################################################
    start = time.time()
    
    tables = {}
    
    for field in fields.keys():
        tables[field + '_under'] = []
        tables[field + '_over'] = []
        tables[field + '_both'] = []
 
    if mode == 'random':
        for key, value in simulation_data['healthy_fields'].items():
            a = "phenotype_table[" + value
            a = a.replace("{", "phenotype_table['")
            a = a.replace("}", "']")
            #a = a.replace("&", "and") 
            a += "]"
            
            healthy_table = eval(a)

    for key, value in fields.items():
        a = "phenotype_table[" + value
        a = a.replace("{", "phenotype_table['")
        a = a.replace("}", "']")
        #a = a.replace("&", "and") 
        a += "]"
        
        subtable = eval(a)  

        if mode == 'normal':
            iter_list = list(subtable.index)
        elif mode == 'random':
            if simulation_data['disease_group_limit'] == False:
                iter_list = random.sample(list(healthy_table.index), len(subtable))
            else:
                iter_list = random.sample(list(healthy_table.index), min(len(list(subtable.index)), simulation_data['disease_group_limit']))               
        elif mode == 'limit': 
            iter_list = random.sample(list(subtable.index), min(len(list(subtable.index)), simulation_data['disease_group_limit']))
            
        for i in iter_list:
            tables[key + '_under'] += expressed_genes_under[i]
            tables[key +  '_over'] += expressed_genes_over[i]
            tables[key +  '_both'] += expressed_genes_under[i] + expressed_genes_over[i] 
     
    #print "time in 2  = " + str(time.time() - start)               
    ###########################################################################
    start = time.time()
    
    counters = {}
    genes = {}
        
    for key, value in tables.items(): 
        try:
            gene = value
        except:
            gene = []
        try:
            counter = Counter(gene)
        except:
            counter = []           
        
        counters[key] = counter
        genes[key] = gene

    #print "time in 3  = " + str(time.time() - start)

    filtered = {}
    reverse_filtered = {}
    flt = {}

    start = time.time()
    
    for key, value in counters.items():  
        for filter_threshold in range(0, filter_range + 1):
            tmp_flt     = dict((subkey, subvalue) for (subkey, subvalue) in dict(value).items() if subvalue > filter_threshold ).keys() 
            tmp_rev_flt = dict((subkey, subvalue) for (subkey, subvalue) in dict(value).items() if ((subvalue <= filter_threshold) & (subvalue > 0)) ).keys()
            
            filtered[str(key) + '_filtered_' + str(filter_threshold)] = tmp_flt
            reverse_filtered[str(key) + '_reverse_filtered_' + str(filter_threshold)] = tmp_rev_flt 
            flt[str(key) + '_flt_' + str(filter_threshold)] = tmp_flt
            
            if filter_threshold != 0:
                flt[str(key) + '_flt_-' + str(filter_threshold)] = tmp_rev_flt
    done = time.time()
    elapsed = done - start
    #print "time in 4 old  = " + str(elapsed)
    
    ###########################################################################
    
    collective_genes = {}
    #collective_genes['filtered'] = filtered
    #collective_genes['reverse_filtered'] = reverse_filtered       
    collective_genes['flt'] = flt
    collective_genes['counters'] = counters
    
    return collective_genes

###############################################################################
###############################################################################
###############################################################################    

def simulate_artificial_disease(disease_params, simulation_data, g, colored_graph):  
    G = disease_params['G']
    D = disease_params['D']
    A = disease_params['A']
    rho_0 = disease_params['rho_0']
    
    rho_D_max = np.min([1, rho_0*G/D])
    rho_D = rho_0 + A*(rho_D_max - rho_0)
    rho_G = rho_0 - (rho_D - rho_0)*D/(G - D)
    
    #print 'rho_0 = ' + str(rho_0) 
    #print 'rho_D = ' + str(rho_D) 
    #print 'rho_G = ' + str(rho_G) 
    
    result = {}
    result['colored_subgraph']   = get_colored_subgraph(colored_graph, color = 'r', equality = 'positive')        
    result['uncolored_subgraph'] = get_colored_subgraph(colored_graph, color = 'r', equality = 'negative')   
     
    all_nodes = colored_graph.nodes()
    dis_nodes = result['colored_subgraph'].nodes()
    hlt_nodes = result['uncolored_subgraph'].nodes()     
    
    # for each individual mark if it is sick
    #print "phenotype table"

    result['phenotype_table'] = pd.DataFrame(columns = ['disease']) 
    result['expressed_genes_under'] = []
    result['expressed_genes_over']  = []
            
    #print "disease"

    for i in range(0, disease_params['S']):    
        patient = {}
        patient['disease'] = 1
        result['phenotype_table'] = result['phenotype_table'].append(patient, ignore_index=True)  

        exp_genes = []
        
        for node in dis_nodes:                
            if(float(np.random.uniform(0,1,1)) <= rho_D):
                exp_genes.append(node)
                
        for node in hlt_nodes:                
            if(float(np.random.uniform(0,1,1)) <= rho_G):
                exp_genes.append(node)
        
        result['expressed_genes_under'].append(dis_nodes) #note that underexpressed genes are used as a disease picture
        result['expressed_genes_over'].append(exp_genes)        
    
    #print "healthy"
    for i in range(disease_params['S'], disease_params['patients_number']):    
        patient = {}
        patient['disease'] = 0
        result['phenotype_table'] = result['phenotype_table'].append(patient, ignore_index=True)  
        
        exp_genes = []
        
        for node in all_nodes:                
            if(float(np.random.uniform(0,1,1)) <= rho_0):
                exp_genes.append(node)
        
        result['expressed_genes_under'].append([]) #note that underexpressed genes are used as a disease picture
        #result['expressed_genes_under'].append(dis_nodes) #note that underexpressed genes are used as a disease picture 
        result['expressed_genes_over'].append(exp_genes)
           
    # if not give to it random expression pattern
    # if sick take some expressed genes from pattern and some at random
    #disease_params['prefix'] += '_p_' + str(disease_params['p']) + '_re_' + str(disease_params['realisation'])
    
    return result

############################################################################### 
    
def simulate_six(simulation_data, disease_params):
    for i in range(1, disease_params['realisations'] + 1): 
        # make network
        if(simulation_data['network_type'] == 'BA'):
            g = nx.barabasi_albert_graph(simulation_data['network_n'], simulation_data['network_m'])
        elif(simulation_data['network_type'] == 'ER'):
            g = nx.erdos_renyi_graph(simulation_data['network_n'], simulation_data['network_p'])  
        elif(simulation_data['model'] == '2D'):
            g = nx.grid_2d_graph(simulation_data['network_x'], simulation_data['network_y'], periodic = True)
        elif(simulation_data['model']  == 'CYC'):
            g = nx.cycle_graph(simulation_data['network_n'])
        elif(simulation_data['model']  == 'REG'):
            g = nx.random_regular_graph(simulation_data['network_d'], simulation_data['network_n'])

        #neighbors_dict = all_neighbors_order(g, simulation_params['order'])
        colored_graph = color_nodes_order(g, disease_params['D'], disease_params['p'], disease_params['order'])
        #colored_graph = color_nodes_order(g, disease_params['D'], disease_params['p'], disease_params['order'])
        
        g_strip = g.copy()
            
        solitary = [ n for n,d in g_strip.degree_iter() if d == 0 ]
        g_strip.remove_nodes_from(solitary)                       
        layout = nx.spring_layout(g_strip)
        
        col_number = 0
        
        plt.figure(figsize=(16,24))
        #plt.figure(figsize=(12,18))
 
        for disease_params['rho_0'] in disease_params['rho_0_list']:
            col_number +=1
        
            disease_prefix = '_G_'  + str(disease_params['G'])
            disease_prefix += '_D_'  + str(disease_params['D']) 
            disease_prefix += '_S_' + str(disease_params['S'])
            #disease_prefix += '_pn_'  + str(disease_params['patients_number'])
  
            disease_prefix += '_A_'   + str(disease_params['A'])
            disease_prefix += '_order_'   + str(disease_params['order'])
            disease_prefix += '_p_'   + str(disease_params['p'])
            disease_prefix += '_i_'   + str(i)
            #disease_prefix += '_rho_0_' + str(disease_params['rho_0'])

            prefix_rnd = simulation_data['model_prefix']    
            prefix     = str(prefix_rnd) + str(disease_prefix) # + '_i_' + str(i)
        
            result = simulate_artificial_disease(disease_params, simulation_data, colored_graph, colored_graph)

            #collective_genes = get_collective_gene_expression(simulation_data, network_genes, expressed_genes_under, expressed_genes_over, phenotype_table, mode = 'normal')        
            collective_genes = get_collective_gene_expression(simulation_data, result['expressed_genes_under'], result['expressed_genes_over'], result['phenotype_table'], mode = 'normal')        
            filtered = collective_genes['flt']
            
            #for flt in [0,1,2,3,5,6,7,8,8,10]:  
            row_number = 0
            for flt in [2,1,0]:
                row_number += 1
                #c_G = 1.0 - np.power(1.0 - nx.density(g_strip), disease_params['rho_0']*disease_params['G'] - 1)
     
                g_over = g_strip.subgraph(filtered['dis_over_flt_' + str(flt)])
            
                solitary_over = len([ n for n,d in g_over.degree_iter() if d == 0 ])

                n = len(g_over.nodes()) 
                if n > 0:     
                    c = float(n - solitary_over)/float(n) 
                else:
                    c = 0
                    
                c_G = 1.0 - np.power(1.0 - nx.density(g_strip), n - 1)                    
                delta_c = c - c_G
             
                F_s  = len(list(set(filtered['dis_over_flt_' + str(flt)])))
                V_G  = len(list(set(filtered['dis_under_flt_' + str(flt)])))
                Vs_G = len(list(set(filtered['dis_under_flt_' + str(flt)]) & set(filtered['dis_over_flt_' + str(flt)])))
                
                try:
                    PPV = float(Vs_G)/float(F_s)
                except:
                    PPV = 0

                try:
                    TPR = float(Vs_G)/float(V_G)  
                except:
                    TPR = 0
                    
                Q = PPV*TPR
                
                plt.subplot(3,2,2*(row_number-1)+col_number)
                
        
                #######################################################################
                
                nx.draw_networkx(g_strip,pos=layout,
                                 with_labels=False,
                                 node_size = 10,
                                 node_color= 'k',
                                 alpha=0.2
                                 )
                
                #######################################################################
                
                # false negative
                nx.draw_networkx(g_strip.subgraph(filtered['dis_under_flt_' + str(flt)]), pos=layout,
                                 with_labels=False,
                                 node_size = 100,
                                 node_color= 'orange',
                                 edge_color = 'orange',
                                 width = 4.0,
                                 alpha=1.0
                                 )   
                                 
                #######################################################################
                
                # false positive
                nx.draw_networkx(g_strip.subgraph(filtered['dis_over_flt_' + str(flt)]), pos=layout,
                                 with_labels=False,
                                 node_size = 100,
                                 node_color= 'lime',
                                 edge_color = 'lime',
                                 width = 4.0,
                                 alpha=1.0
                                 )  
                                 
                #######################################################################
                
                # true positive
                nx.draw_networkx(g_strip.subgraph(list(set(filtered['dis_under_flt_' + str(flt)]) & set(filtered['dis_over_flt_' + str(flt)]))), pos=layout,
                                 with_labels=False,
                                 node_size = 200,
                                 node_color= 'r',
                                 edge_color = 'r',
                                 width = 8.0,
                                 alpha=1.0
                                 )             
                                 
                #######################################################################

                suffix = '_dc_' + str(round(delta_c,2)) + '_Q_' + str(round(Q,2))
                
                try:
                    PPV = float(Vs_G)/float(F_s)
                except:
                    PPV = 0
                 
                try: 
                    TPR = float(Vs_G)/float(V_G) 
                except:
                    TPR = 0        
                
                Q = PPV*TPR
                  
                plt.xticks([])
                plt.yticks([])
                xylim = [-0.1,1.1]
                
                plt.xlim(xylim) 
                plt.ylim(xylim) 
                #plt.title(title, size = 22)    
                
                """
                title =  'G = '  + str(disease_params['G'])
                title += ',   D = '  + str(disease_params['D']) 
                title += ',   S = ' + str(disease_params['S'])
                title += ',   A = '   + str(disease_params['A'])
                title += ',   p = '   + str(disease_params['p'])  + ' \n'
                """
                
                title = 'f = ' + str(flt) 
                title += ',    $\\rho_0$ = ' + str(disease_params['rho_0']) # + ' \n'
                
                #c_text = 'c = ' +  str(round(c,2)) + ' \n'
                #c_text += 'c$_G$ = ' + str(round(c_G,2)) + ' \n'
                #c_text += '$\Delta$c = ' + str(round(delta_c,2)) # + ' \n'
                c_text = '$\Delta$c = ' + str(round(delta_c,2)) # + ' \n'
                
                f_text = 'PPV = ' +  str(round(PPV,2)) + ' \n'
                f_text += 'TPR = ' + str(round(TPR,2)) + ' \n'
                f_text += 'Q = ' + str(round(Q,2)) 
                
                plt.text(0.325, 0.0, c_text, horizontalalignment='left',  verticalalignment='top', size = 32)  

                #plt.text(0.0, 1.0, c_text, horizontalalignment='left',  verticalalignment='top', size = 20)                          
                #plt.text(0.8, 1.0, f_text, horizontalalignment='left',  verticalalignment='top', size = 20)                          
                #plt.text(0.325, 0.0, title, horizontalalignment='left',  verticalalignment='top', size = 20) 
                #plt.title(title, horizontalalignment='left',  verticalalignment='top', size = 20) 
                
                if row_number == 1:
                    plt.title('$\\rho_G$ = ' + str(disease_params['rho_0']), size = 32)
                    
                if col_number == 1:
                    plt.ylabel('f = ' + str(flt), size = 32) 
                
                
                
        #filename = simulation_data['img'] + prefix + '_flt_' + str(flt) + '_rho_0_' + str(disease_params['rho_0']) + suffix 
        filename = simulation_data['img'] + prefix      
        filename = filename.replace('.','_')
        
        plt.tight_layout()
        #plt.savefig(filename + '_network_spring.png')
        #plt.savefig(filename + '_network_spring.pdf')                  
        plt.show() 
        plt.close() 
    

############################################################################### 
    
def simulate_series(simulation_data, disease_params):
    # make network
    if(simulation_data['network_type'] == 'BA'):
        g = nx.barabasi_albert_graph(simulation_data['network_n'], simulation_data['network_m'])
    elif(simulation_data['network_type'] == 'ER'):
        g = nx.erdos_renyi_graph(simulation_data['network_n'], simulation_data['network_p'])  
    elif(simulation_data['model'] == '2D'):
        g = nx.grid_2d_graph(simulation_data['network_x'], simulation_data['network_y'], periodic = True)
    elif(simulation_data['model']  == 'CYC'):
        g = nx.cycle_graph(simulation_data['network_n'])
    elif(simulation_data['model']  == 'REG'):
        g = nx.random_regular_graph(simulation_data['network_d'], simulation_data['network_n'])

    #neighbors_dict = all_neighbors_order(g, simulation_params['order'])
    colored_graph = color_nodes_order(g, disease_params['D'], disease_params['p'], disease_params['order'])
    #colored_graph = color_nodes_order(g, disease_params['D'], disease_params['p'], disease_params['order'])
    
    g_strip = g.copy()
        
    solitary = [ n for n,d in g_strip.degree_iter() if d == 0 ]
    g_strip.remove_nodes_from(solitary)                       
    layout = nx.spring_layout(g_strip)
    
    result = {}
    #result['layout'] = layout
    #result['g'] = g
    #result['g_strip'] = g_strip
 
    for disease_params['rho_0'] in disease_params['rho_0_list']:
        result[str(disease_params['rho_0'])] = {}

        result_disease = simulate_artificial_disease(disease_params, simulation_data, colored_graph, colored_graph)
        collective_genes = get_collective_gene_expression(simulation_data, result_disease['expressed_genes_under'], result_disease['expressed_genes_over'], result_disease['phenotype_table'], mode = 'normal')        
        filtered = collective_genes['flt']
        
        for flt in [2,1,0]:
            #result[str(disease_params['rho_0'])][str(flt)] = {}
            
            tmp_result = {}
            
            tmp_result['extracted_genes']      = list(set(filtered['dis_over_flt_' + str(flt)]))
            tmp_result['disease_genes']        = list(set(filtered['dis_under_flt_' + str(flt)]))
            tmp_result['true_poositive_genes'] = list(set(filtered['dis_under_flt_' + str(flt)]) & set(filtered['dis_over_flt_' + str(flt)]))
            tmp_result['disease_params'] = disease_params
            
            tmp_result['layout'] = layout
            tmp_result['g'] = g
            tmp_result['g_strip'] = g_strip
            
            tmp_result['rho_0'] = disease_params['rho_0']
            tmp_result['flt'] = flt
            
            
            result[str(disease_params['rho_0'])][str(flt)] = tmp_result
            
    return result
            
###############################################################################

def plot_network(tmp_result):   
    g_strip = tmp_result['g_strip']
    layout = tmp_result['layout']
    
    disease_params = tmp_result['disease_params']
   
    plt.figure(figsize=(8,8))

    disease_prefix = '_G_'  + str(disease_params['G'])
    disease_prefix += '_D_'  + str(disease_params['D']) 
    disease_prefix += '_S_' + str(disease_params['S'])
    #disease_prefix += '_pn_'  + str(disease_params['patients_number'])
  
    disease_prefix += '_A_'   + str(disease_params['A'])
    disease_prefix += '_order_'   + str(disease_params['order'])
    disease_prefix += '_p_'   + str(disease_params['p'])
    #disease_prefix += '_i_'   + str(i)
    #disease_prefix += '_rho_0_' + str(disease_params['rho_0'])

    prefix_rnd = simulation_data['model_prefix']    
    prefix     = str(prefix_rnd) + str(disease_prefix) # + '_i_' + str(i)
  
    ###############################################################
    
    g_over = g_strip.subgraph(tmp_result['extracted_genes'])

    solitary_over = len([ n for n,d in g_over.degree_iter() if d == 0 ])

    n = len(g_over.nodes()) 
    if n > 0:     
        c = float(n - solitary_over)/float(n) 
    else:
        c = 0
        
    c_G = 1.0 - np.power(1.0 - nx.density(g_strip), n - 1)                    
    delta_c = c - c_G
 
    F_s  = len(tmp_result['extracted_genes'])
    V_G  = len(tmp_result['disease_genes'])
    Vs_G = len(tmp_result['true_poositive_genes'])
    
    try:
        PPV = float(Vs_G)/float(F_s)
    except:
        PPV = 0

    try:
        TPR = float(Vs_G)/float(V_G)  
    except:
        TPR = 0
        
    Q = PPV*TPR
    
    #######################################################################
    
    nx.draw_networkx(g_strip,pos=layout,
                     with_labels=False,
                     node_size = 10,
                     node_color= 'k',
                     alpha=0.2
                     )
    
    #######################################################################
    
    # false negative
    nx.draw_networkx(g_strip.subgraph(tmp_result['disease_genes']), pos=layout,
                     with_labels=False,
                     node_size = 100,
                     node_color= 'orange',
                     edge_color = 'orange',
                     width = 4.0,
                     alpha=1.0
                     )   
                     
    #######################################################################
    
    # false positive
    nx.draw_networkx(g_strip.subgraph(tmp_result['extracted_genes']), pos=layout,
                     with_labels=False,
                     node_size = 100,
                     node_color= 'lime',
                     edge_color = 'lime',
                     width = 4.0,
                     alpha=1.0
                     )  
                     
    #######################################################################
    
    # true positive
    nx.draw_networkx(g_strip.subgraph(tmp_result['true_poositive_genes']), pos=layout,
                     with_labels=False,
                     node_size = 200,
                     node_color= 'r',
                     edge_color = 'r',
                     width = 8.0,
                     alpha=1.0
                     )             
                     
    #######################################################################

    suffix = '_dc_' + str(round(delta_c,2)) + '_Q_' + str(round(Q,2))
    
    try:
        PPV = float(Vs_G)/float(F_s)
    except:
        PPV = 0
     
    try: 
        TPR = float(Vs_G)/float(V_G) 
    except:
        TPR = 0        
    
    Q = PPV*TPR
      
    plt.xticks([])
    plt.yticks([])
    xylim = [-0.1,1.1]
    
    plt.xlim(xylim) 
    plt.ylim(xylim) 
    #plt.title(title, size = 22)    
    
    """
    title =  'G = '  + str(disease_params['G'])
    title += ',   D = '  + str(disease_params['D']) 
    title += ',   S = ' + str(disease_params['S'])
    title += ',   A = '   + str(disease_params['A'])
    title += ',   p = '   + str(disease_params['p'])  + ' \n'
    """
    
    title = 'f = ' + str(tmp_result['flt']) 
    title += ',    $\\rho_0$ = ' + str(disease_params['rho_0']) # + ' \n'
    
    #c_text = 'c = ' +  str(round(c,2)) + ' \n'
    #c_text += 'c$_G$ = ' + str(round(c_G,2)) + ' \n'
    #c_text += '$\Delta$c = ' + str(round(delta_c,2)) # + ' \n'
    c_text = '$\Delta$c = ' + str(round(delta_c,2)) # + ' \n'
    
    f_text = 'PPV = ' +  str(round(PPV,2)) + ' \n'
    f_text += 'TPR = ' + str(round(TPR,2)) + ' \n'
    f_text += 'Q = ' + str(round(Q,2)) 
    
    plt.text(0.325, 0.0, c_text, horizontalalignment='left',  verticalalignment='top', size = 32)  

    #plt.text(0.0, 1.0, c_text, horizontalalignment='left',  verticalalignment='top', size = 20)                          
    #plt.text(0.8, 1.0, f_text, horizontalalignment='left',  verticalalignment='top', size = 20)                          
    #plt.text(0.325, 0.0, title, horizontalalignment='left',  verticalalignment='top', size = 20) 
    #plt.title(title, horizontalalignment='left',  verticalalignment='top', size = 20) 
    
    #if row_number == 1:
    plt.title('$\\rho_G$ = ' + str(disease_params['rho_0']), size = 32)
        
    #if col_number == 1:
    plt.ylabel('f = ' + str(tmp_result['flt']) , size = 32) 
        
    #filename = simulation_data['img'] + prefix + '_flt_' + str(flt) + '_rho_0_' + str(disease_params['rho_0']) + suffix 
    filename = simulation_data['img'] + prefix      
    filename = filename.replace('.','_')
    
    plt.tight_layout()
    #plt.savefig(filename + '_network_spring.png')
    #plt.savefig(filename + '_network_spring.pdf')                  
    plt.show() 
    plt.close() 
        
###############################################################################
###############################################################################
###############################################################################

#neighbors_dict = all_neighbors_order(g, simulation_params['order'])

###############################################################################
################################ SETUP ########################################
###############################################################################

simulation_data = {}

#################################### COMMON ###################################

simulation_data['stats_simple'] = True
simulation_data['make_z_scores'] = True

########################## COLLECTIVE EXPRESSION ##############################

simulation_data['shuffle'] = True
simulation_data['shuffle'] = False
simulation_data['shuffled_samples'] = 2

simulation_data['excluding'] = True
simulation_data['excluding'] = False
simulation_data['filter_range'] = 11

simulation_data['fields'] = {'dis':'{disease} == 1'}

simulation_data['multiproc'] = False
#simulation_data['multiproc'] = True
simulation_data['processors'] = 32

############################ DISEASE PARAMS ###################################

disease_params = {}
disease_params['order'] = 1 #order of clustering neighborhood 
disease_params['patients_number'] = 100 # pn

"""
D_list     = [10, 50, 200] #disease related genes
S_list     = [10, 20, 50] #sick patiens number
rho_0_list = [0.005, 0.01, 0.05, 0.1] #expression density
A_list     = [0.0, 0.1, 0.5, 1.0] #disease expression density scaling
p_list     = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9] #clustering probability
"""

"""
# quick negative effect
D_list     = [20, 50, 100, 200] #disease related genes
S_list     = [10, 30] #sick patiens number
rho_0_list = [0.01, 0.02, 0.05] #expression density
#A_list     = [0.0, 0.1, 0.5, 1.0] #disease expression density scaling
#A_list     = [0.1, 0.2, 0.5, 1.0, 0.0] #disease expression density scaling
A_list     = [1.0, 0.5, 0.2, 0.0] #disease expression density scaling

#p_list     = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9] #clustering probability

p_list     = [0.9, 0.75, 0.5, 0.25, 0.1, 0.0] #clustering probability
"""

"""
# quick negative effect
D_list     = [50, 20, 100, 200] #disease related genes
S_list     = [30, 10] #sick patiens number
rho_0_list = [0.01, 0.02, 0.03, 0.04, 0.05] #expression density
#A_list     = [0.0, 0.1, 0.5, 1.0] #disease expression density scaling
#A_list     = [0.1, 0.2, 0.5, 1.0, 0.0] #disease expression density scaling
A_list     = [0.5, 0.2, 0.0] #disease expression density scaling

#p_list     = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9] #clustering probability

p_list     = [0.5, 0.1, 0.9, 0.0] #clustering probability
"""


# quick negative effect
D_list     = [50] #disease related genes
S_list     = [10] #sick patiens number
rho_0_list = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1] #expression density
rho_0_list = [0.01, 0.02] #expression density
#A_list     = [0.0, 0.1, 0.5, 1.0] #disease expression density scaling
#A_list     = [0.1, 0.2, 0.5, 1.0, 0.0] #disease expression density scaling
A_list     = [0.5] #disease expression density scaling
#p_list     = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9] #clustering probability
p_list     = [0.5] #clustering probability

# 2x
D_list     = [50] #disease related genes
S_list     = [15] #sick patiens number
rho_0_list = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1] #expression density
rho_0_list = [0.01, 0.02] #expression density
#A_list     = [0.0, 0.1, 0.5, 1.0] #disease expression density scaling
#A_list     = [0.1, 0.2, 0.5, 1.0, 0.0] #disease expression density scaling
A_list     = [0.25] #disease expression density scaling
#p_list     = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9] #clustering probability
p_list     = [0.3] #clustering probability

# 2x3
D_list     = [50] #disease related genes
S_list     = [15] #sick patiens number
rho_0_list = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1] #expression density
rho_0_list = [0.01, 0.02, 0.03, 0.04, 0.05] #expression density
#A_list     = [0.0, 0.1, 0.5, 1.0] #disease expression density scaling
#A_list     = [0.1, 0.2, 0.5, 1.0, 0.0] #disease expression density scaling
A_list     = [0.5] #disease expression density scaling
#p_list     = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9] #clustering probability
p_list     = [0.3] #clustering probability


"""
# quick negative effect
D_list     = [50] #disease related genes
S_list     = [30] #sick patiens number
rho_0_list = [0.01] #expression density
#A_list     = [0.0, 0.1, 0.5, 1.0] #disease expression density scaling
A_list     = [0.25] #disease expression density scaling
p_list     = [0.75] #clustering probability

A_list     = [0.15] #disease expression density scaling
p_list     = [0.5] #clustering probability
"""

#simulation_data['shuffled_samples'] = 100
disease_params['realisations'] = 1

############################ NETWORK MODEL ####################################

#simulation_data['model'] = 'BA_1'
#simulation_data['model'] = 'BA_2'
#simulation_data['model'] = 'BA_3'

#simulation_data['model'] = 'ER_0.001'
simulation_data['model'] = 'ER_0.006'
#simulation_data['model'] = 'ER_0.01'
#simulation_data['model'] = 'ER_0.1'

#simulation_data['model'] = '2D'
#simulation_data['model']= 'CYC'

###############################################################################
############################### PRERUN ########################################
###############################################################################

if(simulation_data['model'] == 'BA_1'):
    simulation_data['network_type']  = 'BA'
    simulation_data['network_n'] = 1000
    simulation_data['network_m'] = 1
    simulation_data['model_prefix']  = 'BA_nn_' + str(simulation_data['network_n']) + '_nm_' + str(simulation_data['network_m']) 
    simulation_data['in_data_path']  = str(this_path) + 'out_BA_1/'
    simulation_data['out_data_path'] = str(this_path) + 'out_BA_1/'  
elif(simulation_data['model'] == 'BA_2'):
    simulation_data['network_type']  = 'BA'
    simulation_data['network_n'] = 1000
    simulation_data['network_m'] = 2
    simulation_data['model_prefix']  = 'BA_nn_' + str(simulation_data['network_n']) + '_nm_' + str(simulation_data['network_m']) 
    simulation_data['in_data_path']  = str(this_path) + 'out_BA_2/'
    simulation_data['out_data_path'] = str(this_path) + 'out_BA_2/'       
elif(simulation_data['model'] == 'BA_3'):
    simulation_data['network_type']  = 'BA'
    simulation_data['network_n'] = 1000
    simulation_data['network_m'] = 3
    simulation_data['model_prefix']  = 'BA_nn_' + str(simulation_data['network_n']) + '_nm_' + str(simulation_data['network_m']) 
    simulation_data['in_data_path']  = str(this_path) + 'out_BA_3/'    
    simulation_data['out_data_path'] = str(this_path) + 'out_BA_3/'
elif(simulation_data['model'] == 'ER_0.001'):
    simulation_data['network_type']  = 'ER'
    simulation_data['network_n'] = 1000
    simulation_data['network_p'] = 0.001 
    simulation_data['model_prefix']  = 'ER_nn_' + str(simulation_data['network_n']) + '_np_' + str(simulation_data['network_p']) 
    simulation_data['in_data_path']  = str(this_path) + 'out_ER_0.001/'
    simulation_data['out_data_path'] = str(this_path) + 'out_ER_0.001/'
elif(simulation_data['model'] == 'ER_0.006'):
    simulation_data['network_type']  = 'ER'
    simulation_data['network_n'] = 1000
    simulation_data['network_p'] = 0.006 
    simulation_data['model_prefix']  = 'ER_nn_' + str(simulation_data['network_n']) + '_np_' + str(simulation_data['network_p']) 
    simulation_data['in_data_path']  = str(this_path) + 'out_ER_0.006/'
    simulation_data['out_data_path'] = str(this_path) + 'out_ER_0.006/'
elif(simulation_data['model'] == 'ER_0.01'):
    simulation_data['network_type']  = 'ER'
    simulation_data['network_n'] = 1000
    simulation_data['network_p'] = 0.01 
    simulation_data['model_prefix']  = 'ER_nn_' + str(simulation_data['network_n']) + '_np_' + str(simulation_data['network_p']) 
    simulation_data['in_data_path']  = str(this_path) + 'out_ER_0.01/'
    simulation_data['out_data_path'] = str(this_path) + 'out_ER_0.01/'
elif(simulation_data['model'] == 'ER_0.1'):
    simulation_data['network_type']  = 'ER'
    simulation_data['network_n'] = 1000
    simulation_data['network_p'] = 0.1 
    simulation_data['model_prefix']  = 'ER_nn_' + str(simulation_data['network_n']) + '_np_' + str(simulation_data['network_p']) 
    simulation_data['in_data_path']  = str(this_path) + 'out_ER_0.1/'
    simulation_data['out_data_path'] = str(this_path) + 'out_ER_0.1/'
elif(simulation_data['model'] == '2D'):
    simulation_data['network_type']  = '2D'
    simulation_data['network_x'] = 40
    simulation_data['network_y'] = 25 
    simulation_data['model_prefix'] = '2D_nx_' + str(simulation_data['network_x']) + '_ny_' + str(simulation_data['network_y'])
    simulation_data['in_data_path']  = str(this_path) + 'out_2D/'
    simulation_data['out_data_path'] = str(this_path) + 'out_2D/'
elif(simulation_data['model'] == 'CYC'):
    simulation_data['network_type']  = 'CYC'
    simulation_data['network_n'] = 1000
    simulation_data['model_prefix'] = 'CYC_nn_' + str(simulation_data['network_n'])
    simulation_data['in_data_path']  = str(this_path) + 'out_CYC/'
    simulation_data['out_data_path'] = str(this_path) + 'out_CYC/'
elif(simulation_data['model'] == 'REG'):
    simulation_data['network_type']  = 'REG'
    simulation_data['network_n'] = 1000
    simulation_data['network_d'] = 10
    simulation_data['model_prefix'] = 'REG_nn_' + str(simulation_data['network_n']) + '_nd_' + str(simulation_data['network_d'])
    simulation_data['in_data_path']  = str(this_path) + 'out_REG/'
    simulation_data['out_data_path'] = str(this_path) + 'out_REG/' 

simulation_data['img'] = str(this_path) + 'img_sixpack_2/' 

###############################################################################

whole_params_stack = []
                   
for D in D_list: 
    for S in S_list:
        #for rho_0 in rho_0_list: 
        for A in A_list:      
            for p in p_list:                     
                disease_params_2 = disease_params.copy()   
                disease_params_2['G']     = simulation_data['network_n'] # genes
                disease_params_2['D']     = D                                                             
                disease_params_2['S']     = S
                disease_params_2['rho_0_list'] = rho_0_list
                disease_params_2['A']     = A
                disease_params_2['p']     = p
                
                record = {}
                record['simulation_data'] = simulation_data
                record['disease_params']  = disease_params_2

                whole_params_stack.append(record)

###############################################################################
############################### RUN ###########################################
###############################################################################

#start = time.time()
    
for whole_params in whole_params_stack:
    #print "------------------------------------"
    #add = Artificial_disease_1dot2_3()
    #add.simulate_six(whole_params['simulation_data'], whole_params['disease_params'])
    #simulate_six(whole_params['simulation_data'], whole_params['disease_params'])   
    #self.simulate(whole_params['simulation_data'], whole_params['disease_params'])
    
    series = simulate_series(whole_params['simulation_data'], whole_params['disease_params']) 
    """
    for key, value in series.items():
        for subkey, subvalue in value.items():
            plot_network(subvalue)
    """
            
#plot_network(series[str(0.02)][str(2)]) 
 
#print "whole time = " + str(time.time() - start)     