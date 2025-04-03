# Financial Agent

To run the docker image for PGVector, run the following command:

```
docker run \
  -e POSTGRES_DB=ai \
  -e POSTGRES_USER=ai \
  -e POSTGRES_PASSWORD=ai \
  -e PGDATA=/var/lib/postgresql/data/pgdata \
  -v pgvolume:/var/lib/postgresql/data \
  -p 5532:5432 \
  pgvector/pgvector:pg16
```

[Docs](https://docs.agno.com/agents/run)

## To-do
- Update RAG to be an [Agentic RAG](https://docs.agno.com/agents/knowledge#step-3%3A-agentic-rag)
- Create visual interface to allow users to interact with the agent,
- Make it read files that are inputed 
