# AI-Powered Lost & Found Management System

A full-stack intelligent platform for managing lost and found items using 
multimodal AI matching — combining image similarity, NLP text embeddings, 
and metadata re-ranking for accurate item retrieval.

## 🚀 Features

- 🖼️**Multimodal Item Matching** — image similarity + NLP text embeddings 
  + metadata re-ranking
- 🔎 **FAISS Vector Search** — scalable retrieval across large item databases
- 📱 **QR-Based Claim Verification** — secure item claiming system
- 🔐 **User Authentication** — secure registration and login
- 📊 **Analytics Dashboard** — recovery statistics and system monitoring
- 🔔 **Notification System** — alerts when matching items are found
- ✅ **Admin Verification** — approve and manage item listings
- 🗄️ **Optimised Database** — normalised relational DB with trigger-based 
  automation and indexed queries

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | PostgreSQL (Supabase) |
| AI/ML | TensorFlow, FAISS, OpenCV |
| NLP | Sentence Transformers, NLP embeddings |
| Frontend | HTML, CSS, JavaScript |
| Auth & QR | Flask-Login, qrcode library |

## 📁 Project Structure

DBMS_Project/
├── app.py                  # Main Flask application
├── templates/              # HTML templates
│   ├── home.html
│   ├── report.html
│   ├── matches.html
│   ├── admin_dashboard.html
│   ├── analytics.html
│   └── ...
├── static/                 # Static files
├── project_tables_dbms.sql # Database schema
├── requirements.txt        # Dependencies
└── DBMS_Lost_And_Found_ER_Diagram.jpeg  # ER Diagram

## ⚙️ Installation

1. Clone the repository:
```bash
git clone https://github.com/B-Sujata/DBMS_Project-AI-LostAndFound_ManagementSystem-.git
cd DBMS_Project-AI-LostAndFound_ManagementSystem-
```

2. Create and activate virtual environment:
```bash
python -m venv dbms_env
dbms_env\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Create a .env file with:
DB_PASSWORD=your_supabase_password
SECRET_KEY=your_secret_key
```

5. Run the application:
```bash
flask run
```

## 🧠 How AI Matching Works
User reports item
↓
Image → TensorFlow feature extraction
Text  → Sentence Transformer embeddings
↓
FAISS vector search across database
↓
Metadata re-ranking for accuracy
↓
Top matches returned + notification sent

## 📊 Database Design

- Normalised relational schema (3NF)
- Trigger-based automation for status updates
- Optimised indexing for high-throughput queries
- ER Diagram included in repository

## 💡 What I Learned
Built this during my 3rd year as part of DBMS coursework. 
The biggest challenge was when Supabase kept disconnecting and I had to debug the connection pooling for hours,
but this project taught me a lot.

## 👩‍💻 Author

**Sujata Bhadke** — B.Tech IT, VIIT Pune  
[LinkedIn](https://www.linkedin.com/in/sujata-bhadke-70a2342ba/) | 
[GitHub](https://github.com/B-Sujata)
