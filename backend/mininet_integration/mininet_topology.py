import random

class MockMininet:
    def __init__(self, topo=None):
        self.topo = topo
        self.nodes = {}
        self.links = []
        self.is_running = False

    def addHost(self, name):
        self.nodes[name] = {"type": "host", "status": "up"}
        return name

    def addSwitch(self, name):
        self.nodes[name] = {"type": "switch", "status": "up"}
        return name

    def addLink(self, node1, node2, bw=10, delay='5ms', loss=0):
        link = {
            "id": f"{node1}-{node2}",
            "nodes": [node1, node2],
            "bw": bw,
            "delay": delay,
            "loss": loss,
            "status": "up"
        }
        self.links.append(link)
        return link

    def start(self):
        self.is_running = True
        print("Mininet Simulation Started")

    def stop(self):
        self.is_running = False
        print("Mininet Simulation Stopped")

def build_topology():
    net = MockMininet()
    
    # Core Switches
    c1 = net.addSwitch('c1')
    c2 = net.addSwitch('c2')
    
    # Edge Switches
    e1 = net.addSwitch('e1')
    e2 = net.addSwitch('e2')
    e3 = net.addSwitch('e3')
    e4 = net.addSwitch('e4')
    
    # Hosts
    h1 = net.addHost('h1')
    h2 = net.addHost('h2')
    h3 = net.addHost('h3')
    h4 = net.addHost('h4')
    
    # Links
    net.addLink(c1, c2, bw=100, delay='1ms')
    net.addLink(c1, e1, bw=10, delay='5ms')
    net.addLink(c1, e2, bw=10, delay='5ms')
    net.addLink(c2, e3, bw=10, delay='5ms')
    net.addLink(c2, e4, bw=10, delay='5ms')
    
    net.addLink(e1, h1, bw=100, delay='1ms')
    net.addLink(e2, h2, bw=100, delay='1ms')
    net.addLink(e3, h3, bw=100, delay='1ms')
    net.addLink(e4, h4, bw=100, delay='1ms')
    
    return net

# Global instance for the simulation
net_instance = build_topology()
