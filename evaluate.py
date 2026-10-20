"""Reproducible source-hit and unanswerable-control check on authored examples."""
import csv,hashlib,secrets,tempfile
from pathlib import Path
import app

CASES=[
 ("How many days of annual leave are provided?","leave.txt","Leave"),
 ("How early should I request planned leave?","leave.txt","Leave"),
 ("Who approves remote work?","remote_work.txt","Workplace"),
 ("What should an approved remote arrangement document?","remote_work.txt","Workplace"),
 ("How do I report a lost work device?","remote_work.txt","Workplace"),
 ("How do I file a formal grievance?","grievance.txt","Conduct"),
 ("Can I bring a colleague to the grievance meeting?","grievance.txt","Conduct"),
 ("How long does HR have to acknowledge a grievance?","grievance.txt","Conduct"),
 ("What is the process to appeal a grievance outcome?","grievance.txt","Conduct"),
 ("What is the parental leave entitlement?","","Leave"),
]

def main():
    old=(app.ROOT,app.DB,app.FILES);tmp=tempfile.TemporaryDirectory();base=Path(tmp.name)
    try:
        app.ROOT=base;app.DB=base/"eval.sqlite3";app.FILES=base/"documents";app.FILES.mkdir();app.init_db()
        salt,digest=app.password_hash(secrets.token_urlsafe(24))
        with app.connect() as c:c.execute("INSERT INTO users(id,email,email_norm,password_hash,salt,created) VALUES(?,?,?,?,?,?)",("evaluation-user","eval@example.test","eval@example.test",digest,salt,0))
        for filename,category in (("remote_work.txt","Workplace"),("leave.txt","Leave"),("grievance.txt","Conduct")):
            path=old[0]/"data"/"sample_policies"/filename;app.index_document("evaluation-user",filename,path.read_bytes(),category,"2025","Synthetic example")
        rows=[]
        for q,expected,category in CASES:
            hits=app.retrieve("evaluation-user",q,category=category)
            names=sorted(set(x["document"]["name"] for x in hits))
            rows.append({"question":q,"expected_document":expected or "unanswerable","retrieved_documents":"|".join(names),"hit":bool(expected and expected in names),"top_k":5,"retriever":"lexical BM25-like"})
        answerable=[r for r in rows if r["expected_document"]!="unanswerable"]
        out=old[0]/"evaluation"/"results.csv";out.parent.mkdir(exist_ok=True)
        with out.open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
        n=sum(r["hit"] for r in answerable);unans=next(r for r in rows if r["expected_document"]=="unanswerable")
        print("Retrieval hit rate: %d/%d (%.1f%%); unanswerable control: %s"%(n,len(answerable),100*n/len(answerable),"rejected" if not unans['retrieved_documents'] else "false positive"))
        print("Results:",out)
    finally:app.ROOT,app.DB,app.FILES=old;tmp.cleanup()

if __name__=="__main__":main()
