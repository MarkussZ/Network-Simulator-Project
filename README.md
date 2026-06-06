# Python Network Simulator

A Python-based educational network simulator designed to help users learn and experiment with networking concepts without requiring physical hardware or enterprise simulation tools.

The simulator allows users to create network topologies, configure devices, assign IP addresses, establish connections, test communication, configure VLANs, EtherChannels, and Layer 3 switching, while visualising the network through an interactive topology viewer.

The project combines networking principles with software engineering concepts, database integration, REST APIs, and graph visualisation to provide a simplified alternative to traditional network simulation platforms.

* Features

## Network Device Creation

- Dynamic device creation using Factory Design Pattern
- Support for multiple networking devices
- Model-specific hardware configurations
- Device state management
- Port management and tracking

Supported devices include:

- Routers
- Layer 2 Switches
- Layer 3 Switches
- Firewalls
- Servers
- PCs

## Network Configuration

- IPv4 address assignment
- Subnet mask validation
- Gateway configuration
- Interface configuration
- Device state management
- Connection management

## VLAN Support

- VLAN creation and management
- VLAN assignment to switch ports
- VLAN membership tracking
- Layer 2 network segmentation

## EtherChannel Support

- EtherChannel configuration
- Link aggregation simulation
- Multiple connection management
- Enterprise networking concepts

## HSRP Support

- Hot Standby Router Protocol simulation
- Virtual gateway configuration
- Active and standby election
- Redundancy concepts

## Connectivity Testing

- Ping simulation
- Route discovery
- Network path visualization
- Reachability testing
- ICMP-style communication checks

## Network Visualization

- Network topology generation using NetworkX
- Device hierarchy representation
- Interactive graph visualisation
- Layered network architecture display
- Matplotlib integration

## Database Integration

- MySQL database support
- Device persistence
- Configuration storage
- Connection tracking
- VLAN and EtherChannel storage
- HSRP configuration storage

## REST API

- FastAPI integration
- Network configuration endpoints
- Device management APIs
- IP assignment APIs
- CRUD functionality

* Technologies Used

## Programming Languages

- Python
- SQL

## Networking Concepts

- IPv4 Addressing
- VLANs
- EtherChannel
- HSRP
- Routing
- Switching
- ICMP Ping Simulation

## Backend Development

- FastAPI
- REST APIs

## Database

- MySQL
- MySQL Connector

## Data Visualisation

- NetworkX
- Matplotlib

## Additional Libraries

- Tabulate
- Collections (Deque)

* Networking Features

## IP Address Management

- IPv4 address validation
- Static IP assignment
- Gateway assignment
- Address format verification

## Subnet Validation

- Subnet mask verification
- Binary subnet checking
- Invalid subnet detection

## Routing & Connectivity

- Route discovery
- Reachability analysis
- Network path generation
- Device communication testing

## Redundancy

- HSRP simulation
- Virtual IP assignment
- Active/Standby election logic

* Design Patterns & Software Engineering Concepts

This project demonstrates:

- Factory Design Pattern
- Object-Oriented Programming
- Encapsulation
- Inheritance
- Polymorphism
- Data Persistence
- Graph Theory Concepts
- REST API Design
- Database Integration

* Database Tables

The simulator stores:

- Devices
- Ports
- Connections
- VLANs
- EtherChannels
- HSRP Configurations

This allows users to save and retrieve network configurations between sessions.

* Example Features

- Create routers and switches
- Configure interfaces
- Assign IP addresses
- Create VLANs
- Configure EtherChannels
- Configure HSRP groups
- Test connectivity with ping
- Visualise network topologies
- Save configurations to MySQL
- Manage devices through FastAPI

* Project Objectives

The project aimed to:

- Simplify networking education
- Provide a lightweight network simulator
- Demonstrate networking concepts through software
- Reduce dependence on physical hardware
- Improve accessibility for beginner networking students
- Integrate networking, databases, and APIs into a single platform

* Future Improvements

Potential future improvements include:

- Full ACL implementation
- Complete HSRP functionality
- NAT support
- DNS simulation
- IPv6 support
- HTTP and HTTPS traffic simulation
- Email protocol simulation (SMTP, IMAP, POP3)
- Web-based GUI
- Remote access functionality
- Drag-and-drop topology designer
- Cloud deployment
- Downloadable desktop application

* Educational Purpose

This project was developed to demonstrate:

- Computer networking concepts
- Network simulation
- Software engineering principles
- Database integration
- REST API development
- Graph visualisation
- Python application development

* Author

**Markuss Zakss**  
TUS Midlands – Final Year Network Simulator Project
