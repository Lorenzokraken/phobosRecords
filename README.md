# Phobos Records

**Music Analytics Platform** — ETL + Reporting per label indipendenti

---

## 🎯 Why I Built This

Dopo un progetto enterprise su Databricks/AWS (100M+ records, Terraform, Delta Lake), volevo dimostrare che so anche fare lo **stack opposto**: leggero, deployabile, senza overengineering.

Non ogni problema richiede Spark. A volte basta Python + PostgreSQL + buone decisioni.

---

## 💡 Key Decisions

| Problema | Scelta | Perché |
|----------|--------|--------|
| Multi-artist royalty splits | Tabella `quotas` separata | Normalizzazione > JSON nested. Query pulite, no parsing runtime |
| Advance recoupment | Calcolo a query-time | Stato sempre fresh, no sync issues |
| Report cross-filtering | Aggregazioni SQL | Il DB fa il lavoro pesante, non Python |
| Architettura ETL | Moduli separati (extract/transform/load) | Testabilità, manutenibilità, pattern riconoscibile |
| Deployment | Railway + PostgreSQL managed | Zero ops, focus sul codice |

---

## 🛠️ Stack
```
Python · PostgreSQL · FastAPI · SQLAlchemy
Docker · Railway
```

---

## 📊 What It Does

- ETL pipeline: JSON/CSV → PostgreSQL → Report
- Royalty calculation con multi-artist splits
- Dashboard con cross-filtering (genere, artista, piattaforma, periodo)
- Advance tracking e recoupment

---

## 🚀 Run It
```bash
# Clone + setup
git clone https://github.com/Lorenzokraken/PhobosRecords.git
cd PhobosRecords
pip install -r requirements.txt

# Start DB (Docker)
docker-compose up -d

# Load data + run
python etl_in.py
python etl_out.py
```

---

## 🔗 Links

- **Live Demo**: [https://phobosrecords-production.up.railway.app/](link)
- **Enterprise Project**: SIAE Allocazione Analitica (PySpark, Delta Lake, AWS, Terraform)

---

<div align="center">
  <i>Built to show that good data engineering is about decisions, not just tools.</i>
</div>