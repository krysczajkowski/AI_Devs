import requests
import json
import os 
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
from neo4j import GraphDatabase

apikey = os.getenv("API_KEY")
client = OpenAI(api_key = os.getenv("OPENAI_KEY"))

def ask_server(apikey, query):
    data = {
        "task": "database",
        "apikey": apikey,
        "query": query
    }
    data_json = json.dumps(data)
    r = requests.get("https://centrala.ag3nts.org/apidb", data=data_json)

    response_json = r.json()
    #return json.dumps(response_json['reply'])
    return response_json['reply']

def create_json_db(apikey):
    db = {}
    users_db = ask_server(apikey, "SELECT * FROM users")
    connections_db = ask_server(apikey, "SELECT * FROM connections")
    db['users'] = users_db
    db['connections'] = connections_db

    # Write the json structure into a file
    with open("db.json", 'w') as file:
        json.dump(db, file, indent=4)  

def create_graph_db(URI, AUTH):
    # Load JSON data
    with open("db.json", "r") as file:
        data = json.load(file)

    # Connect to Neo4j
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()

        # Create nodes for users
        for user in data["users"]:
            driver.execute_query(
                """
                MERGE (u:User {id: $id, username: $username, access_level: $access_level, is_active: $is_active, lastlog: $lastlog})
                """,
                id=user["id"],
                username=user["username"],
                access_level=user["access_level"],
                is_active=user["is_active"],
                lastlog=user["lastlog"],
                database_="neo4j"
            )
        print("User nodes created.")

        # Create relationships between users
        for relationship in data["connections"]:
            driver.execute_query(
                """
                MATCH (from:User {id: $user1_id})
                MATCH (to:User {id: $user2_id})
                MERGE (from)-[r1:KNOWS]->(to)
                MERGE (to)-[r2:KNOWS]->(from)
                """, 
                user1_id=relationship["user1_id"],
                user2_id=relationship["user2_id"],
                database_="neo4j"
            )
        print("Relationships created.")

        # Query to verify the graph
        records, _, _ = driver.execute_query(
            """
            MATCH (n)-[r]->(m)
            RETURN n.username AS from, type (r) AS relationship, m.username AS to
            """,
            database_="neo4j"
        )

        # Print the results
        print("Graph relationships:")
        for record in records:
            print(f"{record['from']} --({record['relationship']})--> {record['to']}")

def find_shortest_path(URI, AUTH, username1, username2):
    try:
        # Connect to Neo4j
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            driver.verify_connectivity()

            # Query to find the shortest path
            query = """
            MATCH (start:User {username: $username1}), (end:User {username: $username2})
            MATCH path = shortestPath((start)-[:KNOWS*]-(end))
            RETURN nodes(path) AS nodes, relationships(path) AS relationships
            """

            # Execute the query
            records, _, _ = driver.execute_query(
                query,
                username1=username1,
                username2=username2,
                database_="neo4j"
            )

            # Process and display the results
            if records:
                for record in records:
                    nodes = record["nodes"]
                    relationships = record["relationships"]
                    path = []
                    for i, node in enumerate(nodes):
                        path.append(node["username"])

                    return ", ".join(path)
            else:
                return None

    except Exception as e:
        print(f"An error occurred: {e}")

def send_answer(apikey, answer):
    server_msg = {
        "task": "connections",
        "apikey": apikey,
        "answer": answer
    }
    response = requests.post(
        url = "https://centrala.ag3nts.org/report",
        json = server_msg,
        headers = {
            "Content-type": "application/json"
        }
    )

    return response.json()

# Neo4j config
URI = "neo4j://localhost:7687/"
AUTH = ("neo4j", "neo4jneo4j")

answer = find_shortest_path(URI, AUTH, "Rafał", "Barbara")

print(send_answer(apikey, answer))


