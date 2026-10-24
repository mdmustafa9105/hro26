from src.data import loader
from src.utils import identity
from src.evidence import parser
data = loader.load_all()
r = identity.IdentityResolver(data)
p = parser.EvidenceParser(data['evidence_files'])
m = r.resolve("amina.elmasri@gmail.com")
ur = m[0]
res = p.parse("evidence_54")
print(ur["email"].lower() in res["text"].lower())
print(res["resources"])
