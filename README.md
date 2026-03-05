# API_Simulation_LPValid

## Running the Service (Docker)

## Start the system

Build and start the API + PostgreSQL containers:

```bash
docker compose up --build
```

---

## Stop the system

```bash
docker compose down
```

---

## Reset the database (delete all data)

```bash
docker compose down -v
docker compose up --build
```

---

## View running containers

```bash
docker ps
```

---

## View logs

API logs:

```bash
docker compose logs api
```

Database logs:

```bash
docker compose logs db
```

---

## Access the API

Open in browser:

```url
http://localhost:8001/docs
```
