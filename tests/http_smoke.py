"""End-to-end smoke test against a running CLAUSE server (destructive only to temp data)."""
import http.cookiejar,json,os,secrets,urllib.error,urllib.request

BASE=os.getenv("CLAUSE_URL","http://127.0.0.1:8501")
def client():
 jar=http.cookiejar.CookieJar();return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
def request(opener,path,method="GET",payload=None):
 data=json.dumps(payload).encode() if payload is not None else None
 req=urllib.request.Request(BASE+path,data=data,method=method,headers={"Content-Type":"application/json"} if data else {})
 try:
  with opener.open(req,timeout=10) as r:return r.status,json.loads(r.read())
 except urllib.error.HTTPError as e:
  try:return e.code,json.loads(e.read())
  finally:e.close()
def upload(opener,name,raw,category,year):
 boundary="----clause"+secrets.token_hex(8);parts=[]
 def field(key,value):parts.append(("--"+boundary+"\r\nContent-Disposition: form-data; name=\""+key+"\"\r\n\r\n"+value+"\r\n").encode())
 field("category",category);field("year",year);parts.extend([("--"+boundary+"\r\nContent-Disposition: form-data; name=\"file\"; filename=\""+name+"\"\r\nContent-Type: text/plain\r\n\r\n").encode(),raw,b"\r\n--"+boundary.encode()+b"--\r\n"])
 req=urllib.request.Request(BASE+"/api/upload",data=b"".join(parts),headers={"Content-Type":"multipart/form-data; boundary="+boundary},method="POST")
 with opener.open(req,timeout=10) as r:return json.loads(r.read())
def main():
 suffix=secrets.token_hex(5);a=client();b=client();email="clause-admin-smoke@example.test";password="Test-policy-"+suffix+"-pass"
 assert request(a,"/api/register","POST",{"email":email,"password":password})[0]==200
 assert request(a,"/api/me")[1]['user']['role']=='admin'
 status,admin_status=request(a,"/api/admin/status");assert status==200 and 'embedded_chunks' in admin_status and 'chunks' in admin_status
 assert request(a,"/api/admin/evaluation")[0]==200
 assert request(a,"/api/admin/settings")[0]==200
 _,library=request(a,"/api/library");assert len(library['documents'])==3
 raw=b"Synthetic benefit policy: employees receive three wellness rest days per year after manager approval is recorded."
 added=upload(a,"wellness-benefit.txt",raw,"Benefits","2024");assert added['status']=="indexed"
 _,filtered=request(a,"/api/ask","POST",{"question":"How many wellness rest days?","category":"Benefits","year":"2024"});assert filtered['sources'] and filtered['sources'][0]['document']['name']=="wellness-benefit.txt"
 import fitz
 pdf=fitz.open();page=pdf.new_page();page.insert_text((72,72),"Synthetic PDF policy: employees report safety hazards to the safety officer immediately.");pdf_raw=pdf.tobytes();pdf.close()
 added_pdf=upload(a,"safety-smoke.pdf",pdf_raw,"Safety","2026");assert added_pdf['status']=="indexed", added_pdf
 _,pdf_answer=request(a,"/api/ask","POST",{"question":"Where do employees report safety hazards?","conversation_id":filtered['conversation_id'],"category":"Safety","year":"2026"});assert pdf_answer['sources'][0]['page']==1
 status,ask=request(a,"/api/ask","POST",{"question":"How many days of annual leave are provided?","conversation_id":filtered['conversation_id'],"category":"Leave","year":"All"})
 assert status==200 and ask['sources'] and ask['sources'][0]['document']['name']=="leave.txt"
 cid=ask['conversation_id'];status,conv=request(a,"/api/conversation/"+cid);assert status==200 and len(conv['messages'])==6 and [m['role'] for m in conv['messages']]==['user','assistant']*3
 docid=library['documents'][0]['id'];status,_=request(b,"/api/register","POST",{"email":"employee-"+suffix+"@example.test","password":password});assert status==200
 assert request(b,"/api/me")[1]['user']['role']=='employee'
 assert request(b,"/api/admin/status")[0]==403
 assert request(b,"/api/admin/evaluation")[0]==403
 assert request(b,"/api/admin/settings")[0]==403
 assert request(b,"/api/admin/settings","PUT",{"top_k":9})[0]==403
 assert request(b,"/api/upload","POST",{})[0]==403
 assert request(b,"/api/document/"+docid)[0]==404
 assert request(b,"/api/conversation/"+cid)[0]==404
 assert request(a,"/api/logout","POST",{})[0]==200
 assert request(a,"/api/login","POST",{"email":email,"password":password})[0]==200
 assert len(request(a,"/api/library")[1]['documents'])==5
 assert len(request(a,"/api/conversations")[1]['conversations'])==1
 print("PASS: role-scoped admin diagnostics/uploads, register, seeded library, retrieval citations, persistent conversation, logout/login persistence, and cross-account isolation.")
if __name__=="__main__":main()
