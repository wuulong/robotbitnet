#RobotBitNet domain monitor
#Features:
#    log RobotBitNet network
#    support dm send raw command through radio tx
#    dm prototype with nodes(all init information from uart rx)
#    CLI support
#    pertype info, monitor id, maxnodes test
#    support networkx, monitor per-node rate
#    support rssi capacity, estimate distance
#    plot sensor information history
#    plot rssi history
#Default:
#    ask end point report number by sequence
#    115200,N81
#    hardcode uart device name
#Architecture:
#    device uart tx all rx/tx content
#    domain monitor log to file
#Verification:
#    Mac OK
#Requirement:
#    pyserial, networkx
#LICENSE: MIT
#Author: WuLung Hsu, wuulong@gmail.com
#Document: https://paper.dropbox.com/doc/MbitBot--AWWwIfCnEicRuc7gSfO_tmcJAg-DG5SSj5zQhBv1CoAgDtAG

import threading
from serial import *
import time
import sys
import cmd
from datetime import datetime
import random

ser_name = '/dev/cu.usbmodem142302' #different environment may changed
VERSION = "0.6.2"

dm = None
cli = None
th = None

IDX_VISCNT=0
IDX_LOGO=1
IDX_LIGHT=2
IDX_SOUND=3
IDX_A_X=4
IDX_A_Y=5
IDX_A_Z=6

def mymap(x, in_min, in_max, out_min, out_max):
    value = int((x-in_min) * (out_max-out_min) / (in_max-in_min) + out_min)
    if value>= out_max:
        value = out_max -1
    elif value < out_min:
        value = out_min

    return value

#calibrate by match any record in the range table
def calibrate_by_offset(cm_m, rssi_m):
    global range_ref
    diff = 0
    for i in range(len(range_ref)):
        [cm,rssi] = range_ref[i]
        if cm_m == cm:
            diff = rssi_m - rssi
            break
    for i in range(len(range_ref)):
        range_ref[i][1] = range_ref[i][1] + diff


def estimate_distance(rssi_m,range_ref):
    max_i = 0
    min_i = 0
    if rssi_m>=range_ref[0][1]:
       return 0
    if rssi_m <= range_ref[len(range_ref)-1][1]:
        return range_ref[-1][0]
    for i in range(len(range_ref)):
        [cm,rssi] = range_ref[i]
        if rssi_m >= rssi:
            max_i = i
            break
        else:
            min_i = i
    return mymap(rssi_m,range_ref[min_i][1],range_ref[max_i][1],range_ref[min_i][0],range_ref[max_i][0])



def test_estimate():
    while True:
        for i in range(-65,-94,-1):
            value = estimate_distance(i,range_ref)
            print("%f->%i"%(i,value))
        sleep(10000)

def file_to_lines(pathname):
    fo = open(pathname, "r")
    #lines = fo.readlines()
    lines = fo.read().splitlines()
    fo.close()
    return lines

# V1 experience, V2 hardware seems different
cal_cm=50
cal_rssi=-76.0

range_ref = [
    [ 0   , -65.2 ],
    [ 10  , -66.0 ],
    [ 20  , -69.1 ],
    [ 30  , -71.0 ],
    [ 40  , -73.0 ],
    [ 50  , -76.0 ],
    [ 75  , -77.0 ],
    [ 100 , -79.0 ],
    [ 125 , -82.0 ],
    [ 150 , -84.6 ],
    [ 200 , -87.6 ],
    [ 250 , -90.0 ],
    [ 300 , -93.7 ]]


class Node():

    def __init__(self,id):
        self.id = id
        self.last_rx = 0
        self.ms = False
        self.cs = False
        self.tinfo = {} #pertype infor, type as id, content [], ex: 20->[number]
        self.rssis = {} #remote node id as key, content rssi
        self.rssis_his = [] # rssi history, [now,remote_node_id,rssi]
        self.sensing = [] # sensing information, from visibility_cnt
        self.sensing_his = [] # sensing history, key = now()
    #l3: [] for l3 information, ex [1,20,number]
    def rx_update(self,l3):
        self.last_rx = time.time()
        #print("rx_update=%s"%(str(l3)))
        if len(l3)>=2:
            tid = int(l3[1])
            self.tinfo[tid] = l3[2:]
            if tid== 1 or tid==2 or tid==3:
                self.ms = int(l3[2])
                self.cs = int(l3[3])
            if tid==3: #visibility_cnt, int(pin_logo.is_touched()),di.read_light_level(),microphone.sound_level(),a_x,a_y,a_z
                self.sensing = l3[4:] 
                now = datetime.now()
                self.sensing_his.append([now,self.sensing])
            if tid==11:
                self.rssis[int(l3[2])] = int(l3[3])
                self.rssis_his.append([datetime.now(),int(l3[2]),int(l3[3])])
                
            #rssi handler, type=11
        

    def desc(self):
        t_now = time.time()
        txt = "node ID=%2i, last_rx=%2.3f s,ms=%i,cs=%i" %(self.id,self.last_rx - t_now,self.ms,self.cs)
        keys = self.tinfo.keys()
        #desc sensor information
        for id in sorted(keys):
            txt +="\n\ttype[%i]=%s" %(id,self.tinfo[id])
        if len(self.sensing)>0:
            sensing_str = "\n\tSensing:VISCNT=%s,LOGO=%s,LIGHT=%s,SOUND=%s,A_X=%s,A_Y=%s,A_Z=%s" % (self.sensing[IDX_VISCNT],self.sensing[IDX_LOGO],self.sensing[IDX_LIGHT],self.sensing[IDX_SOUND],self.sensing[IDX_A_X],self.sensing[IDX_A_Y],self.sensing[IDX_A_Z])
            txt += sensing_str
        #desc rssi, range information
        keys = self.rssis.keys()
        for id in sorted(keys):
            rssi = self.rssis[id] 
            cm = estimate_distance(rssi,range_ref)
            txt +="\n\trssi[%i]=%i -> %i cm" %(id,rssi,cm)
        return txt
    def sensing_his_clear(self):
        self.sensing_his = []
    def desc_sensing_his(self):
        txt = ""
        for v in self.sensing_his:
            sensing = v[1]
            sensing_str = "\nTIME=%s|NODE=%i,VISCNT=%s,LOGO=%s,LIGHT=%s,SOUND=%s,A_X=%s,A_Y=%s,A_Z=%s" % (v[0],self.id,sensing[IDX_VISCNT],sensing[IDX_LOGO],sensing[IDX_LIGHT],sensing[IDX_SOUND],sensing[IDX_A_X],sensing[IDX_A_Y],sensing[IDX_A_Z])
            txt += sensing_str
        return txt
    def rssi_his_clear(self):
        self.rssis_his = []

    def desc_rssi_his(self):
        txt = ""
        for v in self.rssis_his:
            rssi_str = "\nTIME=%s|NODE=%i,RID=%i,RSSI=%i" % (v[0],self.id,v[1],v[2])
            txt += rssi_str
        return txt

# DM function
class DM():
    def __init__(self):
        self.dmid=0 # also sid,no need = 1
        self.sid=1
        self.nodes = {} #id as index, not include self
        self.uids = []
        self.nn_cnt = {} #sid-did as key, [current_cnt, ori_cnt, rate ]
        self.ready = False
        self.t_last_mt = 0
        
    def reset(self):
        self.__init__()
    
    def get_nodes_cnt(self):
        if self.ready:
            return len(self.uids)
        else:
            return 0
    def get_max_id(self):
        max_id=self.sid
        for i in range(len(self.uids)):
            if self.uids[i]>max_id:
                max_id = self.uids[i]
        return max_id
    def get_rate_between(self,sid,did,both=True):
        
        rate = 0 
        key = "%i-%i" %(sid,did)
        if key  in self.nn_cnt:
            rate += self.nn_cnt[key][2]
        if both:
            key = "%i-%i" %(did,sid)
            if key  in self.nn_cnt:
                rate += self.nn_cnt[key][2]
        return rate
    def get_distance_between(self,sid,did):
        if not did in self.nodes:
            return 0
        node = self.nodes[did]
        if not sid in node.rssis:
            return 0
        
        rssi = node.rssis[sid]
        
        if not sid in self.nodes:
            return rssi
        node = self.nodes[sid]
        if not did in node.rssis:
            return rssi
        
        rssi += node.rssis[did]
        return int(rssi/2)
        
    def get_sym_fromid(self,id):
        if id == dm.dmid:
            sym = "d"
        else:                
            if id  in dm.nodes:
                node = dm.nodes[id]

                if node.ms:
                    sym = "l"
                else:
                    sym = "e"
                if node.cs:
                    sym = sym.upper()
            else:
                sym = " "
        return sym

    # monitor network rate
    def proc_traffic(self,sid,did):
        if did==0 or did!=0:
            key = "%i-%i" %(sid,did)
            if key in self.nn_cnt:
                self.nn_cnt[key][0]+=1
                pass
            else:
                self.nn_cnt[key] = [0,0,0]
        
    def desc(self):
        if dm.ready:
            str = "Domain nodes count=%i\nDM/broker ID=%i\n" %(dm.get_nodes_cnt(),dm.dmid)
            print(str)
            keys = dm.nodes.keys()
            for id in sorted(keys):
                node = dm.nodes[id]
                print(node.desc())
            keys = dm.nn_cnt.keys()
            for key in sorted(keys):
                nn = dm.nn_cnt[key]
                ids = key.split("-")
                print("%s->%s : %i,%i,%i" %(ids[0],ids[1],nn[0],nn[1],nn[2]))
        else:
            print("broker not ready!")
        
    #l1 T/R=
    #l2 sid:did:1,type,pertype
    #l3 1,20,num
    def proc_record(self,rec):
        with open('dm.log', 'a') as log_file:
            log_file.write(rec)
            log_file.write("\n")
        l1 = rec.split("=")
        if len(l1)==2:
            tr , l2_str = l1 
            l2 = l2_str.split(":")
            if len(l2)==3:
                sid,did,ap_str = l2
                sid = int(sid)
                did = int(did)
                self.proc_traffic(sid,did)
                l3 = ap_str.split(",")  
                if tr == "T" and self.dmid == 0:          
                    self.dmid = sid
                    self.sid = sid 
                    self.ready = True
                if tr == "T" and did==0: # maintain  
                    time_now = time.time()  
                    ids_need_del = []
                    for id in self.nodes.keys():
                        if time_now - self.nodes[id].last_rx > 4.9:
                            ids_need_del.append(id)
                    for id in ids_need_del: 
                        del self.nodes[id]
                        pos = self.uids.index(id)
                        if pos>=0:
                            del self.uids[pos]
                    if self.t_last_mt>0:
                        if time_now - self.t_last_mt >= 4.9:
                            for key in self.nn_cnt:
                                nn = self.nn_cnt[key]
                                nn[2] = nn[0] * 12
                                nn[1] += nn[0]
                                nn[0]=0
                            self.t_last_mt = time_now
                        else:
                            pass
                    else:
                        self.t_last_mt = time_now
                if tr == "R" or tr=="T":
                    if not sid in self.uids:
                        self.uids.append(sid)
                        self.nodes[sid] = Node(sid)
                        self.nodes[sid].rx_update(l3)                        
                    else:
                        if sid in self.nodes:
                            self.nodes[sid].rx_update(l3)



             

class DmCli(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = 'Dm>'
        self.user_quit = False
        pass
    def do_quit(self, line):
        """quit"""
        self.user_quit = True
        return True
    def do_reset(self,line):
        """reset DM"""
        dm.reset()
    def do_dminfo(self,line):
        """Show DM information every second with [cnt] time
            dminfo [cnt]
        """
        if line.isnumeric():
            cnt = int(line)
            while cnt >0:
                dm.desc()
                cnt-=1
                time.sleep(1)
                
                
        else:
            dm.desc()

    def wait_dm_ready(self):
        while dm.dmid==0:
            time.sleep(0.1)
    def do_version(self,line):
        """Report software version"""
        out = "DmMonitor V%s" %(VERSION)
        print(out)
    def do_mon_ids(self,line):
        """Monitor ID/main status"""
        #ss-12345678901234567890
        #01-.DL.
        txt = "SS-"
        max_id = dm.get_max_id() 
        for i in range(1, max_id+1):
            txt += "%s" % (i%10)
        #txt += "\n"
        print(txt)

        for t in range(10): 
            txt = "%2i-" %(t)    
            for i in range(1, max_id+1):
                sym = dm.get_sym_fromid(i)
                txt += sym
                
            print(txt)
            time.sleep(1)
    
        
    def do_network(self,line):
        """Using networkx to plot current network with update per second
            do_network [with_update]    #with_update 0:no update, 1: update     
        """
        import matplotlib.pyplot as plt
        import matplotlib.animation as an
        import networkx as nx
        
        G = nx.Graph()
        
        
        def nx_update(num=0):
            fig.clf()
            fig.suptitle("Current network status")
            G.clear()
            
            #for did in dm.nodes.keys():
            #    rate = dm.get_rate_between(dm.dmid,did)
            #    rssi = dm.get_distance_between(dm.dmid,did)
                
            #    G.add_edge(str(dm.dmid), str(did), weight= rate+1,length=5 )
            
            for id1 in dm.nodes.keys():
                for id2 in dm.nodes.keys():
                    if id2>id1:
                        rate = dm.get_rate_between(id2,id1)
                        rssi = dm.get_distance_between(id2,id1)
                        sym2 = dm.get_sym_fromid(id2)
                        sym1 = dm.get_sym_fromid(id1)
                        n1 = "%i-%s" %(id2,sym2)
                        n2 = "%i-%s" %(id1,sym1)
                        G.add_edge(n1,n2, rate=rate,rssi=rssi)
            
            elarge = [(u, v) for (u, v, d) in G.edges(data=True) if d['rate'] > 0]
            esmall = [(u, v) for (u, v, d) in G.edges(data=True) if d['rate'] <= 0]
            
            pos = nx.spring_layout(G)  # positions for all nodes
            
            # nodes
            nx.draw_networkx_nodes(G, pos, node_size=700)
            
            # edges
            nx.draw_networkx_edges(G, pos, edgelist=elarge,
                                   width=6)
            nx.draw_networkx_edges(G, pos, edgelist=esmall,
                                   width=6, alpha=0.5, edge_color='b', style='dashed')
            
            # labels
            nx.draw_networkx_labels(G, pos, font_size=20, font_family='sans-serif')
            nx.draw_networkx_edge_labels(G, pos)
            plt.axis('off')
        
        fig, ax = plt.subplots() 
        
        nx_update(1)
        if line=="1":
            ani = an.FuncAnimation(fig, nx_update,init_func=nx_update, frames=6, interval=5000, repeat=False)
        plt.show()
    def do_sensing_his(self,line):
        """show per node sensing history 
            sensing_his [node_id] #0: all, c: clear history
        """
        if line == "c":
            for id in  dm.nodes.keys():
                node = dm.nodes[id]
                node.sensing_his_clear()
            return 
        if line.isnumeric():
            id = int(line)
        else:
            return 
        if id==0:
            for id in  dm.nodes.keys():
                node = dm.nodes[id]
                print(node.desc_sensing_his())
        elif id in dm.nodes.keys():    
            node = dm.nodes[id]
            print(node.desc_sensing_his())
    def do_sensing_plot(self,line):
        """plot sensing history
            
            1. plot one node with all sensor 
                sensing_plot [id] 
            2. plot all node with one sensor
                sensing_plot 0 [col_id]
            3. plot all nodes
                sensing_plot 0
            4. plot one node with one sensor
                sensing_plot [id] [col_id]
            col_id : IDX_VISCNT=0,IDX_LOGO=1,IDX_LIGHT=2,IDX_SOUND=3,IDX_A_X=4,IDX_A_Y=5,IDX_A_Z=6
        """
        import matplotlib.pyplot as plt

        cols = line.split()
        if len(cols)==0:
            return
        id_input = int(cols[0])
        #print("id_input = %i" %(id_input))
        titles = ['VISCNT','LOGO','LIGHT','SOUND','A_X','A_Y','A_Z']
        keys = dm.nodes.keys()
        if len(cols)>1:
            col_id = int(cols[1])
            #print("need plot")
            if id_input>0: # case 4
                id = id_input
                if id in sorted(keys):
                    node = dm.nodes[id]
                    sensing_his = node.sensing_his
                
                # plot this case
                x_vals = list(range(len(sensing_his)))
                v_y = [int(v[1][col_id]) for v in sensing_his]
                fig, axarr =plt.subplots(1,1,sharex=True,figsize=(20, 10))
                axarr.plot(x_vals,v_y)
                axarr.set_title("%s" %(titles[col_id]))
                fig.canvas.set_window_title('Node %s' %(id))
                
            else: #case 2
                
                v_ys = {}
                v_xs = {}
                for id in sorted(keys):
                    node = dm.nodes[id]
                    sensing_his = node.sensing_his
                    x_vals = list(range(len(sensing_his)))
                    v_xs[id]=x_vals
                    v_y = [int(v[1][col_id]) for v in sensing_his]
                    v_ys[id]=v_y
                node_cnt = len(dm.nodes.keys())
                fig, axarr =plt.subplots(node_cnt,1,sharex=True,figsize=(20, 10))
                idx=0
                for id in sorted(keys):
                    axarr[idx].plot(v_xs[id],v_ys[id])
                    axarr[idx].set_title("Node %s:%s" %(id,titles[col_id]))
                    idx +=1
                fig.canvas.set_window_title('All node: %s' %(titles[col_id]))
                
        else: #case 1,3
            for id in sorted(keys):
                node = dm.nodes[id]
                sensing_his = node.sensing_his
                if id_input>0 and id!=id_input:
                    #print("id=%i" %(id))
                    pass
                else:
                    #print("plot node %s" %(id))
                    x_cnt=2
                    y_cnt=4
                    fig, axarr =plt.subplots(y_cnt,x_cnt,sharex=True,figsize=(20, 10))
            
                    x_vals = list(range(len(sensing_his)))
                    
                    for dy in range(y_cnt):
                        for dx in range(x_cnt):
                            idx = dy * x_cnt + dx
                            if idx < len(titles):
                                v_y = [int(v[1][idx]) for v in sensing_his]
                                #axarr[dy][dx].scatter(x_vals,v_y)
                                axarr[dy][dx].plot(x_vals,v_y)
                                axarr[dy][dx].set_title("%s" %(titles[idx]))
            
            
                    #fig.suptitle('Node %s , x-axis (s)' %(id), fontsize=16)
                    fig.canvas.set_window_title('Node %s' %(id))

                
        plt.show()
    def do_rssi_his(self,line):
        """show per node rssi history 
            rssi_his [node_id] #0: all, c: clear history
        """
        if line == "c":
            for id in  dm.nodes.keys():
                node = dm.nodes[id]
                node.rssi_his_clear()
            return 
        if line.isnumeric():
            id = int(line)
        else:
            return 
        if id==0:
            for id in  dm.nodes.keys():
                node = dm.nodes[id]
                print(node.desc_rssi_his())
        elif id in dm.nodes.keys():    
            node = dm.nodes[id]
            print(node.desc_rssi_his())

    def do_rssi_plot(self,line):
        """plot rssi history
            
            1. plot one node with all rssi 
                rssi_plot [id] 
            2. plot all node with one node's rssi
                rssi_plot 0 [rid]
            3. plot all nodes
                rssi_plot 0
            4. plot one node with one rssi
                rssi_plot [id] [rid]
            
        """
        import matplotlib.pyplot as plt

        cols = line.split()
        if len(cols)==0:
            return
        id_input = int(cols[0])
        #print("id_input = %i" %(id_input))
        x_vals = []
        v_y = []
        keys = dm.nodes.keys()
        if len(cols)>1:
            rid = int(cols[1])
            #print("need plot")
            if id_input>0: # case 4
                id = id_input
                if id in sorted(keys):
                    node = dm.nodes[id]
                    rssis_his = node.rssis_his
                
                # plot this case
                xi=0
                for v in rssis_his: #[now, rid, rssi]
                    if v[1]==rid:
                        x_vals.append(xi)
                        xi+=1
                        v_y.append(v[2])
                fig, axarr =plt.subplots(1,1,sharex=True,figsize=(20, 10))
                axarr.plot(x_vals,v_y)
                axarr.set_title("RSSI of Node %s from rid=%s" %(id, rid))
                fig.canvas.set_window_title('Node %s' %(id))
                
            else: #case 2
                pass
                
        else: #case 1,3
            pass
                
        plt.show()

    def demo1(self,show_num):
        sid = dm.sid
        dids = dm.nodes.keys()
        # send command here
        for did in dids:
            if not sid==did:
                th.serial_send("%i:%i:1,20,%i="%(sid,did,show_num)) 
            show_num+=1
            time.sleep(0.5)

    def demo2(self):
        sid = dm.sid
        dids = dm.nodes.keys()
        # send command here
        for did in dids:
            if not sid==did:
                txt_send = "%i:%i:1,25,%i,%i,%i,%i="%(sid,did,did,0,0,60)
                th.serial_send(txt_send) 
            #time.sleep(1)        
    def do_demo(self,line):
        """Current Demo : 
            1. EP show number by sequence
            2. Nodes show current ID's RGB LED with blue color
            """
        self.wait_dm_ready()
        show_num = 1 
        for i in range(5):
            self.demo1(show_num)            
            time.sleep(1)
            show_num+=1
        self.demo2()
    def do_tx_cmd(self,line):
        """Send RAW command by user request
            ex: tx_cmd 1:3:1,20,3
        """
        self.wait_dm_ready()
        txt_send = line
        th.serial_send("%s=" %(txt_send)) 
    def do_act(self,line):
        """action command
            act [act_id] 
                act_id: 
                1) All RGD LED off, 
                2) random RGB
                    act 2 [count]
        """
        act_id = line
        cols = line.split()
        if act_id=="1": #clear RGB LEDs
            sid = dm.sid
            dids = dm.nodes.keys()
            # send command here
            for did in dids:
                if not sid==did:
                    for led_id in range(8):
                        th.serial_send("%i:%i:1,25,%i,0,0,0="%(sid,did,led_id))
                        time.sleep(0.1) 
        if cols[0]=="2": #random RGB
            count = int(cols[1])
            sid = dm.sid
            dids =list(dm.nodes.keys())
            for i in range(count):
                did = random.choice(dids)
                led_id=random.randint(0, 7)
                r=random.randint(0, 255)
                g=random.randint(0, 255)
                b=random.randint(0, 255)
                txt_send = "%i:%i:1,25,%i,%i,%i,%i="%(sid,did,led_id,r,g,b)
                th.serial_send(txt_send)
                time.sleep(0.5) 
            # send command here
            

    def do_script(self,line):
        """run script
            script [filename]
        """
        filename = line
        cmds = file_to_lines(filename)
        try:
            for cmd_str in cmds:
                if not cmd_str.strip()=="":
                    if not cmd_str=="#":
                        now = datetime.now()
                        print("%s:cmd=%s" %(now,cmd_str))
                        cmd_cols = cmd_str.split(" ")
                        str1 = " ".join(cmd_cols[1:])
                        if cmd_cols[0]=="tx_cmd":
                            self.do_tx_cmd(str1)
                            time.sleep(0.1)
                        if cmd_cols[0]=="sleep":
                            time.sleep(int(str1)/1000)
                        if cmd_cols[0]=="car_move":
                            self.do_car_move(str1)
                    
        except:
            print("exception! cmd=%s" %(cmd_str))

    def do_car_move(self,line):
        """car move command
            car_move [did] [cmd] 
                did: 0 for all
                cmd format: 2-digit-num for left, right, 2-digit-num for power. number from 0-99  
                example) 5050: stop, 5099: front, 5000: right, 9999, left: 0099
            ex: car_move 2 9999
        """
        cols = line.split()
        if len(cols)>=2:
            did = int(cols[0])
            cmd = int(cols[1])
        else:
            return
        
        sid = dm.sid
        dids = dm.nodes.keys()
        if did==0:
            th.serial_send("%i:%i:1,23,%i=" %(sid,did,cmd))
            
        else:
            if did in dids:
                th.serial_send("%i:%i:1,23,%i=" %(sid,did,cmd))
 
            
    def do_demo_rccar(self,line):
        """Demo rc car"""
        self.wait_dm_ready()       

        sid = dm.sid
        
        # send command here
        dids = dm.nodes.keys()
        for did in dids:
            if not did == sid:
                # dir = 0 or 1, with different speed
                print("drive car. dir = 0 or 1, with different speed")
                for i in range(0,100,10):
                    v1 = i
                    v2 = i
                    th.serial_send("%i:%i:1,22,%i,%i="%(sid,did,v1,v2)) 
                    time.sleep(0.25)
                # different turn speed
                print("drive car. different turn speed")
                for i in range(0,100,10):
                    percent = i
                    go_value = 50
                    th.serial_send("%i:%i:1,22,%i,%i="%(sid,did,percent,go_value)) 
                    time.sleep(0.5)

                th.serial_send("%i:%i:1,22,%i,%i="%(sid,did,50,50)) 
            
    def do_maxnodes_test(self,line):
        """Test Max nodes
            maxnodes_test [max_nodes_cnt]
        """
        self.wait_dm_ready()
        show_num = 2
        test_did=0
        
        max_nodes_cnt = 20
        if not line =="":
            max_nodes_cnt = int(line)

        sid = dm.sid
        # send command here
        for did in dm.nodes.keys():
            if test_did==0:
                test_did = did
            print("testing id=%i, max counts=%i" %(did,show_num))
            th.serial_send("%i:%i:1,20,%i="%(sid,did,show_num)) 
            show_num+=1
            time.sleep(1)
        for id in range(1,max_nodes_cnt):
            if not(id == dm.sid or (id in dm.uids) ):
                print("testing id=%i, max counts=%i" %(id,show_num))
                th.serial_send("%i:%i:1,20,%i="%(id,1,show_num)) 
                time.sleep(0.01)
                #th.serial_send("%i:%i:1,20,%i="%(sid,test_did,show_num))
                #time.sleep(0.01)
                
                show_num+=1
        self.do_dminfo("")
        #time.sleep(3)
        #for i in range(10):
        #    th.serial_send("%i:%i:1,20,%i="%(sid,test_did,show_num-1))
        #    time.sleep(1)
#Serial process thread
class MonitorThread(threading.Thread):
    def __init__(self, dm, wait=0.01):
        threading.Thread.__init__(self)
        self.event = threading.Event()
        self.wait = wait
        self.exit = False
        self.ser = Serial(ser_name, 115200, timeout=1) #FIXME, change device id to your system device
        self.dm = dm
    def set_ts(self, ts):
        self.wait = ts

    def do_function(self):
        line = self.ser.readline()
        if line:
            if len(line)>0:
                #msg = line.strip()
                msg = str(line,'UTF-8').strip()
                #print(msg)
                msg_line =msg+"\n" 
                #sys.stdout.write(msg_line)
                self.dm.proc_record(msg)

    
    def run(self):
        while 1:
            if self.exit:
                break
                # Wait for a connection
            self.do_function()
            self.event.wait(self.wait)

    def serial_send(self,send_str):
        sys.stdout.write("[%s]\n" % send_str)
        out_str = "%s\n" % send_str
        self.ser.write(out_str.encode())



def main():
    calibrate_by_offset(cal_cm,cal_rssi)
    global dm,cli,th
    dm = DM()
    cli = DmCli()
    th = MonitorThread(dm)
    th.start()
       
    while 1:
        #try:
        cli.cmdloop()
        if cli.user_quit:
            th.exit = True
            break
        #except:
        #    th.exit = True
        #    print("Exception!")
        #    break

if __name__ == "__main__":
    main()
    
    
