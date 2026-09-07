from flask_app.utils.database import database

db = database()
roles = db.getLLMRoles()

print(f"llm_roles table contains {len(roles)} rows:\n")
for role_name, row in roles.items():
    print(f"- {role_name}")
