from neo4j import GraphDatabase

from app.core.config import settings


neo4j_driver = GraphDatabase.driver(
    settings.NEO4J_URI,
    auth=(
        settings.NEO4J_USERNAME,
        settings.NEO4J_PASSWORD
    )
)
