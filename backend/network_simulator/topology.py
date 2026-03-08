import random

class NetworkSimulator:
    def __init__(self, topo=None):
        self.topo = topo
        self.nodes = {}
        self.links = []
        self.is_running = False

    def addHost(self, name):
        self.nodes[name] = {"type": "host", "status": "up", "display_name": name}
        return name

    def addSwitch(self, name, display_name=None):
        self.nodes[name] = {"type": "switch", "status": "up", "display_name": display_name or name}
        return name

    def addLink(self, node1, node2, bw=10, delay='5ms', loss=0):
        link = {
            "id": f"{node1}-{node2}",
            "node1": node1,
            "node2": node2,
            "bw": bw,
            "delay": delay,
            "loss": loss,
            "status": "up"
        }
        self.links.append(link)
        return link

    def start(self):
        self.is_running = True
        print("Network Simulation Started")

    def stop(self):
        self.is_running = False
        print("Network Simulation Stopped")

def build_topology():
    net = NetworkSimulator()
    
    # Core Routers - using city names
    c1 = net.addSwitch('Mumbai-Core-01', 'Mumbai Core Router')
    c2 = net.addSwitch('Bangalore-Core-02', 'Bangalore Core Router')
    
    # Edge Routers - using city names
    e1 = net.addSwitch('Delhi-Edge-05', 'Delhi Edge Router')
    e2 = net.addSwitch('NYC-Peering-01', 'NYC Peering Router')
    e3 = net.addSwitch('Chennai-Link-03', 'Chennai Link Router')
    e4 = net.addSwitch('London-Core-01', 'London Core Router')
    e5 = net.addSwitch('Frankfurt-Core-02', 'Frankfurt Core Router')
    
    # Hosts
    h1 = net.addHost('Host-Mumbai-01')
    h2 = net.addHost('Host-Delhi-01')
    h3 = net.addHost('Host-Bangalore-01')
    h4 = net.addHost('Host-NYC-01')
    
    # Links between core and edge routers
    net.addLink(c1, c2, bw=100, delay='1ms')      # Mumbai to Bangalore
    net.addLink(c1, e1, bw=10, delay='5ms')        # Mumbai to Delhi
    net.addLink(c1, h1, bw=100, delay='1ms')      # Mumbai to Host
    net.addLink(c2, e3, bw=10, delay='5ms')       # Bangalore to Chennai
    net.addLink(c2, h3, bw=100, delay='1ms')      # Bangalore to Host
    net.addLink(e1, h2, bw=100, delay='1ms')      # Delhi to Host
    net.addLink(e2, e4, bw=50, delay='10ms')      # NYC to London (transatlantic)
    net.addLink(e4, e5, bw=50, delay='5ms')       # London to Frankfurt
    net.addLink(e2, h4, bw=100, delay='1ms')      # NYC to Host
    
    return net

# Global instance for the simulation
net_instance = build_topology()

