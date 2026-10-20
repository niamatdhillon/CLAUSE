import hashlib,json,secrets,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import app

class WorkspaceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.old=(app.ROOT,app.DATA,app.FILES,app.DB);base=Path(self.tmp.name)
  app.ROOT=base;app.DATA=base/"data";app.DATA.mkdir();app.FILES=app.DATA/"documents";app.FILES.mkdir();app.DB=app.DATA/"test.sqlite3";app.init_db();self.a=self.user("a@example.test");self.b=self.user("b@example.test")
 def tearDown(self):app.ROOT,app.DATA,app.FILES,app.DB=self.old;self.tmp.cleanup()
 def user(self,email):
  uid=secrets.token_hex(12);salt,digest=app.password_hash("demonstration password")
  with app.connect() as c:c.execute("INSERT INTO users(id,email,email_norm,password_hash,salt,created) VALUES(?,?,?,?,?,?)",(uid,email,email,digest,salt,0));c.execute("INSERT INTO preferences VALUES(?,5)",(uid,))
  return uid
 def add(self,user,name,text,category="Leave",year="2025"):
  return app.index_document(user,name,text.encode(),category,year)
 def test_ingestion_dedup_retrieval_and_metadata_filter(self):
  self.add(self.a,"leave.txt","Full-time employees receive 20 paid annual leave days. Planned leave requests should arrive ten working days in advance.")
  duplicate=self.add(self.a,"different-name.txt","Full-time employees receive 20 paid annual leave days. Planned leave requests should arrive ten working days in advance.")
  self.assertEqual(duplicate['status'],'duplicate')
  hits=app.retrieve(self.a,"How many annual leave days?",category="Leave",year="2025")
  self.assertTrue(hits);self.assertIn("20 paid annual leave days",hits[0]['text']);self.assertEqual(hits[0]['document']['name'],"leave.txt")
  self.assertEqual(app.retrieve(self.a,"How many annual leave days?",category="Conduct"),[])
 def test_users_cannot_retrieve_each_others_documents(self):
  self.add(self.a,"private.txt","This private workplace passage concerns a confidential equipment allowance policy.","Workplace")
  self.assertTrue(app.retrieve(self.a,"equipment allowance",category="Workplace"))
  self.assertEqual(app.retrieve(self.b,"equipment allowance",category="Workplace"),[])
 def test_unknown_policy_is_not_synthesized(self):
  self.add(self.a,"leave.txt","Annual leave is 20 days under this synthetic example. Requests need manager approval.")
  self.assertEqual(app.retrieve(self.a,"What is the parental leave entitlement?",category="Leave"),[])
  text,mode=app.generate_answer("What is parental leave?",[])
  self.assertEqual(mode,"unanswerable");self.assertIn("couldn't find sufficient evidence",text)
 def test_model_prompt_is_grounded_and_citations_are_validated(self):
  e=[{"chunk_id":"doc-0","text":"Employees receive 20 days of annual leave.","page":2,"document":{"title":"Leave","name":"leave.pdf"}}]
  class Response:
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def read(self):return json.dumps({"message":{"content":"The policy gives 20 days [1]. Another claim [9]."}}).encode()
  with patch.object(app,"ollama_state",return_value={"installed":True,"chat_model":"qwen2.5:3b","model":"qwen2.5:3b","host":"http://127.0.0.1:11434"}),patch.object(app.urllib.request,"urlopen",return_value=Response()) as call:
   answer,mode=app.generate_answer("How many leave days?",e)
  sent=json.loads(call.call_args.args[0].data)
  self.assertEqual(mode,"llm");self.assertIn("20 days [1]",answer);self.assertNotIn("[9]",answer)
  self.assertIn("untrusted_policy_excerpt",sent['messages'][-1]['content'])
  self.assertIn("exclusively from the supplied policy evidence",sent['messages'][0]['content'])
 def test_local_semantic_vectors_are_saved_and_used_for_retrieval(self):
  state={"installed":True,"cached":True,"model":"test-local-encoder"}
  with patch.object(app,"embedding_state",return_value=state),patch.object(app,"embed_texts",side_effect=[[[1.0,0.0]],[[1.0,0.0]]]):
   result=self.add(self.a,"leave-semantics.txt","Employees may request an annual leave allowance through their line manager.","Leave","2024")
   self.assertEqual(result['status'],'indexed')
   hits=app.retrieve(self.a,"vacation entitlement",category="Leave",year="2024")
   self.assertEqual(hits[0]['document']['name'],"leave-semantics.txt")
   self.assertAlmostEqual(hits[0]['score'],0.75)
   self.assertEqual(app.retrieve(self.a,"vacation entitlement",category="Conduct",year="2024"),[])
 def test_missing_local_runtime_does_not_fake_synthesis(self):
  evidence=[{"chunk_id":"doc-0","text":"Employees receive 20 annual leave days.","page":None,"document":{"title":"Leave","name":"leave.txt"}}]
  with patch.object(app,"ollama_state",return_value={"installed":False,"chat_model":None,"model":"qwen2.5:3b","host":"http://127.0.0.1:11434"}):
   answer,mode=app.generate_answer("How many days?",evidence)
  self.assertEqual(mode,"retrieval-only")
  self.assertIn("synthesis is unavailable",answer)
 def test_failed_ingestion_is_retained_for_retry(self):
  result=self.add(self.a,"empty-policy.txt","too short")
  self.assertEqual(result['status'],'failed')
  with app.connect() as c:
   row=c.execute("SELECT status,path FROM documents WHERE id=? AND owner_id=?",(result['id'],self.a)).fetchone()
  self.assertEqual(row['status'],'failed');self.assertTrue((app.ROOT/row['path']).exists())
  self.assertEqual(app.reindex_document(self.a,result['id'])['status'],'failed')
 def test_pdf_page_metadata_is_preserved(self):
  import fitz
  pdf=fitz.open();page=pdf.new_page();page.insert_text((72,72),"Synthetic PDF policy: report safety hazards to the safety officer immediately.");raw=pdf.tobytes();pdf.close()
  result=app.index_document(self.a,"safety.pdf",raw,"Safety","2026")
  hits=app.retrieve(self.a,"Where should employees report safety hazards?",category="Safety",year="2026")
  self.assertEqual(result['status'],'indexed');self.assertTrue(hits);self.assertEqual(hits[0]['page'],1)
 def test_persistent_conversation_and_owner_scope(self):
  cid=app.create_conversation(self.a,"Annual leave")
  with app.connect() as c:c.execute("INSERT INTO messages VALUES(?,?,?,?,?,?,?,?)",(secrets.token_hex(12),cid,self.a,"user","How many leave days?",None,"[]",123))
  with app.connect() as c:
   found=c.execute("SELECT title FROM conversations WHERE id=? AND owner_id=?",(cid,self.a)).fetchone()
   leaked=c.execute("SELECT id FROM conversations WHERE id=? AND owner_id=?",(cid,self.b)).fetchone()
  self.assertEqual(found['title'],"Annual leave");self.assertIsNone(leaked)
 def test_sessions_store_only_hash_and_survive_database_reopen(self):
  token=secrets.token_urlsafe(32);digest=hashlib.sha256(token.encode()).hexdigest()
  with app.connect() as c:c.execute("INSERT INTO sessions VALUES(?,?,?,?)",(digest,self.a,9999999999,1))
  self.assertEqual(app.user_for_token(token)['id'],self.a);self.assertIsNone(app.user_for_token(digest))
 def test_removal_cascades_only_for_owner(self):
  d=self.add(self.a,"leave.txt","This synthetic policy explains annual leave and request approval steps.")
  self.assertFalse(app.remove_document(self.b,d['id']));self.assertTrue(app.remove_document(self.a,d['id']))
  self.assertFalse(app.retrieve(self.a,"annual leave"))

if __name__=="__main__":unittest.main()
