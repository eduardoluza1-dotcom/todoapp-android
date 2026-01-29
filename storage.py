import json
import os
import hashlib
import secrets
from datetime import datetime


def pbkdf2_hash(password: str, salt_hex: str | None = None) -> dict:
    if salt_hex is None:
        salt = secrets.token_bytes(16)
        salt_hex = salt.hex()
    else:
        salt = bytes.fromhex(salt_hex)

    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return {"salt": salt_hex, "hash": dk.hex()}


def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    test = pbkdf2_hash(password, salt_hex=salt_hex)
    return secrets.compare_digest(test["hash"], hash_hex)


def valid_dt(data: str, hora: str) -> bool:
    try:
        datetime.strptime(f"{data} {hora}", "%d/%m/%Y %H:%M")
        return True
    except Exception:
        return False


class Storage:
    def __init__(self, data_dir: str):
        os.makedirs(data_dir, exist_ok=True)
        self.users_path = os.path.join(data_dir, "users.json")
        self.tasks_path = os.path.join(data_dir, "tasks.json")

        self.users = self._load(self.users_path, {})
        self.tasks = self._load(self.tasks_path, {})

        if not isinstance(self.users, dict):
            self.users = {}
        if not isinstance(self.tasks, dict):
            self.tasks = {}

        self._save_all()

    def _load(self, path: str, default):
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return default

    def _save(self, path: str, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _save_all(self):
        self._save(self.users_path, self.users)
        self._save(self.tasks_path, self.tasks)

    # ---------- USERS ----------
    def register(self, username: str, password: str):
        username = (username or "").strip()
        if not username or not password:
            return False, "Preencha usuário e senha."
        if " " in username:
            return False, "Usuário não pode ter espaços."
        if username in self.users:
            return False, "Usuário já existe."
        if len(password) < 4:
            return False, "Senha muito curta (mín. 4)."

        self.users[username] = pbkdf2_hash(password)
        self.tasks.setdefault(username, [])
        self._save_all()
        return True, "Usuário criado com sucesso."

    def login(self, username: str, password: str):
        username = (username or "").strip()
        if username not in self.users:
            return False, "Usuário ou senha inválidos."
        u = self.users[username]
        if not verify_password(password or "", u["salt"], u["hash"]):
            return False, "Usuário ou senha inválidos."

        self.tasks.setdefault(username, [])
        self._save_all()
        return True, "OK"

    # ---------- TASKS ----------
    def list_tasks(self, username: str):
        items = self.tasks.get(username, [])
        # ordena por pendente primeiro e por data/hora
        def key_fn(t):
            try:
                dt = datetime.strptime(f"{t.get('data','')} {t.get('hora','')}", "%d/%m/%Y %H:%M")
            except Exception:
                dt = datetime.max
            return (1 if bool(t.get("done")) else 0, dt)
        return sorted(list(items), key=key_fn)

    def _next_task_id(self, username: str) -> int:
        tasks = self.tasks.get(username, [])
        return max((int(t.get("id", 0)) for t in tasks), default=0) + 1

    def add_task(self, username: str, texto: str, data: str, hora: str):
        texto = (texto or "").strip()
        data = (data or "").strip()
        hora = (hora or "").strip()

        if not texto or not data or not hora:
            return False, "Preencha descrição, data e hora."
        if not valid_dt(data, hora):
            return False, "Data/hora inválidas. Use DD/MM/AAAA e HH:MM."

        task_id = self._next_task_id(username)
        self.tasks.setdefault(username, []).append({
            "id": task_id,
            "texto": texto,
            "data": data,
            "hora": hora,
            "done": False,
        })
        self._save(self.tasks_path, self.tasks)
        return True, "Tarefa adicionada."

    def toggle_done(self, username: str, task_id: int, done: bool):
        for t in self.tasks.get(username, []):
            if int(t.get("id")) == int(task_id):
                t["done"] = bool(done)
                self._save(self.tasks_path, self.tasks)
                return

    def delete_task(self, username: str, task_id: int):
        items = self.tasks.get(username, [])
        self.tasks[username] = [t for t in items if int(t.get("id")) != int(task_id)]
        self._save(self.tasks_path, self.tasks)

    def clear_all(self, username: str):
        self.tasks[username] = []
        self._save(self.tasks_path, self.tasks)
