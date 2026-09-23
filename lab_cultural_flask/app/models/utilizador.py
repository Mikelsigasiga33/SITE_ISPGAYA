from app import get_db
from app.utils.security import sanitize


class Utilizador:

    @staticmethod
    def get_by_username(username: str):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT id, nome, username, password, email, role, clube_id, ativo, mfa_secret, mfa_ativo "
                "FROM utilizadores WHERE username = ? AND ativo = 1",
                (username,)
            )
            return cursor.fetchone()

    @staticmethod
    def get_by_id(user_id: int):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT id, nome, username, email, role, clube_id, ativo, mfa_secret, mfa_ativo "
                "FROM utilizadores WHERE id = ?",
                (user_id,)
            )
            return cursor.fetchone()

    @staticmethod
    def get_all():
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT u.id, u.nome, u.username, u.email, u.role, u.clube_id, u.ativo, "
                "c.nome AS clube_nome "
                "FROM utilizadores u "
                "LEFT JOIN clubes c ON u.clube_id = c.id "
                "ORDER BY u.nome"
            )
            return cursor.fetchall()

    @staticmethod
    def verificar_password(password: str, hashed: str | bytes) -> bool:
        import bcrypt
        from config import Config
        if isinstance(hashed, str):
            hashed = hashed.encode('utf-8')
            
        # 1. Tentar com Pepper (novo padrão)
        password_pepper = password + Config.PEPPER
        try:
            if bcrypt.checkpw(password_pepper.encode('utf-8'), hashed):
                return True
        except Exception:
            pass
            
        # 2. Fallback para Sem Pepper (compatibilidade com registos antigos)
        try:
            if bcrypt.checkpw(password.encode('utf-8'), hashed):
                return True
        except Exception:
            pass
            
        return False

    @staticmethod
    def criar(dados: dict) -> bool:
        import bcrypt
        from config import Config
        db = get_db()
        salt = bcrypt.gensalt(rounds=12)
        password_pepper = dados.get('password', '') + Config.PEPPER
        hashed = bcrypt.hashpw(password_pepper.encode('utf-8'), salt)
        role = dados.get('role', 'conteudo')
        clube_id = dados.get('clube_id') or None
        if clube_id:
            clube_id = int(clube_id)
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO utilizadores (nome, username, email, password, role, clube_id) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        sanitize(dados.get('nome', '')),
                        sanitize(dados.get('username', '')),
                        sanitize(dados.get('email', '')),
                        hashed.decode('utf-8'),
                        role,
                        clube_id
                    )
                )
                user_id = cursor.lastrowid
                # Registar no histórico
                cursor.execute(
                    "INSERT INTO historico_passwords (utilizador_id, password_hash) VALUES (?, ?)",
                    (user_id, hashed.decode('utf-8'))
                )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao criar utilizador: {e}")
            return False

    @staticmethod
    def editar(user_id: int, dados: dict) -> bool:
        db = get_db()
        role = dados.get('role', 'conteudo')
        clube_id = dados.get('clube_id') or None
        if clube_id:
            clube_id = int(clube_id)
        try:
            with db.cursor() as cursor:
                # Se forneceu nova password, atualizar
                password = dados.get('password', '').strip()
                if password:
                    import bcrypt
                    from config import Config
                    salt = bcrypt.gensalt(rounds=12)
                    password_pepper = password + Config.PEPPER
                    hashed = bcrypt.hashpw(password_pepper.encode('utf-8'), salt)
                    cursor.execute(
                        "UPDATE utilizadores SET nome=?, username=?, email=?, "
                        "password=?, role=?, clube_id=? WHERE id=?",
                        (
                            sanitize(dados.get('nome', '')),
                            sanitize(dados.get('username', '')),
                            sanitize(dados.get('email', '')),
                            hashed.decode('utf-8'),
                            role,
                            clube_id,
                            user_id
                        )
                    )
                    # Registar no histórico
                    cursor.execute(
                        "INSERT INTO historico_passwords (utilizador_id, password_hash) VALUES (?, ?)",
                        (user_id, hashed.decode('utf-8'))
                    )
                    # Manter apenas as últimas 3 passwords
                    cursor.execute(
                        "DELETE FROM historico_passwords WHERE utilizador_id = ? "
                        "AND id NOT IN (SELECT id FROM historico_passwords WHERE utilizador_id = ? ORDER BY criado_em DESC LIMIT 3)",
                        (user_id, user_id)
                    )
                else:
                    cursor.execute(
                        "UPDATE utilizadores SET nome=?, username=?, email=?, "
                        "role=?, clube_id=? WHERE id=?",
                        (
                            sanitize(dados.get('nome', '')),
                            sanitize(dados.get('username', '')),
                            sanitize(dados.get('email', '')),
                            role,
                            clube_id,
                            user_id
                        )
                    )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao editar utilizador: {e}")
            return False

    @staticmethod
    def eliminar(user_id: int) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute("UPDATE utilizadores SET ativo = 0 WHERE id = ?", (user_id,))
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False

    # Mantido para compatibilidade
    @staticmethod
    def criar_admin(nome: str, username: str, password: str) -> bool:
        return Utilizador.criar({
            'nome': nome,
            'username': username,
            'email': f'{username}@ispgaya.pt',
            'password': password,
            'role': 'admin'
        })

    @staticmethod
    def ativar_mfa(user_id: int, secret: str) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    "UPDATE utilizadores SET mfa_secret = ?, mfa_ativo = 1 WHERE id = ?",
                    (secret, user_id)
                )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao ativar MFA: {e}")
            return False

    @staticmethod
    def desativar_mfa(user_id: int) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    "UPDATE utilizadores SET mfa_secret = NULL, mfa_ativo = 0 WHERE id = ?",
                    (user_id,)
                )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao desativar MFA: {e}")
            return False

    @staticmethod
    def obter_historico_passwords(user_id: int) -> list:
        """Obtém a lista de hashes de passwords do histórico para o utilizador."""
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT password_hash FROM historico_passwords "
                    "WHERE utilizador_id = ? ORDER BY criado_em DESC LIMIT 3",
                    (user_id,)
                )
                return [row['password_hash'] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Erro ao obter histórico de passwords: {e}")
            return []
