# Knowledge Graph Setup with Neo4j
This guide outlines the steps to set up a knowledge graph using Neo4j, including installing Neo4j, configuring the database, and loading data.
---
## Prerequisites
- [Python 3.9+](https://www.python.org/downloads/)
- [Neo4j Desktop or Server](https://neo4j.com/download/) (version 5.24.0)
- A compatible APOC plugin (linked below)
---
## Steps to Setup
### 1. Install Neo4j
#### Download Neo4j Desktop
- Go to [Neo4j Downloads](https://neo4j.com/download/) and download **Neo4j Desktop**.
- Install and start the application.
#### Set Up a Database
1. Open Neo4j Desktop and create a **New Project**.
2. Inside the project, create a new **local database**.
3. Start the database.
4. Note the **URI**, **username**, and **password**.
   - Default URI: `bolt://localhost:7687`
   - Default username: `neo4j`
   - Default password: `neo4j`
5. To reset the password, open a terminal at the Neo4j installation location. To do this, you can click the three dots next to your database and select the "Terminal" button. 
6. Run the following command: `neo4j-admin dbms set-initial-password <password>`
    - I have set the password as `neo4j`
#### Install APOC Plugin
1. Download the latest APOC plugin for your Neo4j version:
   - [APOC Plugin 5.24.0 Core](https://github.com/neo4j/apoc/releases/download/5.24.0/apoc-5.24.0-core.jar)
2. Place the downloaded `.jar` file into the `plugins` directory:
   - For Neo4j Desktop: `~/.Neo4jDesktop/relate-data/dbmss/<db-folder>/plugins`
   - If you are unable to find this, you can click the three dots next to your database and select the "Open Folder" button.
3. Restart the database.
#### Update Neo4j Configuration
1. Open the Neo4j configuration file (`neo4j.conf`).
2. Add the following lines:
```plaintext
# Enable APOC procedures
apoc.import.file.enabled=true
apoc.export.file.enabled=true
apoc.cypher.enabled=true
# Allow unrestricted procedures
dbms.security.procedures.unrestricted=apoc.*
```
3. Save the file and restart the Neo4j database using the desktop application.
---
### 2. Install Python Dependencies
Create a virtual environment and install the required libraries.
```bash
# Create and activate virtual environment
python3 -m venv env
source env/bin/activate
# Install Python dependencies
pip install neo4j langchain pyvis python-dotenv
```
---
### 3. Set Up Environment Variables
Create a `.env` file in the `knowledge_graph_agent` folder with the following content:
```plaintext
OPENAI_API_KEY=
OPENAI_MODEL=gpt-3.5-turbo-instruct
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_ACCEPT_LICENSE_AGREEMENT=yes
```
Replace `your_password` with the password for your Neo4j database.
---
### 4. Load Data into Neo4j
#### Script to Load Data
Run the following script to populate the Neo4j database:
```bash
python db_init.py
```
Make sure the parameters in the script are set correctly such as paths to knowledge base.
---
### 5. Run the Knowledge Graph Agent
Use the `langchain_graph_agent.py` script to ask questions about the graph:
```bash
python langchain_graph_agent.py
```
Example interaction:
```plaintext
Ask questions about your graph database!
Your Question (type 'exit' to quit): List all materials used in Batch B001
Response: Material A, Material B
```
---
### 6. Visualize the Knowledge Graph
#### Neo4j Browser
1. Open the Neo4j Browser at `http://localhost:7474`.
2. Log in using your credentials.
3. Run the following query to view the graph:
```cypher
MATCH (n)-[r]->(m)
RETURN n, r, m
```
#### PyVis Visualization
You can also visualize the graph programmatically using `PyVis`:
```python
from pyvis.network import Network
from neo4j import GraphDatabase
# Neo4j credentials
URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "your_password"
# Connect to Neo4j
driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
# Fetch data
def fetch_graph():
    query = "MATCH (n)-[r]->(m) RETURN n, r, m"
    with driver.session() as session:
        return session.run(query)
# Create visualization
net = Network(notebook=False, directed=True)
for record in fetch_graph():
    n1 = record["n"]
    n2 = record["m"]
    r = record["r"]
    net.add_node(str(n1.id), label=n1.labels[0])
    net.add_node(str(n2.id), label=n2.labels[0])
    net.add_edge(str(n1.id), str(n2.id), title=r.type)
net.show("graph.html")
```
Run the script to generate an HTML file (`graph.html`) for visualization.
---
### Troubleshooting
- If Neo4j doesn't start, ensure the `apoc-*.jar` file is placed in the correct `plugins` directory.
- Check logs in `neo4j.log` and `debug.log` for detailed error information.
- Ensure that the database is running before executing scripts.
---
### References
- [Neo4j Documentation](https://neo4j.com/docs/)
- [APOC Documentation](https://neo4j.com/labs/apoc/)
---